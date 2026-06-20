#!/usr/bin/env python3
"""Build Warmth architecture reference HTML + PDF with full-width SVG diagrams."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

DOCS = Path(__file__).parent
CONFLUENCE = DOCS / "confluence" / "warmth-architecture-complete.html"
HTML_OUT = DOCS / "Warmth-Architecture-Reference.html"
PDF_OUT = DOCS / "Warmth-Architecture-Reference.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PRINT_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Warmth — Architecture Reference</title>
<style>
@page { size: A4; margin: 14mm 12mm 16mm 12mm; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.45; color: #1a1a1a; max-width: 100%;
}
h1 { font-size: 22pt; color: #c0392b; margin: 0 0 6pt; page-break-after: avoid; }
h2 { font-size: 14pt; color: #2c3e50; margin: 20pt 0 8pt; border-bottom: 1px solid #e0e0e0; padding-bottom: 4pt; page-break-after: avoid; }
h3 { font-size: 11pt; color: #34495e; margin: 12pt 0 6pt; page-break-after: avoid; }
p, li { margin: 0 0 6pt; }
ul, ol { margin: 0 0 10pt 18pt; padding: 0; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 14pt; font-size: 9.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #d5d5d5; padding: 5pt 7pt; text-align: left; vertical-align: top; }
th { background: #f5f5f5; font-weight: 600; }
code { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 8.5pt; background: #f4f4f4; padding: 1pt 3pt; border-radius: 2pt; }
pre { background: #f8f8f8; border: 1px solid #e8e8e8; border-radius: 4pt; padding: 8pt 10pt; overflow-x: auto; font-size: 7.5pt; line-height: 1.35; white-space: pre; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 14pt 0; }
a { color: #c0392b; text-decoration: none; }
[data-type^="panel"] { border-left: 4pt solid #3498db; background: #eef6fc; padding: 8pt 12pt; margin: 10pt 0; border-radius: 0 4pt 4pt 0; }
[data-type="panel-success"] { border-color: #27ae60; background: #eefaf3; }
[data-type="panel-warning"] { border-color: #f39c12; background: #fef9ee; }
[data-type="panel-note"] { border-color: #8e44ad; background: #f6eef9; }
.status-done { color: #27ae60; font-weight: 600; }
.status-progress { color: #f39c12; font-weight: 600; }
.status-todo { color: #7f8c8d; font-weight: 600; }
figure.diagram { margin: 10pt 0 16pt; page-break-inside: avoid; width: 100%; }
figure.diagram .svg-diagram { width: 100%; border: 1px solid #ddd; border-radius: 4pt; background: #fff; overflow: hidden; }
figure.diagram .svg-diagram svg { width: 100% !important; height: auto !important; max-width: 100% !important; display: block; }
figure.diagram.tall .svg-diagram { display: flex; justify-content: center; align-items: center; }
figure.diagram.tall .svg-diagram svg {
  width: auto !important;
  max-width: 100% !important;
  max-height: 240pt !important;
  height: auto !important;
  margin: 0 auto;
}
figure.diagram.compact .svg-diagram svg { max-height: 200pt !important; width: auto !important; max-width: 100% !important; margin: 0 auto; }
figure.diagram figcaption { font-size: 9.5pt; color: #555; margin-top: 6pt; font-style: italic; text-align: center; }
</style>
</head>
<body>
"""

PRINT_TAIL = """
<p><em>Generated from the gtmhackathon repository · branch cursor/warmth-ios-enhancements</em></p>
</body></html>
"""

DIAGRAM_INSERTS: list[tuple[str, str, str, str]] = [
    (
        '<h2 id="system">3. System architecture</h2>',
        "system-architecture",
        "Figure 1 — System architecture",
        "Client layer, FastAPI routers, lifecycle pipelines, ML integrations, and data store",
    ),
    (
        '<h2 id="lifecycle">4. Warmth lifecycle</h2>',
        "warmth-lifecycle",
        "Figure 2 — Warmth lifecycle",
        "Four lifecycle stages and their primary integrations",
    ),
    (
        "<h3>Routing decision (core product logic)</h3>",
        "ml-routing",
        "Figure 3 — ML routing decision",
        "Warmth uplift drives CRM outreach vs founder community routing",
    ),
    (
        "<h3>App shell</h3>",
        "ios-app-shell",
        "Figure 4 — iOS app shell",
        "SwiftUI navigation shell and AppModel service wiring",
    ),
    (
        "<h3>Capture sequence</h3>",
        "ios-capture-flow",
        "Figure 5 — iOS capture sequence",
        "End-to-end capture flow from wake phrase to backend signal POST",
    ),
    (
        "<h3>Signal ingest flow (<code>apps/lifecycle/signal_ingest.py</code>)</h3>",
        "backend-signal-ingest",
        "Figure 6 — Backend signal ingest",
        "iOS signal ingress through idempotency, ML routing, and Gmail draft handoff",
    ),
    (
        '<h2 id="web">7. Web dashboard architecture</h2>',
        "web-dashboard-flow",
        "Figure 7 — Web dashboard routes",
        "React Router pages and their FastAPI data dependencies",
    ),
    (
        '<h2 id="integrations">9. External integrations</h2>',
        "integration-map",
        "Figure 8 — Integration map",
        "Third-party services and which lifecycle stages consume them",
    ),
    (
        '<h2 id="journey">12. End-to-end user journey</h2>',
        "user-journey",
        "Figure 9 — User journey",
        "From pre-event prep through floor capture to desk follow-up",
    ),
]

SVG_DIR = DOCS / "diagrams" / "svg"

