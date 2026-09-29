# Interaction patterns

Use this reference when choosing a diagram or adapting the shared explanation panel to a new subject. Preserve the user's requested format when it can represent the content accurately.

## Choose the representation

| Question the viewer needs to answer | Suitable representation | Useful interaction |
| --- | --- | --- |
| What happens next, and under which condition? | Flowchart or state diagram | Select a step; Previous/Next along an explicit path; choose a branch |
| Who calls whom, and when? | Sequence diagram with participant lanes | Advance a message; highlight sender, receiver, and current call |
| Which parts connect or depend on each other? | Architecture or dependency graph | Select a component; reveal its neighbors and labeled connections |
| What changed over time? | Timeline | Select a dated event or interval; move between actual time points |
| What belongs to what? | Tree or hierarchy | Expand a branch; select a node; retain the parent context |
| Which values differ or move together? | Bar, line, scatter, or other data chart | Select a mark or series; filter a group; inspect a comparison |
| What happens when an input changes? | Simulation with controls | Change a parameter; show the resulting state and explain the calculation |

Previous/Next implies an order. Use it for a real sequence or a clearly labeled guided tour. Do not imply causality or execution order between unrelated categories, components, or data points. Use direct selection for unordered exploration.

For branching flows, name the selected path or scenario. Show the branch decision before advancing. Distinguish simultaneous branches from alternatives; do not animate parallel work as a required serial sequence.

## Shared explanation panel

Keep one stable panel below the diagram. Populate it on first render with an overview or meaningful initial selection; never leave an empty placeholder until the first click. Keep enough space for typical content so selections do not repeatedly shift the surrounding layout.

Each selected item should supply:

| Field | Purpose |
| --- | --- |
| Kind | A short, domain-specific category: function, worker, queue, metric, phase, person, event, etc. |
| Title | The selected item's readable name; preserve identifiers when needed. |
| Explanation | What happens or what the item means, followed by why it matters and its result when useful. |
| Evidence, optional | A verified source, calculation, file and line, or input dataset. |
| Qualification, optional | A specific assumption, uncertainty, failure condition, or distinction between illustration and observation. |

Render kind and title together, followed by connected prose. Do not force separate “what / why / result” labels when a short paragraph is clearer. Use an additional detail section only when it adds information needed to understand the selected item.

Selection changes the diagram and panel together. If the viewer selects a connection, explain that relationship, its direction, and any relevant condition. A source link or panel button must not accidentally advance the diagram.

## Feedback and animation

- On click or keyboard activation, immediately distinguish the selected item with a persistent outline, shape, or label as well as color.
- Use animation to explain a change: a message traveling along an edge, a branch unfolding, a timeline marker moving, or a value updating. A brief emphasis animation is enough for a static selection.
- Keep effects finite and restrained. Retain the final selection after motion ends, and let users inspect the explanation before advancing.
- Keep selection, controls, progress, and panel content synchronized. Cancel or replace an unfinished transition when a new selection arrives so an older animation cannot overwrite the latest state.
- Prefer manual advancement. If autoplay materially helps, provide pause and restart and keep manual selection available.
- Define boundary behavior: disable Previous on the first step and Next on the last, or offer an explicitly labeled restart. Never silently loop a one-way process.
- Motion is illustrative unless connected to verified live data. Label a simulation or example so moving dots do not imply that a production task is currently running.

## Technical diagrams: separate entities from actions

Use type labels, grouping, and named arrows to make these distinctions visible:

| Entity | What it represents | Explain on selection |
| --- | --- | --- |
| Runtime or worker | A running process, service, or worker pool | What it receives and which code it executes |
| Function | Code called within an execution context | Who calls it, inputs, work, and return or side effect |
| Job or task message | A request describing work to be performed | Task name, relevant payload, producer, and destination |
| Queue | Stored messages awaiting delivery | Which producers publish and which workers consume |
| Database record | Persisted state | What is written or read and why it is needed later |

Group functions inside their execution context when helpful. A function node is not a separate worker. A new task message does not imply a new machine: one worker pool may execute successive tasks. A queued job, its eventual function invocation, and its database status record are distinct objects even if their names are similar.

Label edges with concrete actions such as “calls,” “publishes,” “delivers,” “writes,” “acknowledges,” and “schedules next node.” Verify asynchronous boundaries from the implementation. Do not assume a method named `delay()` executes immediately, or that every delay uses a queue; some systems persist a timestamp for a later scanner.

Trace code and configuration before asserting routing, retries, scheduling, acknowledgments, or completion behavior. A declared route establishes intended routing; verified broker bindings or runtime evidence establish observed delivery. Put a discrepancy at the affected connection, and explain its scope in the panel. Do not present a source-level possibility as a confirmed production failure.

## Evidence and interpretation

Ground labels, values, paths, and transitions in the supplied material or inspected sources. Inspect files before citing their lines. Include source information where it helps the viewer verify a claim; do not invent citations to fill the panel.

Distinguish a measured value from a derived calculation and from a demonstration value. For calculations, disclose the relevant formula or inputs. Keep units, dates, denominators, and axes visible where their absence would change the meaning. An interaction must not conceal a scale change or transform correlation into causation.

When evidence is incomplete, show the supported portion and attach a precise qualification to the uncertain part. Keep verified behavior and proposed behavior visually distinguishable when comparing them.

## Language

Choose the output language in this order: explicit user instruction, predominant language of the current request, then the established conversation language. Apply it to titles, controls, legends, accessible labels, status messages, and panel prose. A source document's language does not override the user's requested output language.

Keep code identifiers, APIs, product names, and exact quoted values intact when translation would change their identity. Explain technical terminology in the chosen language; do not translate a real function into a fictional identifier. Format numbers and dates consistently with the chosen locale and preserve their actual meaning.

## Small screens, keyboard, and reduced motion

- Keep the panel directly below the diagram in document order. For large diagrams, use a bounded diagram viewport, overview/detail navigation, or grouping so the panel stays reachable. Avoid requiring a long scroll after every selection.
- Keep labels readable. Prefer wrapping, expanding details, or controlled pan/zoom to shrinking a full network into illegible text. Ensure controls and the panel fit a narrow screen.
- Use native buttons for selectable items when possible. Provide visible focus, meaningful accessible names, and keyboard activation with Enter/Space. Expose selected state using the appropriate accessible semantics.
- Announce updated explanation text politely without moving keyboard focus on every selection. Make tooltips supplementary; clicking or focusing must expose the substantive explanation.
- Honor `prefers-reduced-motion`: suppress travel and large transitions while preserving immediate selection and state updates. Do not encode essential information only through motion or color.
- Verify that direct selection, sequential controls when present, repeated clicks, and the initial state all show the matching explanation. Inspect at least a narrow layout and a keyboard interaction.
