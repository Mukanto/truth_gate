"""``truth-gate badge CERT``: a shields.io endpoint JSON for a certificate (spec 0.6, section 9).

The message is the verdict, with `` (unguarded)`` appended when the study note ``K6_EXTERNAL_UNGUARDED`` is present.
Colours: ``brightgreen`` for FALSIFIABLE, ``green`` for FALSIFIABLE (unguarded), ``yellow`` for WEAK, ``red`` otherwise.
"""

from __future__ import annotations

from .certificate import body_sha256

LABEL = "truth gate"
NOTE_UNGUARDED = "K6_EXTERNAL_UNGUARDED"
UNGUARDED_SUFFIX = " (unguarded)"


class BadgeError(Exception):
    """The certificate cannot be turned into a badge.  ``code`` is the CLI exit code: 4 (refused), 5 (hash mismatch)."""

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


def has_unguarded_note(body: dict) -> bool:
    for note in body.get("study_notes") or []:
        if isinstance(note, dict) and note.get("note") == NOTE_UNGUARDED:
            return True
    return False


def badge_payload(stored) -> dict:
    """The endpoint JSON of a certificate envelope.  Raises :class:`BadgeError` (code 5: the hash does not match the
    body; code 4: not a certificate, or a quick-mode certificate, which is not certifiable)."""
    if not isinstance(stored, dict) or not isinstance(stored.get("body"), dict) or not isinstance(
            stored.get("body_sha256"), str):
        raise BadgeError("not a certificate", 4)
    body = stored["body"]
    try:
        recomputed = body_sha256(body)
    except (TypeError, ValueError):
        raise BadgeError("not a certificate (the body cannot be canonicalised)", 4) from None
    if recomputed != stored["body_sha256"]:
        raise BadgeError("MISMATCH: the certificate body does not match its own body_sha256", 5)
    if body.get("mode") != "full":
        raise BadgeError("refusing to make a badge from a quick-mode certificate (quick mode is not certifiable)", 4)
    verdict = body.get("verdict")
    if not isinstance(verdict, str) or not verdict:
        raise BadgeError("not a certificate (no verdict)", 4)
    unguarded = has_unguarded_note(body)
    if verdict == "FALSIFIABLE":
        color = "green" if unguarded else "brightgreen"
    elif verdict == "WEAK":
        color = "yellow"
    else:
        color = "red"
    return {
        "schemaVersion": 1,
        "label": LABEL,
        "message": verdict + (UNGUARDED_SUFFIX if unguarded else ""),
        "color": color,
    }
