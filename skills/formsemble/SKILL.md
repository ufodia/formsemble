---
name: formsemble
license: MIT
description: Understand, design, implement, and review digital-product interfaces by tracing user intent through real behavior to rendered evidence. Use for interface work from focused fixes to complete flows or design systems. Do not use for unrelated backend work or standalone illustration generation.
---

# Formsemble

Run a design studio organized around a shared understanding of the product and evidence from the actual result. Treat specialties as accountable responsibilities, not fictional people. Keep the product's meaning intact from request to screen to working interaction.

## Operating contract

- Read the relevant project instructions, existing product/design records, affected implementation, and supplied references before changing the interface. Prefer observed behavior and current source to guesses from a name or an old mockup. Distinguish the current implementation from the user's requested future behavior.
- Follow the user's scope and existing authorization. Continue through useful reversible work without approval ceremonies. Ask a focused question only when a consequential unknown cannot be resolved from available evidence; continue unaffected work while it is unresolved.
- Preserve real routes, actions, permissions, data semantics, content, and integrations unless the request changes them. A visual redesign does not authorize deleting functionality or inventing product claims.
- Use project-specific design skills for their product rules and tool-specific skills for their required workflows. Let Formsemble coordinate; do not replace a supplied design system with its own house style.
- Match the user's language in conversation. Keep code, components, and documentation consistent with the project. Do not claim people, research participants, independent reviewers, tools, or observations that did not exist.

## 1. Choose the smallest useful studio

Determine both the **scope** and the requested **deliverable**. Respect audit-only, direction-only, or implementation requests. An audit must not modify the product; a direction proposal must not claim working behavior; an implementation request must not end at a plan or representative demo.

| Scope | Working method | Required result |
|---|---|---|
| Patch: a bounded UI defect or copy/layout correction | Inspect the affected area; describe the intended change briefly; implement; check it and nearby behavior | Focused fix and honest verification; no new design manual, visual alternatives, or mandatory agents |
| Flow: one screen, component family, or journey | Refresh the relevant product understanding; make screen commitments; build; use focused review | Complete requested surface and its relevant states |
| Studio: new product, major redesign, or cross-screen system | Reconstruct the product; explore meaningful directions; finish a representative slice; extend and review | Coherent requested scope, working interactions where required, durable decisions, evidence |

For audits, use the relevant scope's understanding and review steps, then deliver prioritized findings. For concept work, label assumptions and future behavior; render the proposal when tools allow. Do not manufacture a pass for implementation checks that cannot yet apply.

Detect available file, rendering, browser, image, implementation, and delegation capabilities. Use actual tool interfaces; never assume a browser, Figma access, an image generator, or subagents exist. After a capability fails, retry only when a concrete new diagnostic supports a different outcome; otherwise continue available work and mark the missing check. See [portability](references/portability.md) when host capabilities affect execution.

## 2. Establish a product understanding you can use

For Flow and Studio work, consult the relevant sections of [product understanding](references/product-model.md). Reuse verified facts; investigate only the relevant gaps. Load supporting references only as their decisions become relevant; do not read the whole manual for a bounded change.

Write a compact teach-back:

> This surface helps **[person in a situation]** accomplish **[job]** by **[interaction]**. Success means **[observable outcome]**. Preserve **[important existing behavior]**.

Use actual domain objects and walk through a primary scenario and a relevant failure or edge case. Mark consequential statements as **observed**, **user supplied**, or **assumed**, with a source where possible. Never relabel an assumption as evidence because another agent repeated it.

Translate the important task into a short trace:

`user need → screen question → visible affordance → action/state transition → observed outcome`

Specify which checks will show that the trace works before implementing it. If the user's correction changes the product model, update dependent layout, language, states, and interactions; do not repair only the sentence they noticed.

Present the teach-back briefly and proceed. It is an alignment aid, not an approval gate. Use [the project note template](assets/project-note-template.md) only when a persistent record is useful; do not fill every field mechanically.

## 3. Assign accountable specialties

For nontrivial work, read [studio responsibilities](references/studio-roles.md). Cover product/UX, art direction, content, implementation, and quality; combine responsibilities when efficient.

If delegation is available and useful, parallelize independent analysis or review with a small number of agents. Give each the relevant artifacts, explicit scope, expected output, and file ownership. Keep one implementation owner per file. Reviewers should return concrete findings before seeing the lead's preferred verdict. Resolve conflicts using the product contract and evidence, not a vote or a fabricated consensus.

If delegation is unavailable, perform focused sequential passes yourself. Call them self-review; do not present them as independent minds. Never make parallel orchestration a prerequisite to helping the user.

## 4. Direct the visual work

