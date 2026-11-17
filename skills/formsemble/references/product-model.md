# Understand the product before directing its appearance

## Gather the minimum useful evidence

Inspect the affected routes/screens, component structure, domain types, current data examples, tests for critical behavior, existing design tokens, supplied references, and product notes. Run the relevant current interface when available. Follow project conventions and avoid unrelated private data.

Use a small evidence table only when facts conflict or decisions need traceability:

| Statement | Status | Source | Design consequence |
|---|---|---|---|
| A visit request is submitted through an existing form | Observed | Component/handler or witnessed interaction | Preserve fields, submission, and feedback |
| Parents should find the age range early | User supplied | Current brief | Give the information meaningful hierarchy |
| Most visits will come from phones | Assumed | No analytics supplied | Prioritize a reversible narrow-layout hypothesis |

Treat current user instructions as intent, source/runtime as evidence of implementation, and older documentation as potentially stale. Explain consequential disagreements. Do not silently preserve a known bug merely because it is current behavior; distinguish intentional invariants from defects.

## Build a compact product model

Capture only what changes the design:

- **Person and situation:** actual role, task frequency, environment, device, language, ability/access constraints when known.
- **Job and outcome:** what the person needs to decide or accomplish; what observable result ends the task.
- **Domain objects:** the real nouns, relationships, units, and status meanings. Do not invent generic "projects," "activity," or "analytics" to fill a layout.
- **Journey:** entry, orientation, decision, action, feedback, recovery, and next step.
- **Invariants:** routes, permissions, calculations, actions, content, integrations, and error meanings that must remain.
- **Constraints:** platform, stack, existing system, audience, scope, delivery format, known technical limitations.
- **Uncertainty:** assumption, impact if wrong, cheapest way to resolve it, whether work can proceed.

Do not infer a whole product category from its brand name. A playful name can belong to a serious tool, and a location feature does not imply that a map should dominate every screen.

## Make screen commitments

Use one short row per consequential task, not per decorative element:

| Need | Screen question | Visible affordance | Action and state | Acceptance evidence |
|---|---|---|---|---|
| Arrange a visit | Is this suitable, and how can I visit? | Relevant age/hours information and a clearly labeled visit control | Existing form opens; validation and confirmation follow actual response | Rendered hierarchy plus exercised success/failure path |

Specify target state and completion criteria. "Improve engagement" is not an acceptance condition without an agreed observable measure. A task can require several controls; avoid an artificial one-button rule for dense professional tools.

For each relevant screen, ask:

1. What must the person understand before acting?
2. What information must be visible at the moment of choice?
3. What action is expected, and what does it actually do?
4. What can go wrong, and how can they recover?
5. What must remain consistent with the rest of the product?

Walk the model through one main scenario and at least one relevant edge case for a Flow or Studio request. Choose edge cases from evidence: no results, denied location, expired session, long labels, duplicate submission, an interrupted task, or a permission boundary. Do not build every imaginable state regardless of scope.

## Resolve uncertainty without stalling

First inspect available material. If a missing answer changes the primary journey, audience, permissions, or a costly external action, ask one focused question and continue unaffected work. Otherwise state a reversible assumption and proceed. Group essential questions; do not turn discovery into a long intake form.

For a greenfield concept, propose a coherent provisional model based on the brief and label it as proposed. Do not invent interviews, analytics, customer demand, business partnerships, testimonials, operating hours, prices, or actual user preferences.

## Repair misunderstandings at their source

When the user says "you misunderstood," "this is for teachers, not parents," or otherwise corrects the premise:

1. State the corrected product fact in ordinary language.
2. Identify affected screen commitments, content, navigation, actions, states, and tokens.
3. Preserve valid unrelated work; revise the dependent pieces.
4. Update the project record with the correction and scope.
5. Recheck the relevant journey and rendered result.

Do not treat a premise change as a request to replace a title. Conversely, do not use a local wording correction as authorization to redesign the entire product.

## Keep inference distinct from validation

A synthetic persona or model walkthrough can reveal questions to investigate. It cannot establish how real users behave. Label model-based interpretation as a hypothesis. Reserve "user tested," measured improvement, research findings, and conversion results for actual supplied or observed evidence.
