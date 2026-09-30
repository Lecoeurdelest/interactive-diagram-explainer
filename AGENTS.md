# Agent instructions

This repository provides the `interactive-diagram-explainer` skill.

- To create an interactive explanatory diagram, follow `skills/interactive-diagram-explainer/SKILL.md`.
- Read `skills/interactive-diagram-explainer/references/data-model.md` before writing a model.
- Build with `python3 skills/interactive-diagram-explainer/scripts/build_explainer.py model.json output.html`.
- Run tests with `python3 -m unittest discover -s tests`.
- Keep the skill host-neutral: guard any host-specific API (such as `window.openai`) so output works standalone.
