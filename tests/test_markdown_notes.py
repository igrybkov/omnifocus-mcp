"""Tests for Markdown -> rich-text note conversion (write side).

The rich-text -> Markdown direction lives in OmniJS (markdown_serializer.js) and is
verified end-to-end against real OmniFocus; here we test the Python parser and the
OmniJS-applier helpers. The escaping round-trip is exercised from the parser side:
escaped Markdown must parse back to literal, unstyled text.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from omnifocus_mcp.markdown_notes import apply_note, apply_notes, markdown_to_runs


def _only_run(md: str) -> dict:
    """Return the single run of a single-block parse result."""
    blocks = markdown_to_runs(md)
    assert len(blocks) == 1, blocks
    assert len(blocks[0]["runs"]) == 1, blocks[0]["runs"]
    return blocks[0]["runs"][0]


class TestMarkdownToRuns:
    def test_empty_string(self):
        assert markdown_to_runs("") == []

    def test_plain_paragraph(self):
        blocks = markdown_to_runs("just text")
        assert blocks == [
            {
                "kind": "paragraph",
                "runs": [
                    {
                        "text": "just text",
                        "bold": False,
                        "italic": False,
                        "code": False,
                        "link": None,
                    }
                ],
            }
        ]

    def test_bold(self):
        run = _only_run("**bold**")
        assert run["bold"] is True and run["italic"] is False and run["text"] == "bold"

    def test_italic(self):
        run = _only_run("*ital*")
        assert run["italic"] is True and run["bold"] is False and run["text"] == "ital"

    def test_bold_italic(self):
        run = _only_run("***both***")
        assert run["bold"] is True and run["italic"] is True and run["text"] == "both"

    def test_inline_code(self):
        run = _only_run("`code`")
        assert run["code"] is True and run["text"] == "code"

    def test_link(self):
        run = _only_run("[label](https://example.com)")
        assert run["link"] == "https://example.com" and run["text"] == "label"

    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5, 6])
    def test_heading_levels(self, level):
        blocks = markdown_to_runs("#" * level + " Heading")
        assert blocks[0]["kind"] == "heading"
        assert blocks[0]["headingLevel"] == level
        assert blocks[0]["runs"][0]["text"] == "Heading"

    def test_bullet_list(self):
        blocks = markdown_to_runs("- one\n- two")
        assert [b["kind"] for b in blocks] == ["list_item", "list_item"]
        assert all(b["listKind"] == "bullet" for b in blocks)
        assert [b["runs"][0]["text"] for b in blocks] == ["one", "two"]

    def test_numbered_list_indices(self):
        blocks = markdown_to_runs("1. first\n2. second\n3. third")
        assert [b["listKind"] for b in blocks] == ["number"] * 3
        assert [b["listIndex"] for b in blocks] == [1, 2, 3]

    def test_numbered_list_custom_start(self):
        blocks = markdown_to_runs("5. five\n6. six")
        assert [b["listIndex"] for b in blocks] == [5, 6]

    def test_nested_list_levels(self):
        blocks = markdown_to_runs("- top\n    - nested")
        levels = [b["listLevel"] for b in blocks]
        assert levels == [0, 1]

    def test_code_fence_becomes_code_runs(self):
        blocks = markdown_to_runs("```\nline1\nline2\n```")
        assert len(blocks) == 2
        assert all(b["runs"][0]["code"] is True for b in blocks)
        assert [b["runs"][0]["text"] for b in blocks] == ["line1", "line2"]

    def test_mixed_inline_styles(self):
        blocks = markdown_to_runs("a **b** c")
        runs = blocks[0]["runs"]
        assert [(r["text"], r["bold"]) for r in runs] == [("a ", False), ("b", True), (" c", False)]


class TestEscapingRoundTrip:
    """Escaped Markdown (as emitted by the read serializer) must parse to literal text."""

    @pytest.mark.parametrize(
        "escaped,literal",
        [
            (r"\*not bold\*", "*not bold*"),
            (r"\_not ital\_", "_not ital_"),
            (r"cost: 5\* each", "cost: 5* each"),
            (r"\[not a link\]", "[not a link]"),
            (r"a \\ backslash", "a \\ backslash"),
        ],
    )
    def test_escaped_inline_parses_literal(self, escaped, literal):
        blocks = markdown_to_runs(escaped)
        # No styling should be applied, and the literal characters preserved.
        text = "".join(r["text"] for r in blocks[0]["runs"])
        assert text == literal
        assert all(not r["bold"] and not r["italic"] and not r["code"] for r in blocks[0]["runs"])

    def test_escaped_leading_hash_is_not_heading(self):
        blocks = markdown_to_runs(r"\# not a heading")
        assert blocks[0]["kind"] == "paragraph"
        assert "".join(r["text"] for r in blocks[0]["runs"]) == "# not a heading"


class TestApplyNote:
    @pytest.mark.asyncio
    async def test_apply_note_success(self):
        with patch(
            "omnifocus_mcp.markdown_notes.omnijs_json_response",
            new=AsyncMock(
                return_value=json.dumps({"success": True, "results": [{"success": True}]})
            ),
        ) as mock_omnijs:
            ok, msg = await apply_note("task-1", "**hi**")

            assert ok is True
            script_name, params = mock_omnijs.call_args[0][:2]
            assert script_name == "set_note_text"
            assert params["item_id"] == "task-1"
            assert params["blocks"][0]["runs"][0]["bold"] is True

    @pytest.mark.asyncio
    async def test_apply_note_item_not_found(self):
        with patch(
            "omnifocus_mcp.markdown_notes.omnijs_json_response",
            new=AsyncMock(
                return_value=json.dumps(
                    {
                        "success": False,
                        "results": [{"success": False, "error": "Item not found: x"}],
                    }
                )
            ),
        ):
            ok, msg = await apply_note("x", "note")
            assert ok is False
            assert "not found" in msg.lower()

    @pytest.mark.asyncio
    async def test_apply_note_top_level_error(self):
        with patch(
            "omnifocus_mcp.markdown_notes.omnijs_json_response",
            new=AsyncMock(return_value=json.dumps({"error": "boom"})),
        ):
            ok, msg = await apply_note("x", "note")
            assert ok is False and msg == "boom"

    @pytest.mark.asyncio
    async def test_apply_notes_batch(self):
        with patch(
            "omnifocus_mcp.markdown_notes.omnijs_json_response",
            new=AsyncMock(
                return_value=json.dumps(
                    {"success": True, "results": [{"success": True}, {"success": True}]}
                )
            ),
        ) as mock_omnijs:
            ok, result = await apply_notes(
                [{"item_id": "a", "markdown": "x"}, {"item_id": "b", "markdown": "**y**"}]
            )

            assert ok is True
            params = mock_omnijs.call_args[0][1]
            assert [i["item_id"] for i in params["items"]] == ["a", "b"]
            assert params["items"][1]["blocks"][0]["runs"][0]["bold"] is True
