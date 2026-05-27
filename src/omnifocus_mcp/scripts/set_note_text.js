// Build OmniFocus-native rich text (noteText) from a Markdown-derived runs IR.
// The inverse (rich text -> Markdown) lives in common/markdown_serializer.js.
//
// Params (one of):
//   { item_id: "<primaryKey>", blocks: [ ...blocks IR... ] }
//   { items: [ { item_id: "...", blocks: [...] }, ... ] }   // batch, single round-trip
//
// Block IR (see markdown_notes.py for the full shape):
//   { kind: "paragraph"|"heading"|"list_item",
//     headingLevel, listKind, listLevel, listIndex,
//     runs: [ { text, bold, italic, code, link } ] }
//
// Returns: { success: bool, results: [ { item_id, success, error? } ] }

try {
    // Heading font sizes by level. MUST stay in sync with the read-side
    // thresholds in common/markdown_serializer.js.
    var HEADING_SIZES = { 1: 24, 2: 21, 3: 18, 4: 16, 5: 14, 6: 13 };
    var CODE_FONT = "Menlo";
    var BOLD_WEIGHT = 9;

    function findItem(id) {
        // Task and Project ids share a namespace; try both.
        var t = Task.byIdentifier(id);
        if (t) return t;
        return Project.byIdentifier(id);
    }

    function applyRunStyle(textObj, run, fontSize) {
        var st = textObj.styleForRange(textObj.range);
        if (run.bold) st.set(Style.Attribute.FontWeight, BOLD_WEIGHT);
        if (run.italic) st.set(Style.Attribute.FontItalic, true);
        if (run.code) st.set(Style.Attribute.FontFamily, CODE_FONT);
        if (fontSize) st.set(Style.Attribute.FontSize, fontSize);
        // Links last; color attributes are never applied to link runs.
        if (run.link) {
            var url = URL.fromString(run.link);
            if (url) st.set(Style.Attribute.Link, url);
        }
    }

    function buildAndSet(item, blocks) {
        // Clear content AND reset styling to defaults. Capturing note.style from
        // an already-styled note inherits stray attributes (e.g. a prior heading's
        // FontSize), which would leak into every run on re-edit. Setting the plain
        // note to "" first resets the typing style to the document default.
        item.note = "";
        var note = item.noteText;
        var base = note.style;

        blocks = blocks || [];
        for (var bi = 0; bi < blocks.length; bi++) {
            var block = blocks[bi];

            // Separator between blocks: single newline between consecutive list
            // items, blank line otherwise. The reader reconstructs blocks from this.
            if (bi > 0) {
                var prev = blocks[bi - 1];
                var sameList = prev.kind === "list_item" && block.kind === "list_item"
                    && prev.listKind === block.listKind;
                note.append(new Text(sameList ? "\n" : "\n\n", base));
            }

            // Literal list marker prefix (OF has no native list construct here).
            if (block.kind === "list_item") {
                var indent = "";
                for (var k = 0; k < (block.listLevel || 0); k++) indent += "  ";
                var marker = (block.listKind === "number")
                    ? (indent + (block.listIndex || 1) + ". ")
                    : (indent + "- ");
                note.append(new Text(marker, base));
            }

            var fontSize = (block.kind === "heading")
                ? (HEADING_SIZES[block.headingLevel] || HEADING_SIZES[3])
                : null;

            var runs = block.runs || [];
            for (var ri = 0; ri < runs.length; ri++) {
                var run = runs[ri];
                if (!run.text) continue;
                var t = new Text(run.text, base);
                applyRunStyle(t, run, fontSize);
                note.append(t);
            }
        }
    }

    function processOne(entry) {
        try {
            if (!entry || !entry.item_id) {
                return { item_id: entry ? entry.item_id : null, success: false, error: "item_id is required" };
            }
            var item = findItem(entry.item_id);
            if (!item) {
                return { item_id: entry.item_id, success: false, error: "Item not found: " + entry.item_id };
            }
            buildAndSet(item, entry.blocks);
            return { item_id: entry.item_id, success: true };
        } catch (e) {
            return { item_id: entry ? entry.item_id : null, success: false, error: e.toString() };
        }
    }

    var entries = params.items
        ? params.items
        : [{ item_id: params.item_id, blocks: params.blocks }];

    var results = entries.map(processOne);
    var allOk = results.every(function (r) { return r.success; });
    return JSON.stringify({ success: allOk, results: results });

} catch (error) {
    return JSON.stringify({ error: "Error setting note text: " + error.toString() });
}
