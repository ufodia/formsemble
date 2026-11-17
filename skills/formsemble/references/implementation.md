# Build an interface that retains its meaning

## Inspect the implementation contract

Read relevant project instructions and establish the current framework, routing, component library, tokens, data flow, form handling, permissions, and existing checks. Locate the smallest useful change boundary. Inspect the working tree and preserve unrelated user work.

For a visual redesign, list the few behaviors at risk: a form's submission handler, map selection semantics, filters, stored choices, authorization, calculation meaning, or navigation destinations. Treat them as invariants unless the user requests otherwise. Fix demonstrated defects within scope; do not entrench them as requirements.

Do not replace real data with mock data in a working product or silently invent new APIs. In a prototype, make representative data and simulated behavior explicit in the handoff. Never present a decorative control as implemented functionality.

## Finish a representative slice early

Choose a slice that tests the difficult design decisions, not merely the easiest hero section. Include:

- Realistic content and the primary task.
- A meaningful transition and completion/feedback state.
- Important loading, empty, error, or permission conditions.
- The target device constraints and a narrower or denser case where relevant.
- The shared primitives and tokens that later work will depend on.

Render and inspect it. Correct its significant problems before expanding the pattern. Then complete all requested screens or states; the slice is a learning step, not an excuse to stop early.

## Preserve architecture proportionately

Use the project's framework and component conventions. Prefer semantic controls and existing accessible primitives. Centralize repeated tokens when useful. Keep interaction/state logic separate enough from styling to avoid changing behavior accidentally.

Avoid framework migrations, dependency additions, global resets, wholesale component-library replacement, or deployment changes unless needed for the authorized goal. If a missing capability affects only optional polish, use a sensible existing alternative. Respect lockfiles and existing install/test commands.

Do not commit, publish, deploy, contact people, or change external account settings solely because this skill is running. Follow the user's actual request and the host's authorization rules.

## Design states and content together

Build the applicable states into the component model. Preserve values and provide recovery after errors. Keep disabled, unavailable, loading, and empty meanings distinct. Announce relevant state changes with platform-appropriate semantics; color alone must not convey an essential distinction.

Use realistic stress content: long Turkish labels when relevant, accented characters, long names, large counts, missing imagery, wrapping error messages, and zero results. Avoid lorem ipsum that hides the actual layout problem. Do not invent testimonials, prices, numerical outcomes, or product capabilities.

For multilingual scope, check the actual supported translations, text expansion, locale-aware dates/numbers/units, and right-to-left layout when applicable. Prefer logical layout properties where the existing stack supports them. Do not claim an RTL or localization review without the relevant rendered content and interactions.

For web layouts, inspect actual viewport behavior and content reflow. For native apps, inspect the relevant device, platform navigation, text scaling, safe areas, keyboard behavior, and orientation requirements. A web screenshot cannot establish native behavior.

When animation changes meaning or control availability, verify its timing and interruption. Respect reduced-motion preferences where relevant. Do not make essential content depend on motion, hovering, or a gesture without an appropriate alternative.

## Use assets deliberately

Use supplied or authorized product assets and check their fit. Prefer real typography and controls over rasterized UI text. Use image-generation or retrieval tools for appropriate artwork when available and authorized by the task; they do not generate evidence of a running interface.

If final assets are missing, use a clearly identified temporary treatment without inventing brand facts. State whether external fonts or images introduce a runtime dependency. Avoid new remote requests when local assets meet the task.

## Check performance risks introduced by the design

When the change adds large images, fonts, animation, expensive rendering, or a long list, inspect the relevant loading and interaction costs. Use appropriately sized assets, reserve image space to reduce layout movement, and avoid unnecessary font variants or perpetual animation. Preserve existing list/windowing behavior when it matters. Measure with available project tools when a concrete risk warrants it; do not invent timings, require a new performance service, or apply one universal score as a design gate.

## Verify the changed risk

Run existing relevant checks for the change, such as a build, type checks, or a focused behavior test. Do not write trivial tests that only restate a padding value. Add a focused regression test when a demonstrated behavior bug merits one.

Exercise the primary interaction and relevant recovery path. Inspect the final rendered version after fixes. If a shared component changed, check its other materially affected contexts. Keep build/static validation, interaction observations, and visual inspection distinct in the handoff.

If rendering or runtime execution is unavailable, continue with useful source-level work and identify the unverified checks. Do not alter a status to passed because the tools needed to check it are missing.
