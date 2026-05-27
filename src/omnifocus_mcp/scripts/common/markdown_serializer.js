// Serialize an OmniFocus item's rich-text note to Markdown (read side).
// Inverse of the write path in markdown_notes.py + set_note_text.js.
//
// Exposes: noteToMarkdown(item) -> String
//
// Notes are returned as Markdown everywhere in this server. Plain (unstyled)
// text is escaped so literal Markdown metacharacters survive a read -> write ->
// read round-trip. Bold/italic/code/links round-trip losslessly; headings
// (font size) and lists (literal markers) are best-effort.

// Heading font-size thresholds. MUST stay in sync with HEADING_SIZES in
// set_note_text.js (write uses 24/21/18/16/14/13; body is 12).
function _sizeToHeadingLevel(sz) {
    if (sz == null) return 0;
    if (sz >= 22) return 1;
    if (sz >= 19) return 2;
    if (sz >= 16.5) return 3;
    if (sz >= 14.5) return 4;
    if (sz >= 12.6) return 5;
    if (sz >= 12.1) return 6;
    return 0;
}

function _isMonospace(family) {
    return !!family && /mono|menlo|courier|consolas/i.test(family);
}

function _readFlags(style) {
    var w = style.get(Style.Attribute.FontWeight);
    var sz = style.get(Style.Attribute.FontSize);
    var fam = style.get(Style.Attribute.FontFamily);
    var lk = style.get(Style.Attribute.Link);
    return {
        // FontWeight is remapped on read (bold set to 9 reads back ~12; normal is 5).
        bold: (w != null && w >= 7),
        italic: (style.get(Style.Attribute.FontItalic) === true),
        code: _isMonospace(fam),
        size: (sz != null ? sz : 12),
        link: (lk && lk.string) ? lk.string : null
    };
}

function _styleIsDefault(style) {
    var f = _readFlags(style);
    return !f.bold && !f.italic && !f.code && !f.link && f.size <= 12;
}

// Escape inline Markdown metacharacters (backslash first). The trailing replace
// guards "<" only when it could start an autolink or HTML tag (e.g. "<https://x>",
// "<div>"), so a literal "<url>" in a plain note doesn't become a real link on
// re-write, while "a < b" is left untouched.
function _escapeInline(text) {
    return text
        .replace(/[\\`*_\[\]]/g, function (m) { return "\\" + m; })
        .replace(/<(?=[A-Za-z/])/g, "\\<");
}

// Escape a full plain-text line: inline chars + leading block triggers, while
// deliberately leaving list markers ("- "/"+ "/"N. ") so they round-trip as lists.
function _escapePlainLine(line) {
    var esc = _escapeInline(line);
    // Leading ATX heading / blockquote markers.
    esc = esc.replace(/^(\s*)([#>])/, function (_m, sp, ch) { return sp + "\\" + ch; });
    // Whole-line thematic break / setext underline (=== or ---).
    if (/^\s*=+\s*$/.test(line)) {
        esc = esc.replace(/=/, "\\=");
    } else if (/^\s*-+\s*$/.test(line)) {
        esc = esc.replace(/-/, "\\-");
    }
    return esc;
}

function _escapePlainText(text) {
    return text.split("\n").map(_escapePlainLine).join("\n");
}

// Wrap inline code, widening the backtick fence past any internal run of backticks.
function _wrapCode(text) {
    var longest = 0, cur = 0, i;
    for (i = 0; i < text.length; i++) {
        if (text[i] === "`") { cur++; if (cur > longest) longest = cur; }
        else { cur = 0; }
    }
    var fence = new Array(longest + 2).join("`");
    var pad = (longest > 0 || text.charAt(0) === "`" || text.charAt(text.length - 1) === "`") ? " " : "";
    return fence + pad + text + pad + fence;
}

function _renderStyledText(seg) {
    if (seg.code) return _wrapCode(seg.text);
    var t = _escapeInline(seg.text);
    if (seg.bold && seg.italic) return "***" + t + "***";
    if (seg.bold) return "**" + t + "**";
    if (seg.italic) return "*" + t + "*";
    return t;
}

// Render one line's segments to inline Markdown, merging adjacent same-link runs.
function _renderInline(segs) {
    var out = "";
    var i = 0;
    while (i < segs.length) {
        var link = segs[i].link;
        if (link) {
            var inner = "";
            while (i < segs.length && segs[i].link === link) {
                inner += _renderStyledText(segs[i]);
                i++;
            }
            out += "[" + inner + "](" + link + ")";
        } else {
            out += _renderStyledText(segs[i]);
            i++;
        }
    }
    return out;
}

function _renderLine(segs) {
    if (segs.length === 0) return "";
    // Heading level from the largest non-whitespace segment.
    var maxSize = 0;
    for (var i = 0; i < segs.length; i++) {
        if (segs[i].text.trim() !== "" && segs[i].size > maxSize) maxSize = segs[i].size;
    }
    var level = _sizeToHeadingLevel(maxSize);
    var inline = _renderInline(segs);
    if (level > 0) {
        return new Array(level + 1).join("#") + " " + inline;
    }
    // Paragraph/list line: escape a leading #/> that would otherwise become a block.
    return inline.replace(/^(\s*)([#>])/, function (_m, sp, ch) { return sp + "\\" + ch; });
}

function noteToMarkdown(item) {
    var plain = item.note || "";
    if (plain === "") return "";

    var nt = item.noteText;
    var runs = nt.ranges(TextComponent.AttributeRuns);

    // Cheap path: a single default-styled run is just escaped plain text.
    if (runs.length === 1 && _styleIsDefault(nt.styleForRange(runs[0]))) {
        return _escapePlainText(plain);
    }

    // Full walk: distribute styled runs across lines (a run may span newlines).
    var lines = [[]];
    for (var r = 0; r < runs.length; r++) {
        var style = nt.styleForRange(runs[r]);
        var flags = _readFlags(style);
        var text = nt.textInRange(runs[r]).string;
        var parts = text.split("\n");
        for (var j = 0; j < parts.length; j++) {
            if (j > 0) lines.push([]);
            if (parts[j] !== "") {
                lines[lines.length - 1].push({
                    text: parts[j],
                    bold: flags.bold,
                    italic: flags.italic,
                    code: flags.code,
                    link: flags.link,
                    size: flags.size
                });
            }
        }
    }

    return lines.map(_renderLine).join("\n");
}
