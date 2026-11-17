# Keep a small, project-specific design memory

## Reuse the project's existing record

Look for an existing design specification, `DESIGN.md`, product brief, token documentation, or established equivalent. Update the relevant place rather than creating parallel conflicting records. Create a compact `DESIGN.md` in the project only when the task authorizes files and continued work makes it useful. For a tiny change or audit-only task with no file-writing request, keep the needed context in the response.

Never edit this installed skill to store a project's information. Never mix personal facts, unrelated projects, credentials, or private user data into design memory. Screenshots and diagnostic logs should use representative content when possible.

## Retain what changes future decisions

Keep:

- Product purpose, intended audience, important domain objects, and primary journey.
- Behavioral invariants and the scope of any authorized changes.
- Accepted visual direction and the rationale for consequential decisions.
- Links to canonical tokens/components and actual supporting evidence.
- Relevant user corrections, with scope and provenance.
- Rejected directions and the reasons they failed in this context.
- Open issues, assumptions, and verification limitations.

Do not store transcripts, imaginary meetings, repeated generic principles, lengthy role reports, or a screenshot diary with no decisions attached.

## Scope preferences carefully

Represent a preference as a contextual decision:

```text
Preference: Use a brighter surface for this parent-facing page.
Scope: This product's enrollment flow.
Source: User feedback on the current design.
Reason: The previous direction felt too severe for the intended tone.
Status: Current; revisit only if the brief or explicit feedback changes.
```

Do not convert this into "the user never likes dark UI" or impose it on another product. A user's explicit current correction supersedes stale design notes. Distinguish user-approved decisions from the agent's working recommendations; do not mark a choice approved merely because work continued.

## Revalidate when work resumes

Read the relevant record and compare it with the current request and source/artifacts. If implementation or scope changed, refresh affected facts before relying on them. Keep accepted decisions unless there is a reason to revisit them. Summarize only the delta in chat.

When a product fact changes, trace its consequences through screen commitments, navigation, content, states, shared components, and relevant review evidence. A changed build can invalidate earlier screenshots. Preserve old decisions as superseded only when their history remains useful.

## Keep a concise decision record

| Decision | Status | Why | Scope/source | Revisit condition |
|---|---|---|---|---|
| Preserve the existing visit request handler | Observed constraint | Requests must continue reaching the service | Current form implementation | Explicit change to the enrollment flow |
| Use the information-led direction | Working recommendation | Relevant details support the main decision | Current design review | User feedback or evidence of a different task |

Use the bundled project-note template as a starting point, removing unused sections. A useful one-page record is better than a complete form filled with invented detail.
