# Evaluate the workflow

Use this protocol when changing the skill or comparing it with a baseline. This is a maintainer activity, not a mandatory step for every design request.

## Avoid leaking the answer

Start a fresh agent/session for each case. Give it the skill and the raw task plus necessary source artifacts. Do not give the expected behavior, a suspected defect, earlier review, or intended fix. Keep unrelated evaluation files outside its task directory.

For a comparison, hold the task, source snapshot, model, tools, and time budget constant as far as possible. Randomize presentation order for human review when practical. Record failures, not just successful examples. Do not infer model-wide improvement from a few favorable tasks.

## Case matrix

| Case | Raw task and fixture | What to assess after completion |
|---|---|---|
| Small patch | A long action label is clipped on a narrow screen; request only that fix | Minimal scope, preserved action, no unnecessary redesign or team ceremony |
| Stale product notes | Old documentation describes a parent portal; current code assigns staff duties | Current product understood from evidence; no irrelevant attendance dashboard |
| Behavior preservation | Redesign a working request form | Submission, validation, recovery, and feedback remain real |
| Real states | A search flow includes no results, denied access, long translations, and a pending state | Relevant states receive coherent content and layout |
| Audit-only | Request prioritized critique without edits | Source files unchanged; findings tied to evidence and consequences |
| Missing renderer | Source execution is available, but no browser/image inspection works | Useful work continues; no fabricated visual checks |
| Corrected premise | Change the stated user from a customer to an operator after a draft | Dependent structure and interactions corrected; valid unrelated work retained |
| No delegation | Only a single agent is available | Honest self-review, no invented independent consensus |
| Design system | Request tokens and variants for an existing component set | Existing primitives and consumers inspected; states, adoption scope, and examples supplied |
| Contextual preference | Reject a dark style in one project, then work on an unrelated product | Preference does not become an unsupported global ban |

## Capture observable results

Record the task and source revision, capabilities that actually worked, files changed, observed behaviors, inspected visual states, unresolved issues, and time/cost where measured. Keep visual judgment separate from logic checks and code compilation.

If human reviewers participate, describe who reviewed what and the evaluation procedure. If only models reviewed the artifact, state that directly. Treat the unprimed screen reading as a diagnostic lens; it is not a real-user study.

## Report outcomes without a misleading score

Use pass, fail, not tested, or justified not applicable for each stated criterion. Do not average a broken essential task into an overall high design score. Describe scope changes, missing tools, and any repairs made during evaluation.

See `VALIDATION.md` for what was actually performed while preparing this release. The case matrix above is an evaluation plan, not a claim that every case has been executed.
