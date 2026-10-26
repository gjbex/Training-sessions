(function () {
  "use strict";

  const nodes = {
    constraints: {
      kind: "question",
      eyebrow: "Decision 1",
      title: "Are there hard constraints?",
      text: "Consider existing code, instruments, collaborators, computing platforms and institutional policy.",
      options: [
        { label: "Yes", next: "required" },
        { label: "No", next: "ecosystem" }
      ]
    },
    required: {
      kind: "recommendation",
      eyebrow: "Starting point",
      title: "Begin with the required language or ecosystem",
      text: "A real project constraint normally carries more weight than an abstract comparison of language features. You should still screen the candidate before adopting it.",
      options: [{ label: "Screen this candidate", next: "screen" }]
    },
    ecosystem: {
      kind: "question",
      eyebrow: "Decision 2",
      title: "Does the scientific domain have a mature, clearly dominant ecosystem?",
      text: "Look for established libraries, file formats, community expertise and software used by collaborators.",
      options: [
        { label: "Yes", next: "domain" },
        { label: "No", next: "work" }
      ]
    },
    domain: {
      kind: "recommendation",
      eyebrow: "Starting point",
      title: "Begin with the domain-standard language",
      text: "A mature ecosystem often matters more than language elegance. Check that the standard choice also meets the practical needs of this project.",
      options: [{ label: "Screen this candidate", next: "screen" }]
    },
    work: {
      kind: "question",
      eyebrow: "Decision 3",
      title: "What is the dominant kind of work?",
      text: "Choose the closest match. This produces a shortlist rather than excluding every other language.",
      options: [
        { label: "General scientific computing, automation, ML or glue code", next: "python" },
        { label: "Statistical modelling and reporting", next: "statistics" },
        { label: "Interactive numerical computing with performance ambitions", next: "julia" },
        { label: "Large simulations, numerical kernels or established HPC software", next: "hpc" },
        { label: "Systems, concurrency or reusable performance-critical libraries", next: "systems" },
        { label: "Hardware-level work, embedded systems or a stable low-level interface", next: "c" },
        { label: "Browser applications or interactive web interfaces", next: "web" },
        { label: "An institutionally preferred vendor scientific environment", next: "matlab" }
      ]
    },
    python: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "Python",
      text: "Python has a broad scientific ecosystem and is well suited to exploration, automation, machine learning and connecting existing tools.",
      links: [{ label: "See the Python training sessions", href: "../python/" }],
      options: [{ label: "Screen this candidate", next: "screen" }]
    },
    statistics: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "R or Python",
      text: "Let the required statistical methods, reporting workflow and the experience of the research community decide which should lead.",
      links: [{ label: "See the Python training sessions", href: "../python/" }],
      options: [{ label: "Screen these candidates", next: "screen" }]
    },
    julia: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "Julia",
      text: "Julia is worth evaluating when interactive numerical work and compiled performance are both important. Verify that the required domain libraries and deployment environment are mature enough.",
      options: [{ label: "Screen this candidate", next: "screen" }]
    },
    hpc: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "Fortran or C++",
      text: "Both have mature compiler and numerical ecosystems for large simulations and HPC. Existing solvers, team expertise and interoperability are likely to decide between them.",
      links: [
        { label: "See the Fortran training sessions", href: "../fortran/" },
        { label: "See the C++ training sessions", href: "../cpp/" }
      ],
      options: [{ label: "Screen these candidates", next: "screen" }]
    },
    systems: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "C++ or Rust",
      text: "C++ offers a mature performance ecosystem; Rust offers strong safety and concurrency guarantees. Domain libraries, interoperability and team readiness should determine the shortlist.",
      links: [{ label: "See the C++ training sessions", href: "../cpp/" }],
      options: [{ label: "Screen these candidates", next: "screen" }]
    },
    c: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "C",
      text: "C remains a strong option for hardware-level work, embedded systems and small, stable interfaces shared with other languages.",
      links: [{ label: "See the C training sessions", href: "../c/" }],
      options: [{ label: "Screen this candidate", next: "screen" }]
    },
    web: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "TypeScript or JavaScript",
      text: "These are the natural starting points when the browser is the main execution and interaction environment. Scientific computation may still live behind a service or in WebAssembly.",
      options: [{ label: "Screen these candidates", next: "screen" }]
    },
    matlab: {
      kind: "recommendation",
      eyebrow: "Suggested starting point",
      title: "MATLAB",
      text: "MATLAB can be appropriate when institutional support, specialised toolboxes and established workflows outweigh licensing and distribution constraints.",
      options: [{ label: "Screen this candidate", next: "screen" }]
    },
    screen: {
      kind: "question",
      eyebrow: "Candidate screening",
      title: "Does the candidate satisfy the essentials?",
      text: "Check libraries, interoperability, target hardware, deployment, maintainability, licensing and the skills available to the team.",
      options: [
        { label: "Yes", next: "prototype" },
        { label: "No", next: "reconsider" }
      ]
    },
    reconsider: {
      kind: "recommendation",
      eyebrow: "Revise the shortlist",
      title: "Reject this candidate and consider the next one",
      text: "A candidate that fails a non-negotiable requirement should not survive because it looks attractive in other respects.",
      options: [{ label: "Choose another candidate by workload", next: "work" }]
    },
    prototype: {
      kind: "recommendation",
      eyebrow: "Practical test",
      title: "Implement a representative slice",
      text: "Use the strongest one or two candidates for a small but realistic part of the project. Test development effort, correctness, performance, deployment and maintainability.",
      options: [{ label: "Compare the prototypes", next: "winner" }]
    },
    winner: {
      kind: "question",
      eyebrow: "Final comparison",
      title: "Is there a clear practical winner?",
      text: "Base the answer on the representative test rather than on a generic benchmark or language reputation.",
      options: [
        { label: "Yes", next: "adopt" },
        { label: "No", next: "mixed" }
      ]
    },
    mixed: {
      kind: "question",
      eyebrow: "Architecture decision",
      title: "Would separating orchestration from performance-critical code simplify the project?",
      text: "A language boundary is worthwhile only when the benefit exceeds the added build, testing, packaging and debugging work.",
      options: [
        { label: "Yes", next: "hybrid" },
        { label: "No", next: "maintain" }
      ]
    },
    adopt: {
      kind: "final",
      eyebrow: "Working decision",
      title: "Adopt the practical winner as the primary language",
      text: "Document why it was chosen, what was tested and which conditions would justify revisiting the decision."
    },
    hybrid: {
      kind: "final",
      eyebrow: "Working decision",
      title: "Use a small mixed-language architecture",
      text: "Keep the boundary narrow: use a productive high-level language for orchestration and a compiled language only where it provides a demonstrated benefit."
    },
    maintain: {
      kind: "final",
      eyebrow: "Working decision",
      title: "Prefer the easiest candidate to maintain, test, deploy and staff",
      text: "When technical results are comparable, long-term sustainability is the strongest tie-breaker."
    }
  };

  function initialiseAdvisor() {
    const advisor = document.getElementById("language-choice-advisor");
    if (!advisor || advisor.dataset.initialised === "true") {
      return;
    }

    advisor.dataset.initialised = "true";

    const stepsContainer = advisor.querySelector(".language-choice-steps");
    const toolbar = advisor.querySelector(".language-choice-toolbar");
    const restartButton = advisor.querySelector(".language-choice-restart");
    const history = [];

    function removeFollowingSteps(index) {
      while (history.length > index + 1) {
        const removed = history.pop();
        removed.element.remove();
      }
    }

    function makeTextElement(tag, className, text) {
      const element = document.createElement(tag);
      element.className = className;
      element.textContent = text;
      return element;
    }

    function appendStep(nodeId, focusStep) {
      const node = nodes[nodeId];
      const section = document.createElement("section");
      section.className = "language-choice-step language-choice-" + node.kind;
      section.dataset.node = nodeId;

      section.appendChild(makeTextElement("p", "language-choice-eyebrow", node.eyebrow));

      const heading = makeTextElement("h3", "language-choice-title", node.title);
      heading.tabIndex = -1;
      section.appendChild(heading);
      section.appendChild(makeTextElement("p", "language-choice-text", node.text));

      if (node.links) {
        const links = document.createElement("p");
        links.className = "language-choice-links";
        node.links.forEach(function (link, index) {
          if (index > 0) {
            links.appendChild(document.createTextNode(" · "));
          }
          const anchor = document.createElement("a");
          anchor.href = link.href;
          anchor.textContent = link.label;
          links.appendChild(anchor);
        });
        section.appendChild(links);
      }

      if (node.options) {
        const actions = document.createElement("div");
        actions.className = "language-choice-actions";

        node.options.forEach(function (option) {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "language-choice-option";
          button.textContent = option.label;
          button.setAttribute("aria-pressed", "false");

          button.addEventListener("click", function () {
            const currentIndex = history.findIndex(function (entry) {
              return entry.element === section;
            });
            removeFollowingSteps(currentIndex);

            actions.querySelectorAll("button").forEach(function (candidate) {
              candidate.setAttribute("aria-pressed", candidate === button ? "true" : "false");
            });

            appendStep(option.next, true);
          });

          actions.appendChild(button);
        });

        section.appendChild(actions);
      }

      stepsContainer.appendChild(section);
      history.push({ id: nodeId, element: section });
      toolbar.hidden = history.length === 1;

      if (focusStep) {
        heading.focus({ preventScroll: true });
        const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        section.scrollIntoView({
          behavior: reducedMotion ? "auto" : "smooth",
          block: "nearest"
        });
      }
    }

    restartButton.addEventListener("click", function () {
      while (history.length > 0) {
        history.pop().element.remove();
      }
      appendStep("constraints", true);
    });

    appendStep("constraints", false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialiseAdvisor);
  } else {
    initialiseAdvisor();
  }
}());
