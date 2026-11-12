"""A tiny YAML reader for the tests (PyYAML is not a dependency).

It reads the subset that ``action.yml``, ``.pre-commit-hooks.yaml`` and the workflow template use: block mappings,
block sequences (items that are scalars or mappings), plain, single-quoted and double-quoted scalars, ``true``/``false``,
integers, ``null``, flow sequences of scalars (``[a, b]``), ``|`` and ``|-`` block scalars, and comments.  Anything else
(anchors, tags, flow mappings, multi-document files, tabs) raises :class:`YamlError`, so a file that leaves the subset
fails the test that parses it instead of being misread.
"""

import json
import re


class YamlError(ValueError):
    pass


def _strip_comment(text):
    quote = None
    for pos, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            if pos == 0 or text[pos - 1] in " [,:{":
                quote = ch
        elif ch == "#" and (pos == 0 or text[pos - 1] == " "):
            return text[:pos].rstrip()
    return text.rstrip()


def _split_key(text):
    """``(key, rest)`` for a ``key: value`` line, or ``None`` when the text is not a mapping entry."""
    if text[:1] in "\"'":
        quote = text[0]
        end = 1
        while end < len(text):
            if text[end] == quote and not (quote == "'" and text[end + 1:end + 2] == "'"):
                break
            end += 2 if (quote == "'" and text[end:end + 2] == "''") else 1
        else:
            return None
        key_text, tail = text[:end + 1], text[end + 1:]
        if not tail.startswith(":") or (len(tail) > 1 and tail[1] != " "):
            return None
        return _scalar(key_text), tail[1:].strip()
    match = re.match(r"^([^\s:\[\]{}#&*!|>'\"%@`,][^:]*?):(?: +(.*))?$", text)
    if not match:
        return None
    return match.group(1).strip(), (match.group(2) or "").strip()


def _scalar(text):
    text = text.strip()
    if text == "":
        return None
    if text[0] == '"':
        try:
            return json.loads(text)
        except ValueError:
            raise YamlError(f"bad double-quoted scalar: {text}") from None
    if text[0] == "'":
        if len(text) < 2 or text[-1] != "'":
            raise YamlError(f"bad single-quoted scalar: {text}")
        return text[1:-1].replace("''", "'")
    if text[0] == "[":
        if text[-1] != "]":
            raise YamlError(f"bad flow sequence: {text}")
        inner, items, depth, quote, start = text[1:-1], [], 0, None, 0
        for pos, ch in enumerate(inner + ","):
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
            elif ch in "[{":
                raise YamlError("nested flow collections are outside the subset")
            elif ch == "," and pos >= start:
                part = inner[start:pos].strip()
                if part:
                    items.append(_scalar(part))
                start = pos + 1
        return items
    if text[0] in "{&*!|>%@`":
        raise YamlError(f"outside the subset: {text}")
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if text in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


class _Reader:
    def __init__(self, text):
        if "\t" in text:
            raise YamlError("tabs are not allowed")
        if re.search(r"(?m)^---\s*$", text.lstrip("\ufeff").split("\n", 1)[-1]):
            raise YamlError("multi-document files are outside the subset")
        self.lines = text.lstrip("\ufeff").replace("\r\n", "\n").split("\n")
        self.i = 0

    def peek(self):
        while self.i < len(self.lines):
            raw = self.lines[self.i]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#") or stripped == "---":
                self.i += 1
                continue
            return len(raw) - len(raw.lstrip(" ")), _strip_comment(raw.strip())
        return None

    def block(self, indent):
        nxt = self.peek()
        if nxt is None:
            return None
        return self.seq(indent) if nxt[1].startswith("-") and (nxt[1] == "-" or nxt[1][1] == " ") else self.mapping(indent)

    def mapping(self, indent):
        out = {}
        while True:
            nxt = self.peek()
            if nxt is None or nxt[0] < indent:
                return out
            ind, text = nxt
            if ind > indent:
                raise YamlError(f"unexpected indentation at line {self.i + 1}: {text}")
            if text.startswith("- "):
                return out
            split = _split_key(text)
            if split is None:
                raise YamlError(f"not a mapping entry at line {self.i + 1}: {text}")
            key, rest = split
            if key in out:
                raise YamlError(f"duplicate key {key!r} at line {self.i + 1}")
            self.i += 1
            out[key] = self.value(rest, indent)

    def value(self, rest, indent):
        if rest in ("|", "|-", "|+"):
            return self.block_scalar(rest, indent)
        if rest:
            return _scalar(rest)
        nxt = self.peek()
        if nxt is None:
            return None
        ind, text = nxt
        if ind > indent:
            return self.block(ind)
        if ind == indent and text.startswith("- "):
            return self.seq(indent)
        return None

    def block_scalar(self, style, indent):
        body = []
        base = None
        while self.i < len(self.lines):
            raw = self.lines[self.i]
            if raw.strip() == "":
                body.append("")
                self.i += 1
                continue
            ind = len(raw) - len(raw.lstrip(" "))
            if ind <= indent:
                break
            base = ind if base is None else min(base, ind)
            body.append(raw)
            self.i += 1
        while body and body[-1] == "":
            body.pop()
        base = base or 0
        text = "\n".join(line[base:] if line else "" for line in body)
        return text if style == "|-" else text + "\n"

    def seq(self, indent):
        out = []
        while True:
            nxt = self.peek()
            if nxt is None or nxt[0] != indent or not (nxt[1] == "-" or nxt[1].startswith("- ")):
                return out
            ind, text = nxt
            rest = text[1:].lstrip(" ")
            offset = len(text) - len(rest)
            if not rest:
                self.i += 1
                inner = self.peek()
                out.append(self.block(inner[0]) if inner and inner[0] > indent else None)
            elif _split_key(rest) is not None and rest[:1] not in "\"'[":
                self.lines[self.i] = " " * (indent + offset) + rest  # the item is a mapping that starts on the dash line
                out.append(self.mapping(indent + offset))
            else:
                self.i += 1
                out.append(_scalar(rest))


def load(text):
    reader = _Reader(text)
    result = reader.block(0) if reader.peek() is not None else None
    if reader.peek() is not None:
        raise YamlError(f"trailing content at line {reader.i + 1}")
    return result
