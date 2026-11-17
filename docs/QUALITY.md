# Quality and evidence model

## Product understanding

A useful design must preserve the chain from the user's need to the visible interface, its actual action, and the resulting state. Formsemble records consequential facts as observed, user supplied, or assumed. Current source and runtime evidence can correct outdated product notes; an explicit new user requirement can intentionally change existing behavior.

The product teach-back is an alignment aid, not a permission ceremony. A reversible assumption can keep work moving when it does not change the core task or create a consequential external action.

## Accountable design responsibilities

The lead maintains scope and coherence. UX defines the journey and screen commitments. Art direction makes deliberate visual choices. Content makes controls and states understandable. Engineering implements the requested behavior. Quality review identifies concrete defects and verifies fixes.

These responsibilities can be combined or delegated. Only actually separate reviewers count as independent reviews. Neither simulated role labels nor a long fictional meeting establishes a team.

## Unprimed screen reading

A fresh reviewer receives the rendered artifact and only the context needed to understand the situation. Before seeing the intended answer, the reviewer identifies the apparent purpose, likely first action, expected result, and ambiguity. The lead then compares that reading with the product contract.

Treat a mismatch as a diagnostic hypothesis. Do not label it a user-research result, a measured conversion effect, or proof that every user will misunderstand the screen. If the reviewer inherited the answer, cannot inspect images, or saw the rationale first, label the pass context-aware review or self-review.

## Six separate review dimensions

| Dimension | Appropriate question | Typical evidence |
|---|---|---|
| Intent | Does this surface support the actual user and task? | Contract comparison and source/artifact observations |
| Task | Can the intended action and relevant recovery complete? | An exercised running interaction |
| Visual | Does the rendered result express the intended hierarchy and craft? | Current captured states actually inspected |
| Accessibility | Did the specifically scoped checks pass? | Relevant semantic, keyboard, contrast, or assistive-technology evidence |
| Responsiveness | Does the UI remain usable at the relevant sizes and content extremes? | Observed sizes/states with realistic content |
| Preservation | Do required behaviors and meanings remain intact? | Focused diffs and relevant behavior checks |

Technical checks such as a build or type check remain useful, but do not substitute for the other dimensions. A DOM simulation can test logic without proving browser layout, native validation, keyboard navigation, or screen-reader behavior.

## Review-record semantics

The optional checker validates a record, its declared files, and method/status consistency. Its two main outputs have different meanings:

- `valid`: the record is structurally acceptable and declared files match their recorded fingerprints.
- `complete`: all recorded checks are satisfied and no blocking unresolved findings remain under the checker's explicit rules.

The second output is not a judgment about whether the user's task has been delivered. An audit that correctly identifies unresolved defects can be finished while `complete` is false. Likewise, `complete: true` does not certify taste, truthful observation, comprehensive accessibility, or production readiness.

The checker reads only declared local paths. It cannot detect an omitted dependency or prove that a screenshot came from a particular running build. It checks image declarations and supported extensions, not pixel content. Preserve the capture's route, viewport, state, and build context in the evidence description or a linked local note.

## Critique should lead to a correction

Every material finding needs an affected location/state, an observation, a user consequence, evidence, severity, a bounded repair, and a recheck condition. In JSON records, put those details inside `description`; unknown extra keys are rejected.

Resolve in-scope blockers and major defects. Use discretion for optional polish. After two discretionary polish rounds, continue only for a concrete material defect or explicit requirement. When a capability is unavailable, complete useful work and disclose the remaining check rather than inventing a result.

## Distinctiveness and limits

Formsemble seeks product-specific composition and interaction, while preserving usability and existing constraints. It has no universal palette, font ban, or predetermined visual style. It does not guarantee original output from every model or establish that the overall approach is globally unprecedented.
