"""Loopback-only web interface for reviewing notebook classifications."""

from __future__ import annotations

import hmac
import secrets
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Annotated, Any
from urllib.parse import quote, urlsplit

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from notebook_classifier.drafts import DraftError
from notebook_classifier.manifest import ManifestConflictError, ManifestError
from notebook_classifier.preview import build_preview
from notebook_classifier.review import (
    CONSTRAINTS,
    EDITABLE_PROPERTIES,
    REQUIRED_DECISIONS,
    VOCABULARIES,
    ReviewState,
)
from notebook_classifier.suggestions import suggestion_map

COOKIE_NAME = "notebook_classifier_session"
MAX_FORM_BYTES = 128 * 1024
_PACKAGE = Path(__file__).parent
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def create_app(
    repository_path: Path,
    manifest_path: Path = Path("validation/manifest.toml"),
    *,
    draft_root: Path | None = None,
    session_token: str | None = None,
    csrf_token: str | None = None,
) -> FastAPI:
    """Create one local review application and its isolated session state."""

    review = ReviewState(
        repository_path, manifest_path=manifest_path, draft_root=draft_root
    )
    app = FastAPI(
        title="Notebook classifier",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["127.0.0.1", "localhost", "[::1]"],
    )
    app.mount(
        "/static",
        StaticFiles(directory=_PACKAGE / "static"),
        name="static",
    )
    templates = Jinja2Templates(directory=_PACKAGE / "templates")
    app.state.review = review
    app.state.session_token = session_token or secrets.token_urlsafe(32)
    app.state.csrf_token = csrf_token or secrets.token_urlsafe(32)

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Any:
        length = request.headers.get("content-length")
        if request.method == "POST" and length is not None:
            try:
                too_large = int(length) > MAX_FORM_BYTES
            except ValueError:
                too_large = True
            if too_large:
                return HTMLResponse("Request body is too large.", status_code=413)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'none'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'self'"
        )
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        return response

    def authenticated(request: Request) -> None:
        actual = request.cookies.get(COOKIE_NAME, "")
        if not hmac.compare_digest(actual, app.state.session_token):
            raise HTTPException(status_code=403, detail="local review session required")

    def write_authorized(request: Request, token: str) -> None:
        authenticated(request)
        if not hmac.compare_digest(token, app.state.csrf_token):
            raise HTTPException(status_code=403, detail="invalid form token")
        if not _acceptable_write_origin(request):
            raise HTTPException(status_code=403, detail="cross-origin write rejected")

    def context(request: Request, **values: Any) -> dict[str, Any]:
        return {
            "request": request,
            "review": review,
            "csrf_token": app.state.csrf_token,
            "progress": review.progress(),
            "vocabularies": VOCABULARIES,
            "constraints": CONSTRAINTS,
            "required_decisions": REQUIRED_DECISIONS,
            **values,
        }

    @app.exception_handler(ManifestConflictError)
    async def conflict_page(request: Request, error: ManifestConflictError) -> Any:
        return templates.TemplateResponse(
            request,
            "error.html",
            context(request, title="Repository changed", message=str(error)),
            status_code=409,
        )

    @app.exception_handler(ManifestError)
    @app.exception_handler(DraftError)
    @app.exception_handler(ValueError)
    async def invalid_page(request: Request, error: Exception) -> Any:
        return templates.TemplateResponse(
            request,
            "error.html",
            context(request, title="Cannot apply change", message=str(error)),
            status_code=400,
        )

    @app.get("/session", response_class=HTMLResponse)
    def establish_session(token: str = "") -> RedirectResponse:
        if not hmac.compare_digest(token, app.state.session_token):
            raise HTTPException(status_code=403, detail="invalid local session token")
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            COOKIE_NAME,
            app.state.session_token,
            httponly=True,
            samesite="strict",
            secure=False,
        )
        return response

    @app.get("/", response_class=HTMLResponse)
    def dashboard(
        request: Request,
        q: str = "",
        state: str = "",
        completeness: str = "",
        role: str = "",
        scope: str = "",
        sort: str = "path",
        direction: str = "asc",
        _: None = Depends(authenticated),
    ) -> Any:
        inventory = {item.path: item for item in review.inventory.notebooks}
        rows = []
        for resolved in review.resolution.notebooks:
            facts = inventory.get(resolved.path)
            if facts is None:
                continue
            missing_required = review.missing_required_decisions(resolved)
            row = {
                "resolved": resolved,
                "facts": facts,
                "missing_required": missing_required,
                "decisions_complete": not missing_required,
                "detail_url": f"/notebook?path={quote(resolved.path, safe='')}",
            }
            if q and q.casefold() not in resolved.path.casefold():
                continue
            if state and resolved.review_state != state:
                continue
            if completeness == "complete" and missing_required:
                continue
            if completeness == "incomplete" and not missing_required:
                continue
            if role and resolved.properties.get("role") != role:
                continue
            if scope and resolved.properties.get("delivery_scope") != scope:
                continue
            rows.append(row)
        sort_keys = {
            "path": lambda row: row["resolved"].path,
            "state": lambda row: row["resolved"].review_state,
            "completeness": lambda row: (
                row["decisions_complete"],
                row["missing_required"],
            ),
            "role": lambda row: row["resolved"].properties.get("role", ""),
            "scope": lambda row: row["resolved"].properties.get("delivery_scope", ""),
            "tier": lambda row: row["resolved"].properties.get("validation_tier", ""),
        }
        sort = sort if sort in sort_keys else "path"
        direction = direction if direction in {"asc", "desc"} else "asc"
        rows.sort(key=sort_keys[sort], reverse=direction == "desc")
        counts = {
            "state": Counter(item.review_state for item in review.resolution.notebooks),
            "role": Counter(
                item.properties.get("role") for item in review.resolution.notebooks
            ),
        }
        return templates.TemplateResponse(
            request,
            "index.html",
            context(
                request,
                rows=rows,
                counts=counts,
                filters={
                    "q": q,
                    "state": state,
                    "completeness": completeness,
                    "role": role,
                    "scope": scope,
                },
                sort=sort,
                direction=direction,
                message=request.query_params.get("message", ""),
            ),
        )

    @app.get("/notebook", response_class=HTMLResponse)
    def notebook_detail(
        request: Request,
        path: str,
        _: None = Depends(authenticated),
    ) -> Any:
        facts = review.notebook_inventory(path)
        resolved = review.resolved_notebook(path)
        preview = None
        preview_error = None
        try:
            preview = build_preview(review.repository_root / path)
        except (OSError, ValueError) as error:
            preview_error = str(error)
        return templates.TemplateResponse(
            request,
            "detail.html",
            context(
                request,
                facts=facts,
                resolved=resolved,
                suggestions=suggestion_map(facts, review.inventory),
                preview=preview,
                preview_error=preview_error,
                message=request.query_params.get("message", ""),
            ),
        )

    @app.post("/notebook")
    async def update_notebook(
        request: Request,
        path: Annotated[str, Form()],
        reviewer: Annotated[str, Form()],
        csrf: Annotated[str, Form()],
    ) -> RedirectResponse:
        write_authorized(request, csrf)
        form = await request.form()
        values: dict[str, Any] = {}
        for name in EDITABLE_PROPERTIES:
            if name == "constraints":
                selected = [str(value) for value in form.getlist("constraints")]
                invalid = set(selected) - set(CONSTRAINTS)
                if invalid:
                    raise ValueError(f"unsupported constraints: {sorted(invalid)}")
                mode = str(form.get("constraints_mode", "inherit"))
                if mode not in {"inherit", "override"}:
                    raise ValueError("unsupported constraints mode")
                values[name] = selected if mode == "override" else None
                continue
            raw = str(form.get(name, "__inherit__"))
            values[name] = _property_value(name, raw, allow_inherit=True)
        review.update_notebook(path, values, reviewer=reviewer)
        return RedirectResponse(
            f"/notebook?path={quote(path, safe='')}&message=Draft+saved",
            status_code=303,
        )

    @app.post("/bulk")
    async def bulk_update(
        request: Request,
        property_name: Annotated[str, Form()],
        value: Annotated[str, Form()],
        reviewer: Annotated[str, Form()],
        csrf: Annotated[str, Form()],
    ) -> RedirectResponse:
        write_authorized(request, csrf)
        form = await request.form()
        paths = [str(item) for item in form.getlist("paths")]
        parsed = _property_value(property_name, value, allow_inherit=False)
        review.bulk_update(
            paths,
            property_name=property_name,
            value=parsed,
            reviewer=reviewer,
        )
        return RedirectResponse("/?message=Bulk+draft+saved", status_code=303)

    @app.get("/rules", response_class=HTMLResponse)
    def rule_form(request: Request, _: None = Depends(authenticated)) -> Any:
        return templates.TemplateResponse(request, "rules.html", context(request))

    @app.post("/rules/preview", response_class=HTMLResponse)
    def preview_rule(
        request: Request,
        rule_id: Annotated[str, Form()],
        include: Annotated[str, Form()],
        exclude: Annotated[str, Form()] = "",
        property_name: Annotated[str, Form()] = "role",
        value: Annotated[str, Form()] = "unknown",
        csrf: Annotated[str, Form()] = "",
    ) -> Any:
        write_authorized(request, csrf)
        parsed = _property_value(property_name, value, allow_inherit=False)
        exclusions = tuple(
            line.strip() for line in exclude.splitlines() if line.strip()
        )
        candidate = PurePosixPath
        affected = [
            notebook
            for notebook in review.resolution.notebooks
            if notebook.tracked
            and candidate(notebook.path).full_match(include)
            and not any(
                candidate(notebook.path).full_match(item) for item in exclusions
            )
        ]
        return templates.TemplateResponse(
            request,
            "rule_preview.html",
            context(
                request,
                rule={
                    "id": rule_id,
                    "include": include,
                    "exclude": exclude,
                    "property_name": property_name,
                    "value": value,
                },
                affected=affected,
                parsed_value=parsed,
            ),
        )

    @app.post("/rules")
    def create_rule(
        request: Request,
        rule_id: Annotated[str, Form()],
        include: Annotated[str, Form()],
        exclude: Annotated[str, Form()] = "",
        property_name: Annotated[str, Form()] = "role",
        value: Annotated[str, Form()] = "unknown",
        csrf: Annotated[str, Form()] = "",
    ) -> RedirectResponse:
        write_authorized(request, csrf)
        parsed = _property_value(property_name, value, allow_inherit=False)
        review.add_rule(
            rule_id=rule_id,
            include=include,
            exclude=exclude.splitlines(),
            property_name=property_name,
            value=parsed,
        )
        return RedirectResponse("/?message=Rule+added+to+draft", status_code=303)

    @app.get("/review", response_class=HTMLResponse)
    def final_review(request: Request, _: None = Depends(authenticated)) -> Any:
        return templates.TemplateResponse(
            request,
            "review.html",
            context(
                request,
                change=review.change,
                unresolved=review.unresolved_notebooks(),
            ),
        )

    @app.post("/save")
    def save_manifest(
        request: Request,
        confirm: Annotated[str, Form()],
        csrf: Annotated[str, Form()],
    ) -> RedirectResponse:
        write_authorized(request, csrf)
        if confirm != "save":
            raise ValueError("save confirmation was not supplied")
        path = review.save_manifest()
        return RedirectResponse(
            f"/?message=Manifest+written+to+{quote(str(path), safe='')}",
            status_code=303,
        )

    return app


