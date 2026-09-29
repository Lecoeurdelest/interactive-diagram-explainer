# Starter model and builder

Read this when using the bundled HTML starter. It renders flows and bar comparisons. For another diagram type, adapt a **copy** of the visual renderer while preserving selection, meaningful feedback, keyboard access, reduced motion, and the explanation panel beneath the diagram. The starter's two types do not limit the skill's output formats.

## Build

```bash
python3 scripts/build_explainer.py model.json output.html
python3 scripts/build_explainer.py model.json fragment.html --format fragment
```

Run these commands from the skill folder, or use absolute paths. The builder uses only Python's standard library. The standalone output opens directly in a browser without a server or external dependencies. The fragment is for an environment that supports inline HTML with scripts; use that environment's documented renderer. Use `--force` only when intentionally replacing an existing output.

The input is UTF-8 JSON. The builder rejects invalid models before writing output and prints actionable errors to stderr with a nonzero exit code. It escapes model data for embedding in HTML and assigns a unique root ID so fragments can coexist. Keep user-provided labels and descriptions rendered with `textContent` when adapting the template.

## Common fields

| Field | Requirement |
|---|---|
| `title` | Nonempty display string. |
| `subtitle` | Optional string describing scope or evidence. |
| `language` | Language tag such as `en`, `vi`, or `zh-Hant`. |
| `type` | `flow` or `bars` for this starter. |
| `mode` | `step` for a verified ordered flow; `explore` for direct selection. |
| `items` | Nonempty list of objects described below. |
| `initial` | Optional selected item ID; defaults to the first item in `order` for step mode, otherwise the first item. |
| `ui` | Localized strings: `previous`, `next`, `step`, `diagramLabel`, `detailsLabel`, `source`, `caveat`. All required and nonempty; `step` contains both `{current}` and `{total}`. |

Each item requires `id`, `label`, `kind`, and `explanation` as nonempty strings. IDs must be unique, start with an ASCII letter, and contain only ASCII letters, digits, `_`, and `-`. The `kind` is a visible category, such as “Worker”, “Function”, or “Metric”; choose categories that resolve likely ambiguity.

Optional item fields:

- `source`: `{ "label": "Readable evidence reference", "url": "https://…" }`. Omit `url` for a source that cannot be linked; URLs must be absolute HTTP(S). Use a real reference, not an invented citation. A source label can preserve a local file path and line number without turning it into an unsupported URL.
- `caveat`: A nonempty explanation of a relevant assumption, uncertainty, or discrepancy.
- `unit`: A string for a bar's measurement, such as `%` or `ms`.
- `value`: Required for every item in a bar chart; a finite, nonnegative number. Zero is valid. For negative values or a different chart, adapt the renderer and its validation to the data.

Translate all displayed prose and `ui` labels into the output language. Preserve exact code identifiers and product names. `language` describes the content; it does not translate it automatically.

## Flow fields

- `rows`: A nonempty list of nonempty lists of item IDs. Every item appears exactly once. Rows set the spatial layout; they do not by themselves assert execution order.
- `edges`: A list of `{ "from": "item-id", "to": "item-id", "label": "Optional relationship" }`. Endpoints must exist. The list may be empty.
- `order`: Required in `step` mode and contains every item ID exactly once. Every adjacent pair must have a directed edge in `edges`. Use `explore` for branching graphs, cycles, or relationships without a justified walkthrough covering all items; do not invent a sequence to satisfy the builder.

## Ordered flow example

This illustrates a queue handoff, not a claim about any particular system. Descriptions deliberately separate the queued message from the process that executes it.

```json
{
  "title": "One queued job",
  "subtitle": "Illustrative handoff; not a live system trace",
  "language": "en",
  "type": "flow",
  "mode": "step",
  "ui": {
    "previous": "Previous",
    "next": "Next",
    "step": "{current} / {total}",
    "diagramLabel": "Job handoff diagram",
    "detailsLabel": "Selected step explanation",
    "source": "Source",
    "caveat": "Note"
  },
  "items": [
    {"id": "producer", "label": "Submit work", "kind": "Producer", "explanation": "The producer sends a message describing the work and its input."},
    {"id": "queue", "label": "Wait for delivery", "kind": "Queue", "explanation": "The queue holds the message until a consumer can receive it."},
    {"id": "worker", "label": "Execute the task", "kind": "Worker", "explanation": "A worker receives the message and calls the task function with its input."}
  ],
  "rows": [["producer"], ["queue"], ["worker"]],
  "edges": [
    {"from": "producer", "to": "queue", "label": "publish"},
    {"from": "queue", "to": "worker", "label": "deliver"}
  ],
  "order": ["producer", "queue", "worker"]
}
```

## Bar comparison

Set `type` to `bars` and `mode` to `explore`, supply `value` on every item, and omit `rows`, `edges`, and `order`. Keep the common fields and localized `ui` strings. For example, these items could compare two measured durations when the supplied evidence supports them:

```json
[
  {"id": "before", "label": "Before", "kind": "Duration", "value": 120, "unit": "ms", "explanation": "The measured operation took 120 ms before the change."},
  {"id": "after", "label": "After", "kind": "Duration", "value": 80, "unit": "ms", "explanation": "The measured operation took 80 ms after the change."}
]
```

For generated or illustrative data, state that scope in the subtitle or explanations. Selection explains the chosen value; animation must not imply that historical measurements are live or causally connected.
