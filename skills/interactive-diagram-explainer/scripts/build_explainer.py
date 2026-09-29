#!/usr/bin/env python3
"""Validate an explainer model and render a dependency-free HTML artifact."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import uuid


ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
LANGUAGE_PATTERN = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
UI_KEYS = (
    "previous", "next", "step", "diagramLabel", "detailsLabel", "source", "caveat"
)


class ModelError(ValueError):
    """An actionable problem with the model or template."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ModelError(message)


def require_text(value: object, location: str, *, nonempty: bool = True) -> None:
    require(isinstance(value, str), f"{location} must be a string")
    if nonempty:
        require(bool(value.strip()), f"{location} must not be empty")


def validate_source(value: object, location: str) -> None:
    require(isinstance(value, dict), f"{location} must be an object")
    require_text(value.get("label"), f"{location}.label")
    if "url" not in value:
        return
    url = value["url"]
    require_text(url, f"{location}.url")
    require(not any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url),
            f"{location}.url must not contain whitespace or control characters")
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
        parsed.port  # Reject malformed or out-of-range ports.
    except ValueError as exc:
        raise ModelError(f"{location}.url is not a valid HTTP(S) URL: {exc}") from exc
    require(valid, f"{location}.url must be an absolute http:// or https:// URL")


def validate_model(model: object) -> dict:
    require(isinstance(model, dict), "model must be a JSON object")
    require_text(model.get("title"), "title")
    require_text(model.get("language"), "language")
    require(bool(LANGUAGE_PATTERN.fullmatch(model["language"])),
            "language must be a language tag such as en, vi, or zh-Hant")
    require(model.get("type") in ("flow", "bars"), "type must be flow or bars")
    require(model.get("mode") in ("step", "explore"), "mode must be step or explore")
    if "subtitle" in model:
        require_text(model["subtitle"], "subtitle", nonempty=False)

    ui = model.get("ui")
    require(isinstance(ui, dict), "ui must be an object containing localized labels")
    for key in UI_KEYS:
        require_text(ui.get(key), f"ui.{key}")
    require("{current}" in ui["step"] and "{total}" in ui["step"],
            "ui.step must contain both {current} and {total}")

    items = model.get("items")
    require(isinstance(items, list) and bool(items), "items must be a nonempty list")
    ids = []
    for index, item in enumerate(items):
        location = f"items[{index}]"
        require(isinstance(item, dict), f"{location} must be an object")
        for key in ("id", "label", "kind", "explanation"):
            require_text(item.get(key), f"{location}.{key}")
        item_id = item["id"]
        require(bool(ID_PATTERN.fullmatch(item_id)),
                f"{location}.id must start with an ASCII letter and contain only letters, digits, _ or -")
        require(item_id not in ids, f"duplicate item id: {item_id}")
        ids.append(item_id)
        if "source" in item:
            validate_source(item["source"], f"{location}.source")
        if "caveat" in item:
            require_text(item["caveat"], f"{location}.caveat")
        if "unit" in item:
            require_text(item["unit"], f"{location}.unit", nonempty=False)
        if model["type"] == "bars":
            value = item.get("value")
            valid_number = isinstance(value, (int, float)) and not isinstance(value, bool)
            try:
                finite = valid_number and math.isfinite(value)
            except OverflowError:
                finite = False
            require(finite and value >= 0,
                    f"{location}.value must be a finite, nonnegative number")

    id_set = set(ids)
    if "initial" in model:
        require_text(model["initial"], "initial")
        require(model["initial"] in id_set, "initial must refer to an existing item id")

    if model["type"] == "bars":
        require(model["mode"] == "explore", "bars supports explore mode only")
    else:
        rows = model.get("rows")
        require(isinstance(rows, list) and bool(rows), "flow.rows must be a nonempty list of rows")
        row_ids = []
        for row_index, row in enumerate(rows):
            require(isinstance(row, list) and bool(row), f"rows[{row_index}] must be a nonempty list")
            for item_id in row:
                require(isinstance(item_id, str) and item_id in id_set,
                        f"rows[{row_index}] contains an unknown item id: {item_id!r}")
                row_ids.append(item_id)
        require(len(row_ids) == len(ids) and set(row_ids) == id_set,
                "rows must contain every item id exactly once")

        edges = model.get("edges")
        require(isinstance(edges, list), "flow.edges must be a list (it may be empty)")
        edge_pairs = set()
        for edge_index, edge in enumerate(edges):
            location = f"edges[{edge_index}]"
            require(isinstance(edge, dict), f"{location} must be an object")
            for key in ("from", "to"):
                require(isinstance(edge.get(key), str) and edge[key] in id_set,
                        f"{location}.{key} must refer to an existing item id")
            if "label" in edge:
                require_text(edge["label"], f"{location}.label")
            edge_pairs.add((edge["from"], edge["to"]))

        if model["mode"] == "step":
            order = model.get("order")
            require(isinstance(order, list) and all(isinstance(item_id, str) for item_id in order),
                    "step mode requires order as a list of item ids")
            require(len(order) == len(ids) and set(order) == id_set,
                    "order must contain every item id exactly once")
            for previous, following in zip(order, order[1:]):
                require((previous, following) in edge_pairs,
                        f"step order has no directed edge from {previous!r} to {following!r}; use explore mode for unordered relationships")
    return model


def safe_json(model: dict) -> str:
    """Keep model text from terminating or changing its HTML script container."""
    encoded = json.dumps(model, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    for character, escaped in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                               ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        encoded = encoded.replace(character, escaped)
    return encoded


def render(model: dict, template: str, output_format: str) -> str:
    require("__ROOT_ID__" in template, "template is missing __ROOT_ID__")
    require(template.count("__MODEL_JSON__") == 1,
            "template must contain __MODEL_JSON__ exactly once")
    root_id = f"explainer-{uuid.uuid4().hex}"
    fragment = template.replace("__ROOT_ID__", root_id).replace("__MODEL_JSON__", safe_json(model))
    if output_format == "fragment":
        return fragment
    language = html.escape(model["language"], quote=True)
    title = html.escape(model["title"], quote=True)
    return (f'<!doctype html>\n<html lang="{language}">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title>\n'
            '<style>:root{color-scheme:light dark}body{margin:0;padding:clamp(12px,3vw,32px);font-family:system-ui,sans-serif;'
            'background:light-dark(#ffffff,#16181c);color:light-dark(#20242b,#f0f2f5)}*{box-sizing:border-box}</style>\n'
            f'</head>\n<body>\n{fragment}\n</body>\n</html>\n')


def reject_constant(value: str) -> None:
    raise ModelError(f"JSON must not contain {value}; use finite numbers")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_json", type=Path, help="UTF-8 JSON model")
    parser.add_argument("output_html", type=Path, help="HTML file to create")
    parser.add_argument("--format", choices=("standalone", "fragment"), default="standalone",
                        help="standalone page (default) or inline fragment")
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    args = parser.parse_args(argv)
    try:
        model = json.loads(args.model_json.read_text(encoding="utf-8"), parse_constant=reject_constant)
        validate_model(model)
        template_path = Path(__file__).resolve().parent.parent / "assets" / "explainer.html"
        template = template_path.read_text(encoding="utf-8")
        result = render(model, template, args.format)
        args.output_html.parent.mkdir(parents=True, exist_ok=True)
        with args.output_html.open("w" if args.force else "x", encoding="utf-8") as output:
            output.write(result)
    except FileExistsError:
        parser.exit(1, f"error: output already exists: {args.output_html}; use --force to replace it\n")
    except (ModelError, OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(args.output_html.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
