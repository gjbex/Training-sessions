# Choosing a programming language for research

Researchers rarely choose a programming language in isolation.  Existing
software, instruments, collaborators, computing platforms and conventions in a
scientific domain may already limit the sensible options.  When those
constraints do not determine the answer, the questions below can help you form
a shortlist.

> **Caveat:** This guide suggests a starting point; it does not prescribe a
> universally best language.  Treat its outcome as a hypothesis to test with a
> representative part of your project.

<div id="language-choice-advisor"
     class="language-choice-advisor"
     role="region"
     aria-labelledby="language-choice-advisor-title">
  <h2 id="language-choice-advisor-title">Interactive decision guide</h2>
  <p class="language-choice-introduction">
    Answer one question at a time.  Your earlier answers remain visible and can
    be changed at any point.
  </p>
  <div class="language-choice-steps" aria-live="polite"></div>
  <div class="language-choice-toolbar" hidden>
    <button type="button" class="language-choice-restart">Start again</button>
  </div>
</div>

<noscript>
This guide needs JavaScript for its step-by-step presentation.  The underlying
recommendations are:

  * honour hard constraints such as existing code, instruments and platforms;
  * prefer a mature domain ecosystem when one clearly exists;
  * otherwise shortlist languages according to the dominant work;
  * screen the shortlist for libraries, interoperability, hardware,
    deployment, maintainability and licensing;
  * test the strongest candidates with a representative slice of the project.
</noscript>

## Interpreting the result

The suggested language is a candidate, not a verdict.  Before committing to it,
consider:

  * whether the required scientific libraries and data formats are well
    supported;
  * whether collaborators can read, review and maintain the software;
  * whether it runs on the required hardware and is practical to deploy;
  * whether its performance is adequate for a representative workload;
  * whether the toolchain, licensing and governance model are sustainable;
  * whether interoperability costs outweigh the benefits of using more than
    one language.

A small mixed-language architecture can be useful: for example, a productive
high-level language for orchestration and a compiled language for a few
performance-critical kernels.  However, every language boundary adds build,
testing, packaging and debugging work.

Revisit the decision when the project, team or deployment environment changes.
