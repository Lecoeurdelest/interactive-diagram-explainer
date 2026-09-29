"""Behavioral checks for model validation and generated HTML artifacts."""

from __future__ import annotations

import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
BUILDER = REPOSITORY / "skills" / "interactive-diagram-explainer" / "scripts" / "build_explainer.py"
FLOW_FIXTURE = REPOSITORY / "examples" / "queue-vi.json"
BARS_FIXTURE = REPOSITORY / "examples" / "regions-en.json"


class GeneratedHTML(HTMLParser):
    """Read the public embedded-model contract without executing scripts."""

    def __init__(self, document: str):
        super().__init__()
        self.tags = []
        self.declarations = []
        self.models = []
        self._model_parts = None
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "script" and dict(attrs).get("type") == "application/json":
            self._model_parts = []

    def handle_data(self, data):
        if self._model_parts is not None:
            self._model_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._model_parts is not None:
            self.models.append(json.loads("".join(self._model_parts)))
            self._model_parts = None

    def handle_decl(self, declaration):
        self.declarations.append(declaration)


class BuilderTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="explainer-builder-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def build(self, model_path: Path, output: Path, *options: str):
        return subprocess.run(
            [sys.executable, str(BUILDER), str(model_path), str(output), *options],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_model(self, model: dict) -> Path:
        path = self.directory / "model.json"
        path.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
        return path

    def load_fixture(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def assert_rejected(self, model: dict):
        output = self.directory / "rejected.html"
        result = self.build(self.write_model(model), output)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())
        self.assertFalse(output.exists(), "An invalid model must not produce output")

    def test_both_example_fixtures_build_as_standalone_pages(self):
        for fixture in (FLOW_FIXTURE, BARS_FIXTURE):
            with self.subTest(fixture=fixture.name):
                output = self.directory / f"{fixture.stem}.html"
                result = self.build(fixture, output)
                self.assertEqual(result.returncode, 0, result.stderr)
                document = output.read_text(encoding="utf-8")
                self.assertNotIn("__ROOT_ID__", document)
                self.assertNotIn("__MODEL_JSON__", document)
                parsed = GeneratedHTML(document)
                self.assertIn("html", parsed.tags)
                self.assertIn("body", parsed.tags)
                self.assertEqual(parsed.models, [self.load_fixture(fixture)])

    def test_existing_output_requires_force(self):
        output = self.directory / "existing.html"
        original = "Existing work must remain intact."
        output.write_text(original, encoding="utf-8")

        result = self.build(FLOW_FIXTURE, output)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding="utf-8"), original)

        result = self.build(FLOW_FIXTURE, output, "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = GeneratedHTML(output.read_text(encoding="utf-8"))
        self.assertEqual(parsed.models, [self.load_fixture(FLOW_FIXTURE)])

    def test_explanation_cannot_escape_its_embedded_model(self):
        baseline_output = self.directory / "baseline.html"
        result = self.build(FLOW_FIXTURE, baseline_output)
        self.assertEqual(result.returncode, 0, result.stderr)
        baseline = GeneratedHTML(baseline_output.read_text(encoding="utf-8"))

        model = self.load_fixture(FLOW_FIXTURE)
        model["items"][0]["explanation"] = '</script><script>alert("example")</script><p>& \u2028\u2029'
        output = self.directory / "escaped.html"
        result = self.build(self.write_model(model), output)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = GeneratedHTML(output.read_text(encoding="utf-8"))
        self.assertEqual(parsed.models, [model], "The explanation must round-trip as model text")
        self.assertEqual(parsed.tags, baseline.tags, "Model text must not introduce HTML elements")

    def test_fragment_has_no_standalone_wrapper(self):
        output = self.directory / "fragment.html"
        result = self.build(FLOW_FIXTURE, output, "--format", "fragment")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = output.read_text(encoding="utf-8")
        parsed = GeneratedHTML(document)
        self.assertTrue(parsed.tags)
        self.assertFalse({"html", "head", "body"}.intersection(parsed.tags))
        self.assertFalse(parsed.declarations)
        self.assertEqual(parsed.models, [self.load_fixture(FLOW_FIXTURE)])
        self.assertNotIn("__ROOT_ID__", document)
        self.assertNotIn("__MODEL_JSON__", document)

    def test_invalid_flow_relationships_are_rejected(self):
        fixture = self.load_fixture(FLOW_FIXTURE)
        dangling = copy.deepcopy(fixture)
        dangling["edges"][0]["to"] = "missing"
        fake_order = copy.deepcopy(fixture)
        fake_order["order"] = list(reversed(fake_order["order"]))
        duplicate = copy.deepcopy(fixture)
        duplicate["items"][1]["id"] = duplicate["items"][0]["id"]
        for name, model in (("dangling edge", dangling), ("fake step order", fake_order), ("duplicate ID", duplicate)):
            with self.subTest(case=name):
                self.assert_rejected(model)

    def test_nonfinite_and_negative_bar_values_are_rejected(self):
        fixture = self.load_fixture(BARS_FIXTURE)
        for value in (float("inf"), float("-inf"), float("nan"), -1):
            with self.subTest(value=value):
                model = copy.deepcopy(fixture)
                model["items"][0]["value"] = value
                self.assert_rejected(model)

    def test_unsafe_source_urls_are_rejected(self):
        fixture = self.load_fixture(FLOW_FIXTURE)
        for url in ("javascript:alert(1)", "data:text/html,example", "file:///tmp/example", "//example.com/page"):
            with self.subTest(url=url):
                model = copy.deepcopy(fixture)
                model["items"][0]["source"] = {"label": "Example", "url": url}
                self.assert_rejected(model)


if __name__ == "__main__":
    unittest.main()
