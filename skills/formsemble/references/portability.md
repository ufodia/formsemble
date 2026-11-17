# Run the same method on different hosts

## Keep the portable core simple

Use the shared `SKILL.md` with `name` and `description` frontmatter and its adjacent references, assets, and scripts. Resolve relative links against the actual skill directory. Keep `agents/openai.yaml` as optional Codex-facing metadata; it is not a requirement for Claude execution.

Do not assume provider-specific variables, tool names, hooks, agent-team settings, or a particular model. Do not edit the host's permissions or auto-approval configuration. Detect capabilities from the current session and use the host's documented tool interfaces.

| Available capability | Useful behavior | Missing-capability behavior |
|---|---|---|
| Source and shell | Inspect and implement in the project; run relevant checks | Produce the requested design artifact/specification; do not claim integration |
| Browser or native preview | Exercise actual UI and capture target states | Perform available source checks; label runtime verification missing |
| Image inspection | Inspect screenshots or rendered designs | Do not claim visual inspection; deliver a bounded review plan |
| Independent agents | Delegate focused analysis and review | Use honest sequential self-review |
| Image tools | Create/retrieve appropriate visual assets | Use supplied assets or a clear temporary treatment |
| Figma or another design connector | Read/write when the user requests it and the tool is available | Work in the requested available medium; report the constraint |
| Python 3 and local evidence | Run the optional report checker | Use the same evidence distinctions in a concise manual table |

No row is a reason to invent a tool result or refuse all useful work. An image-generation result is an artwork proposal, not an observed screenshot of implemented behavior. A rendered static prototype is not proof of backend integration.

## Local skill discovery

When moving the complete folder to a local coding host, the official documentation checked on 2026-11-16 specifies:

| Host | Project scope | Personal scope | Explicit invocation |
|---|---|---|---|
| Codex CLI/IDE | `.agents/skills/formsemble/SKILL.md` | `~/.agents/skills/formsemble/SKILL.md` | `$formsemble` |
| Claude Code | `.claude/skills/formsemble/SKILL.md` | `~/.claude/skills/formsemble/SKILL.md` | `/formsemble` |

Copy the whole folder, not just its entry file. ChatGPT-managed installation and Claude account/cloud installation are separate mechanisms; saving the skill in one service does not establish installation in the other. Local folders do not imply availability in every cloud or Cowork session. Recheck current host documentation if installation behavior differs.

Do not hardcode subagent counts or assume agent-team features are enabled. Ordinary available delegation is sufficient. Avoid parallel writers to the same file and parallel controllers of the same UI surface.

## Sources for host details

- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/skills)
- [Claude Code: Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code: Agent teams](https://code.claude.com/docs/en/agent-teams)

These sources establish host behavior, not the effectiveness or originality of Formsemble's design method.
