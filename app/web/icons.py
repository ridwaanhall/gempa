"""Inline SVG icon set (24x24 viewBox, stroke-based). Mirrors `static/js/lib/icons.js`.

Use `{{ icon("arrow-right") }}` in templates. Never use text glyphs
(arrows, multiplication signs, plus/minus characters) as icons: they render
inconsistently across fonts.
"""

from markupsafe import Markup

PATHS: dict[str, str] = {
    "arrow-right": "M5 12h14M13 6l6 6-6 6",
    "arrow-left": "M19 12H5M11 6l-6 6 6 6",
    "chevron-down": "m6 9 6 6 6-6",
    "close": "M6 6l12 12M18 6 6 18",
    "plus": "M12 5v14M5 12h14",
    "minus": "M5 12h14",
    "layers": "m12 3 9 5-9 5-9-5 9-5ZM3 13l9 5 9-5",
    "check": "m5 12 5 5 9-10",
    "search": "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Zm9 2-3.5-3.5",
    "wave": "M2 16c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2M2 20c2 0 2-2 4-2s2 2 4 2 2-2 "
    "4-2 2 2 4 2 2-2 4-2M6 11c0-3.5 3-6 6.5-6 1.5 0 3 .5 4 1.5",
    "pulse": "M2 12h4l2-6 4 12 3-9 2 3h5",
    "code": "m8 7-5 5 5 5M16 7l5 5-5 5",
    "moon": "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z",
    "sun": "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 "
    "1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4m11.4-11.4 1.4-1.4",
}


def icon(name: str, cls: str = "icon") -> Markup:
    return Markup(
        f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
        f'focusable="false"><path d="{PATHS[name]}"/></svg>'
    )
