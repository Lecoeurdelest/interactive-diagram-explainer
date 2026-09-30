# Interactive Diagram Explainer

A reusable English-language skill for creating diagrams people can explore. Clicking an item or advancing a real sequence updates both the visual and an explanation panel underneath. Short animation shows the change; the selected state remains visible afterward.

Diagram labels and explanations follow the user's requested language, or the language of their request. Technical identifiers stay intact.

## What it covers

- Processes, architecture, sequences, timelines, trees, relationships, data, and simulations.
- Interaction chosen for the content: steps for ordered processes, selection for data or networks, expansion for hierarchies.
- A persistent panel showing the selected item's kind, title, explanation, and optional source or uncertainty.
- Keyboard operation, reduced motion, responsive layout, light and dark themes.
- A dependency-free HTML starter for flows and bars, with guidance for adapting other visual forms.

The starter is a small implementation aid, not a universal chart library. The skill's behavior contract applies to other renderers as well.

## Install

Installation and use require prior written permission from the applicable copyright holder. The instructions below are for authorized users; they do not grant a license. See [LICENSE](LICENSE).

The skill is a standard `SKILL.md` folder plus a dependency-free Python builder, so it works with any agent that can read files and run a command.

| Platform | Install |
|---|---|
| Claude Code | `python3 skills/interactive-diagram-explainer/scripts/install.py claude` (installs to `~/.claude/skills`) |
| Codex | `python3 skills/interactive-diagram-explainer/scripts/install.py codex` (uses `CODEX_HOME` when set) |
| Other agents that read `.agents/skills` | `python3 skills/interactive-diagram-explainer/scripts/install.py agents` |
| Agents that read `AGENTS.md` (Grok Build, Cursor, Aider, OpenCode, and others) | Work inside this repository; [AGENTS.md](AGENTS.md) points to the skill. |
| DeepSeek, Grok, Gemini, or any chat model | Use [adapters/generic-prompt.md](adapters/generic-prompt.md) as the system prompt, then run the builder on the JSON it returns. |

Use `all` to install for every skill directory, `--project DIR` to install under `DIR/.<platform>/skills`, `--dest DIR` for a custom skills directory, and `--force` to replace an existing copy. Inspect an existing skill before replacing it.

Invoke it with `/interactive-diagram-explainer` (Claude Code), `$interactive-diagram-explainer` (Codex), or by asking for an explanatory interactive diagram. Automatic discovery remains enabled. `agents/openai.yaml` is optional Codex UI metadata; other platforms ignore it.

## Examples

The fixtures contain fictional teaching data and no private project code.

- [Vietnamese queue walkthrough](examples/queue-vi.html) — Previous/Next and direct node selection.
- [English regional chart](examples/regions-en.html) — choose a bar to inspect its value and explanation.
- [English order review](examples/order-review-en.html) — explore two alternative branches; generated from a Vietnamese request that explicitly asked for English output.

To build or adapt them:

```sh
python3 skills/interactive-diagram-explainer/scripts/build_explainer.py \
  examples/queue-vi.json output.html
```

Add `--format fragment` for an inline visualization surface. Read the [data model](skills/interactive-diagram-explainer/references/data-model.md) for the schema and supported starter layouts. Neither rendering mode loads external scripts or makes network requests.

## Contents

```text
skills/interactive-diagram-explainer/
  SKILL.md
  agents/openai.yaml
  assets/explainer.html
  references/interaction-patterns.md
  references/data-model.md
  scripts/build_explainer.py
  scripts/install.py
adapters/generic-prompt.md
AGENTS.md
CLAUDE.md
examples/
tests/
```

Run the Python builder tests with `python3 -m unittest discover -s tests`. Browser verification uses Playwright; run `node tests/browser.cjs` after making its package and Chromium available to Node. To use an installed Chrome instead, set `EXPLAINER_BROWSER_CHANNEL=chrome`. Tests check selection/explanation synchronization, meaningful step order, language content, rapid interaction, keyboard use, narrow screens, reduced motion, and standalone rendering.

## Author

Lecoeurdelest

## License and copyright

Copyright (c) 2026 Lecoeurdelest. **All rights reserved.**

This repository is proprietary. No permission is granted to use, copy, modify, create derivative works from, distribute, or commercially or noncommercially exploit its original material without prior written permission from the applicable copyright holder, subject to the exceptions in [LICENSE](LICENSE).

Contact [Lecoeurdelest](https://github.com/Lecoeurdelest) to request permission. Attribution alone does not authorize reuse.