def _property_value(name: str, raw: str, *, allow_inherit: bool) -> Any:
    if name not in EDITABLE_PROPERTIES:
        raise ValueError(f"unsupported property: {name}")
    value = raw.strip()
    if allow_inherit and value == "__inherit__":
        return None
    if name in VOCABULARIES:
        if value not in VOCABULARIES[name]:
            raise ValueError(f"unsupported {name} value: {value}")
        return value
    if name == "constraints":
        items = tuple(
            dict.fromkeys(item.strip() for item in value.split(",") if item.strip())
        )
        invalid = set(items) - set(CONSTRAINTS)
        if invalid:
            raise ValueError(f"unsupported constraints: {sorted(invalid)}")
        return list(items)
    if not value:
        raise ValueError(f"{name} must not be empty")
    maximum = 2_000 if name == "rationale" else 120
    if len(value) > maximum:
        raise ValueError(f"{name} is longer than {maximum} characters")
    return value


def _acceptable_write_origin(request: Request) -> bool:
    """Accept browser form posts from the same loopback server.

    A valid per-session CSRF token is the primary write authorization.  Origin
    remains a defence-in-depth check when a browser supplies it, but browsers
    and embedded webviews may omit it or serialize it as ``null``.
    """

    if request.headers.get("sec-fetch-site", "").casefold() == "cross-site":
        return False
    origin = request.headers.get("origin")
    if origin is None or origin == "null":
        return True
    try:
        parsed = urlsplit(origin)
        origin_port = parsed.port or _default_port(parsed.scheme)
        request_port = request.url.port or _default_port(request.url.scheme)
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname in _LOOPBACK_HOSTS
        and parsed.username is None
        and parsed.password is None
        and parsed.path in {"", "/"}
        and not parsed.query
        and not parsed.fragment
        and origin_port == request_port
    )


def _default_port(scheme: str) -> int | None:
    return {"http": 80, "https": 443}.get(scheme)