# Diagrams that should never stretch to full page width (portrait or dense).
COMPACT_DIAGRAMS = frozenset({"ml-routing", "backend-signal-ingest", "web-dashboard-flow"})


def svg_dimensions(name: str) -> tuple[float, float]:
    text = (SVG_DIR / f"{name}.svg").read_text(encoding="utf-8")
    vb = re.search(r'viewBox="\s*[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)\s*"', text)
    if vb:
        return float(vb.group(1)), float(vb.group(2))
    w = re.search(r'\bwidth="([\d.]+)"', text)
    h = re.search(r'\bheight="([\d.]+)"', text)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    return 800.0, 600.0


def diagram_size_class(name: str) -> str:
    if name in COMPACT_DIAGRAMS:
        return "compact"
    width, height = svg_dimensions(name)
    if height / max(width, 1) > 1.25:
        return "tall"
    return ""


def inline_svg(name: str) -> str:
    path = SVG_DIR / f"{name}.svg"
    return path.read_text(encoding="utf-8")


def figure_html(name: str, title: str, caption: str) -> str:
    svg = inline_svg(name)
    size_class = diagram_size_class(name)
    cls = f"diagram {size_class}".strip()
    return (
        f'<figure class="{cls}"><div class="svg-diagram">{svg}</div>'
        f"<figcaption><strong>{title}</strong> — {caption}</figcaption></figure>\n\n"
    )


ACTOR_SEQUENCE_AFTER = (
    '<h2 id="journey">12. End-to-end user journey</h2>\n\n'
    + figure_html("user-journey", "Figure 9 — User journey", "User journey swimlanes")
    + figure_html(
        "actor-sequence",
        "Figure 10 — Cross-system sequence",
        "Capture → ML routing → CRM / Gmail / community → web review",
    )
)


def build_html() -> str:
    body = CONFLUENCE.read_text(encoding="utf-8")

    # Insert actor sequence + user journey as a pair at journey section
    body = body.replace(
        '<h2 id="journey">12. End-to-end user journey</h2>',
        ACTOR_SEQUENCE_AFTER,
        1,
    )

    for anchor, name, title, caption in DIAGRAM_INSERTS:
        if anchor.startswith('<h2 id="journey">'):
            continue  # handled above
        fig = figure_html(name, title, caption)
        if anchor in body:
            body = body.replace(anchor, anchor + "\n\n" + fig, 1)

    toc_extra = '<li><a href="#diagrams">Visual diagrams index</a></li>\n'
    diagram_index = """
<h2 id="diagrams">Visual diagrams</h2>
<p>Ten full-width Mermaid diagrams (sources in <code>docs/diagrams/*.mmd</code>): system architecture, lifecycle, ML routing, iOS shell &amp; capture, backend ingest, web routes, integrations, user journey, actor sequence.</p>
"""
    body = body.replace("<li><a href=\"#overview\">", toc_extra + "<li><a href=\"#overview\">", 1)
    body = body.replace("<hr/>\n\n<h2 id=\"overview\">", "<hr/>\n\n" + diagram_index + "\n<hr/>\n\n<h2 id=\"overview\">", 1)

    return PRINT_HEAD + body + PRINT_TAIL


def build_pdf(html_path: Path, pdf_path: Path) -> None:
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    if not pdf_path.exists():
        raise RuntimeError("PDF was not created")


def verify_diagrams() -> list[str]:
    issues: list[str] = []
    svg_dir = DOCS / "diagrams" / "svg"
    for svg in sorted(svg_dir.glob("*.svg")):
        text = svg.read_text(encoding="utf-8")
        vb = re.search(r'viewBox="\s*[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)\s*"', text)
        if not vb:
            issues.append(f"{svg.name}: missing viewBox")
            continue
        w, h = float(vb.group(1)), float(vb.group(2))
        if w < 500:
            issues.append(f"{svg.name}: width {w:.0f}px too narrow")
    return issues


def verify_pdf_preview() -> Path:
    """Screenshot lifecycle section from built HTML at A4 content width."""
    preview = DOCS / "diagrams" / "verify-lifecycle-preview.png"
    snippet_path = DOCS / "diagrams" / "verify-preview.html"
    lifecycle_fig = figure_html(
        "warmth-lifecycle",
        "Figure 2 — Warmth lifecycle",
        "Four lifecycle stages and their primary integrations",
    )
    snippet_path.write_text(
        f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><style>
        body {{ margin:0; padding:24px; width:794px; background:#fff; font-family: Arial, sans-serif; }}
        h2 {{ font-size: 18pt; margin-bottom: 12px; }}
        figure.diagram .svg-diagram svg {{ width: 100% !important; height: auto !important; display: block; }}
        </style></head><body>
        <h2>4. Warmth lifecycle</h2>
        {lifecycle_fig}
        </body></html>""",
        encoding="utf-8",
    )
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--window-size=842,700",
        "--force-device-scale-factor=2",
        "--virtual-time-budget=5000",
        f"--screenshot={preview}",
        snippet_path.as_uri(),
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return preview


def main() -> int:
    issues = verify_diagrams()
    if issues:
        for issue in issues:
            print(f"VERIFY FAIL: {issue}", file=sys.stderr)
        return 1

    html = build_html()
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {HTML_OUT}")

    build_pdf(HTML_OUT, PDF_OUT)
    size_kb = PDF_OUT.stat().st_size // 1024
    print(f"Wrote {PDF_OUT} ({size_kb} KB)")

    preview = verify_pdf_preview()
    if preview.exists() and preview.stat().st_size > 50000:
        print(f"Preview OK: {preview} ({preview.stat().st_size} bytes)")
    else:
        print("Preview screenshot may be too small", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
