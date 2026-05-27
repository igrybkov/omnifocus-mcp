"""Markdown ↔ OmniFocus rich-text note conversion (write side).

Notes in this MCP server use Markdown as their single representation. This module
parses Markdown into a flat "runs" intermediate representation (IR) that the
``set_note_text.js`` OmniJS script turns into OmniFocus-native rich text. The
inverse direction (rich text → Markdown, on read) lives in OmniJS at
``scripts/common/markdown_serializer.js`` because query tools emit their JSON
entirely inside OmniFocus.

The two directions are independent inverse implementations; round-trip parity is
guaranteed by the tests in ``tests/test_markdown_notes.py``.

Runs IR shape (JSON-serializable)::

    {"blocks": [
        {"kind": "paragraph" | "heading" | "list_item",
         "headingLevel": 1,                  # heading only (1..6)
         "listKind": "bullet" | "number",    # list_item only
         "listLevel": 0,                     # list_item only (nesting depth)
         "listIndex": 1,                     # numbered list_item only
         "runs": [
             {"text": "x", "bold": False, "italic": False, "code": False, "link": None}
         ]}
    ]}

Mapping to OmniFocus style attributes (applied by set_note_text.js):
    bold   -> FontWeight = 9        italic -> FontItalic = true
    code   -> FontFamily = "Menlo"  link   -> Link = URL.fromString(href)
    heading level N -> FontSize per the scale in markdown_serializer.js
"""

import json

from markdown_it import MarkdownIt

from .mcp_tools.response import omnijs_json_response

_md = MarkdownIt("commonmark")


def _parse_inline(children: list) -> list[dict]:
    """Convert an inline token's children into a list of style runs."""
    runs: list[dict] = []
    bold = 0
    italic = 0
    link: str | None = None

    def emit(text: str, code: bool = False) -> None:
        if text == "":
            return
        runs.append(
            {
                "text": text,
                "bold": bold > 0,
                "italic": italic > 0,
                "code": code,
                "link": link,
            }
        )

    for child in children or []:
        ctype = child.type
        if ctype == "strong_open":
            bold += 1
        elif ctype == "strong_close":
            bold = max(0, bold - 1)
        elif ctype == "em_open":
            italic += 1
        elif ctype == "em_close":
            italic = max(0, italic - 1)
        elif ctype == "link_open":
            link = child.attrGet("href") or ""
        elif ctype == "link_close":
            link = None
        elif ctype == "code_inline":
            emit(child.content, code=True)
        elif ctype == "text":
            emit(child.content)
        elif ctype in ("softbreak", "hardbreak"):
            emit("\n")
        elif ctype == "image":
            # No image support in OF notes; keep the alt text so nothing is lost.
            emit(child.content)
        # html_inline and other tokens are intentionally ignored.

    return runs


def markdown_to_runs(text: str) -> list[dict]:
    """Parse Markdown into the blocks/runs IR consumed by set_note_text.js."""
    if not text:
        return []

    tokens = _md.parse(text)
    blocks: list[dict] = []

    heading_level: int | None = None
    list_kind_stack: list[str] = []  # 'bullet' | 'number'
    ordinal_stack: list[int | None] = []  # current ordinal per ordered list

    for tok in tokens:
        ttype = tok.type
        if ttype == "heading_open":
            heading_level = int(tok.tag[1:])
        elif ttype == "heading_close":
            heading_level = None
        elif ttype == "bullet_list_open":
            list_kind_stack.append("bullet")
            ordinal_stack.append(None)
        elif ttype == "ordered_list_open":
            start = tok.attrGet("start")
            ordinal_stack.append(int(start) if start is not None else 1)
            list_kind_stack.append("number")
        elif ttype in ("bullet_list_close", "ordered_list_close"):
            if list_kind_stack:
                list_kind_stack.pop()
                ordinal_stack.pop()
        elif ttype == "list_item_close":
            if ordinal_stack and ordinal_stack[-1] is not None:
                ordinal_stack[-1] += 1
        elif ttype == "inline":
            runs = _parse_inline(tok.children)
            if not runs:
                runs = [{"text": "", "bold": False, "italic": False, "code": False, "link": None}]
            if heading_level is not None:
                blocks.append({"kind": "heading", "headingLevel": heading_level, "runs": runs})
            elif list_kind_stack:
                block = {
                    "kind": "list_item",
                    "listKind": list_kind_stack[-1],
                    "listLevel": len(list_kind_stack) - 1,
                    "runs": runs,
                }
                if list_kind_stack[-1] == "number":
                    block["listIndex"] = ordinal_stack[-1] or 1
                blocks.append(block)
            else:
                blocks.append({"kind": "paragraph", "runs": runs})
        elif ttype in ("fence", "code_block"):
            # Multi-line code: one code-styled paragraph line per source line.
            content = tok.content.rstrip("\n")
            for line in content.split("\n"):
                blocks.append(
                    {
                        "kind": "paragraph",
                        "runs": [
                            {
                                "text": line,
                                "bold": False,
                                "italic": False,
                                "code": True,
                                "link": None,
                            }
                        ],
                    }
                )

    return blocks


def _first_failure(result: dict) -> str | None:
    """Return the first error message from a set_note_text result, if any."""
    if result.get("error"):
        return result["error"]
    for item in result.get("results", []):
        if not item.get("success", False):
            return item.get("error", "Unknown error setting note")
    return None


async def apply_note(item_id: str, markdown_text: str) -> tuple[bool, str]:
    """Set a single item's note from Markdown via set_note_text.js.

    Args:
        item_id: Task or project id (primaryKey). set_note_text.js resolves either.
        markdown_text: The note content as Markdown.

    Returns:
        Tuple of (success, message).
    """
    params = {"item_id": item_id, "blocks": markdown_to_runs(markdown_text)}
    result = json.loads(await omnijs_json_response("set_note_text", params))
    err = _first_failure(result)
    if err:
        return False, err
    return True, "Note set"


async def apply_notes(items: list[dict]) -> tuple[bool, dict]:
    """Set notes for multiple items in a single OmniJS round-trip.

    Args:
        items: List of {"item_id": str, "markdown": str}.

    Returns:
        Tuple of (all_succeeded, raw result dict with per-item ``results``).
    """
    payload = [
        {"item_id": item["item_id"], "blocks": markdown_to_runs(item.get("markdown", ""))}
        for item in items
    ]
    result = json.loads(await omnijs_json_response("set_note_text", {"items": payload}))
    err = _first_failure(result)
    return (err is None), result