For new visual direction or meaningful aesthetic change, read [art direction](references/art-direction.md). Translate words such as "premium," "playful," or "professional" into observable decisions about composition, typography, density, content, materials, motion, and interaction feedback.

For Studio work without an established direction, compare two materially different hypotheses using the same representative screen and realistic content. If creating both complete variants would waste effort, use compact sketches or rationale and implement the recommended direction. A palette swap is not a separate concept. Do not demand a user choice unless the alternatives represent an unresolved consequential preference.

Choose a product-specific visual signature and a coherent grammar. Reuse sound existing tokens and components. Explain the strongest decisions through the task and audience. Do not universalize taste rules or add decorative complexity to justify "premium."

For an explicit design-system deliverable, inventory existing primitives and consumers; define semantic token roles and the required component variants, states, usage guidance, and responsive behavior. Include the migration or adoption boundary and representative examples. Do not create a full library when the request is only to refine one screen.

## 5. Build a complete representative slice, then finish the scope

For implementation, read [building the interface](references/implementation.md). First finish a representative route or interaction with realistic content, important states, and the target device constraints. Inspect it before propagating the design to other screens.

Implement real controls, navigation, and feedback using the existing stack and contracts. Keep prototype-only behavior explicit. Use actual assets when available; use image tools for requested imagery when appropriate, never as proof of a working UI. Avoid changing architecture, dependencies, or deployment settings merely to make styling easier.

Resolve material findings in the representative slice, then extend the agreed grammar across the requested scope. If a necessary check is unavailable, record the gap and continue useful authorized work without treating the slice as verified. Recheck shared components in their affected contexts. Do not stop at the slice when the user asked for the whole flow or product.

## 6. Inspect, challenge, and repair

Read [review and evidence](references/review.md) for Flow and Studio work or any verification claim.

1. Inspect rendered output at the relevant sizes and states using available visual tools. Source code and a successful build do not establish appearance.
2. Exercise the primary action and its important recovery path when implementation is in scope. A screenshot does not establish functionality.
3. Check relevant accessibility and content resilience, including keyboard/focus when applicable, contrast, names/labels, long text, and narrow layouts. Describe the checks performed; do not imply a full compliance audit.
4. For substantial changes with a fresh reviewer and image inspection available, run an **unprimed screen reading**: give the reviewer only the rendered artifact and minimal situation, withhold the product explanation, and ask what the interface enables and what happens next. Then compare with the contract. Treat discrepancies as diagnostic hypotheses to investigate, not findings from real users. Otherwise label the check as self-review or unavailable.
5. Record actionable defects: location/state, observation, user consequence, evidence, severity, smallest sufficient repair, and recheck condition. Fix blockers and major issues within scope; inspect the changed result again.

Keep separate statuses for intent, task completion, visual craft, accessibility checks, responsiveness/content fit, and behavior preservation: **pass**, **fail**, **not tested**, or **not applicable with a reason**. "Tool unavailable" means not tested. Do not average failures into a favorable overall score.

After two discretionary polish rounds, continue only to fix a concrete material defect or satisfy an explicit requirement. Do not end while a repairable in-scope blocker remains; if blocked, finish other work and identify the precise remaining limitation.

For multi-screen or handoff-heavy work with local evidence, use [the review record template](assets/review-template.json) and the read-only checker:

```text
python3 <skill-directory>/scripts/check_review.py <report.json> --project-root <project-directory>
```

Resolve the actual skill directory; angle-bracket values are placeholders. The checker detects malformed records, missing or changed declared files, unsatisfied checks, and incompatible evidence methods. Its `complete` flag means all recorded checks are satisfied; it does not decide whether an audit or delivery task is finished. A complete audit may correctly document failures. The checker does not inspect images, prove that a review happened, certify accessibility, or judge design quality. Never fabricate evidence to satisfy it. If files or Python are unavailable, provide a concise evidence table and disclose the limitation.

## 7. Preserve decisions and deliver clearly

For work likely to continue, read [project memory](references/project-memory.md). Reuse an existing design record or create a small project-local one when authorized and useful. Keep product facts, behavioral invariants, accepted direction, scoped preferences, reasons for rejected directions, and open verification gaps. Revalidate stale material on reuse. Never store project-specific facts in this installed skill.

Deliver the requested artifact or implementation and explain:

- What changed and how it supports the product's main task.
- The few design decisions that matter and their practical tradeoffs.
- What was actually verified, against which artifact, and what remains unverified.
- Any unresolved material issue and the next concrete action it requires.

Link the actual preview, files, or changed project as the host permits. Keep the response proportional. Do not attach fictional agency conversations, ceremonial role reports, unsupported conversion claims, or a self-awarded quality score.
