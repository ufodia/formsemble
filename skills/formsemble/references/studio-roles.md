# Coordinate a studio with accountable work

## Assign responsibilities, then decide who performs them

| Responsibility | Owns | Useful output |
|---|---|---|
| Design lead | Scope, product coherence, arbitration, final delivery | Product model, chosen direction, resolved tradeoffs |
| Experience designer | Information architecture, interaction, recovery | Screen commitments and relevant state transitions |
| Art director | Composition, typography, visual signature, rhythm | Concrete direction using the product's actual content |
| Content designer | Meaning, hierarchy of language, labels, instructions, errors | Clear copy tied to the action and domain |
| Interface engineer | Components, tokens, integration, responsive behavior | Working requested interface with preserved contracts |
| Accessibility and quality reviewer | Usability obstacles, focus/semantics, robustness, evidence | Prioritized reproducible findings |
| Unprimed reader | What the rendered artifact communicates without its rationale | Independent interpretation and uncertainty |

These are coverage areas, not seven required agents or fictional staff members. The lead can also implement. Consolidate related responsibilities. For a normal flow, a lead plus one or two reviewers is usually enough; a patch often needs only one executor. Detect the actual available capacity.

## Delegate with a bounded work packet

Include:

- Task and deliverable, with relevant product contract and constraints.
- Exact artifact paths, routes, or screenshots to inspect.
- Question the specialty must answer and the expected output shape.
- Write ownership, if any; default reviewers to read-only.
- Known capabilities and limitations, without preloading the desired conclusion.

Ask reviewers to return a short decision or finding, source/evidence, consequence, and proposed correction. Avoid open-ended instructions such as "think of everything" or "act like the world's best designer."

Parallelize independent reading, concept exploration, or checks. Sequence work that depends on a selected direction, shared tokens, or a live page under active modification. Never let two agents unknowingly modify the same files or drive the same interactive session at once.

Do not change model selection, permissions, account settings, or experimental host features just to create a larger team. Do not require recursive agent spawning. A skilled single-agent pass remains useful when orchestration is absent.

## Use two different review lenses

### Contract review

Give the reviewer the brief, behavioral invariants, and actual implementation/artifacts. Ask whether the requested task is supported and the design satisfies its constraints. This reviewer needs product context.

### Unprimed screen reading

Use a fresh reviewer when available. Give only the rendered screen or prototype and minimal situation needed to read it. Do not supply the product explanation, intended primary action, desired verdict, implementation rationale, prior critique, or expected answers before the first response.

Ask:

> From this screen, what can someone accomplish? What would you do first? What result would you expect? Which details are unclear? Point to visible evidence and state uncertainty.

If the flow requires familiar domain context, provide that context without revealing the answer. Do not create an artificial test that expects an expert tool to explain its whole domain to a novice. For interaction claims, give access to a running prototype; a static image only supports interpretation of the captured state.

After receiving the independent reading, compare it with the screen commitments. Investigate consequential mismatches through visible hierarchy, copy, affordances, or actual behavior. A model's mistake is a signal, not proof that users will fail. If the reader cannot inspect images or has inherited the answer, label the pass as context-aware review, not unprimed review.

Do not use a single screenshot-reading response as a universal approval gate. Weigh it against the task, platform conventions, and other evidence.

## Resolve disagreements explicitly

Use this priority order within the user's instructions and project constraints:

1. Broken primary task, inaccessible essential control, inaccurate content, or violated behavioral contract.
2. Clear evidence of confusion, missing information, or responsive failure.
3. Consistency with the chosen direction and product-specific hierarchy.
4. Optional aesthetic preference.

A visual preference cannot waive a functional defect. A technical convenience cannot erase the product's essential action. Ask the lead to choose the smallest sufficient correction and record the reason for a consequential tradeoff. Do not decide by majority vote, number of role labels, or a made-up numerical score.

Use a concrete resolution record only when useful:

| Concern | Evidence | Decision | Recheck |
|---|---|---|---|
| Large imagery pushes essential visit information below the narrow screen's first decision point | Captured layout with actual copy | Reduce image height and move age/hours context alongside the action | Inspect the same viewport and long-text variant |

## Keep collaboration invisible where it adds no value

Tell the user what was learned, what changed, and what remains uncertain. Do not print role speeches, simulated meetings, or lengthy "team consensus" narratives. Only claim independent review when an independent agent actually reviewed the relevant artifact. Never imply that real human designers participated.
