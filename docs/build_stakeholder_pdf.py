#!/usr/bin/env python3
"""Build Warmth stakeholder overview HTML + PDF (non-technical)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

DOCS = Path(__file__).parent
DIAGRAMS = DOCS / "diagrams"
SVG_DIR = DIAGRAMS / "svg"
HTML_OUT = DOCS / "Warmth-Stakeholder-Overview.html"
PDF_OUT = DOCS / "Warmth-Stakeholder-Overview.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

STAKEHOLDER_DIAGRAMS = [
    "stakeholder-touchpoints",
    "stakeholder-lifecycle",
    "stakeholder-journey",
    "stakeholder-warmth",
]

COMPACT = frozenset({"stakeholder-warmth"})

PRINT_CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 11pt; line-height: 1.55; color: #1a1a1a;
}
.cover { text-align: center; padding: 48pt 0 32pt; page-break-after: always; }
.cover h1 { font-size: 32pt; color: #c0392b; margin: 0 0 10pt; font-weight: 700; }
.cover .tagline { font-size: 14pt; color: #444; max-width: 420pt; margin: 0 auto 20pt; }
.cover .meta { font-size: 10pt; color: #888; }
h2 { font-size: 16pt; color: #2c3e50; margin: 24pt 0 10pt; border-bottom: 2px solid #c0392b; padding-bottom: 5pt; page-break-after: avoid; }
h3 { font-size: 12pt; color: #34495e; margin: 16pt 0 8pt; page-break-after: avoid; }
p { margin: 0 0 10pt; }
ul, ol { margin: 0 0 12pt 20pt; padding: 0; }
li { margin-bottom: 5pt; }
.lead { font-size: 12.5pt; color: #333; margin-bottom: 14pt; }
.callout {
  border-left: 4pt solid #c0392b; background: #fef5f3; padding: 12pt 16pt;
  margin: 14pt 0; border-radius: 0 6pt 6pt 0;
}
.callout-blue { border-color: #3498db; background: #eef6fc; }
.callout-green { border-color: #27ae60; background: #eefaf3; }
table { width: 100%; border-collapse: collapse; margin: 12pt 0 16pt; font-size: 10.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #ddd; padding: 8pt 10pt; text-align: left; vertical-align: top; }
th { background: #f7f7f7; font-weight: 600; }
figure.diagram { margin: 12pt 0 18pt; page-break-inside: avoid; }
figure.diagram .svg-diagram { border: 1px solid #e0e0e0; border-radius: 6pt; background: #fff; overflow: hidden; }
figure.diagram .svg-diagram svg { width: 100% !important; height: auto !important; max-width: 100% !important; display: block; }
figure.diagram.compact .svg-diagram svg { max-height: 220pt !important; width: auto !important; max-width: 100% !important; margin: 0 auto; display: block; }
figure.diagram.compact .svg-diagram { display: flex; justify-content: center; }
figure.diagram figcaption { font-size: 10pt; color: #666; margin-top: 8pt; text-align: center; font-style: italic; }
.pillars { display: block; margin: 16pt 0; }
.pillar { margin-bottom: 12pt; padding-left: 14pt; border-left: 3pt solid #c0392b; }
.pillar strong { color: #c0392b; }
.footer { margin-top: 28pt; padding-top: 12pt; border-top: 1px solid #e0e0e0; font-size: 9.5pt; color: #888; text-align: center; }
"""


def inline_svg(name: str) -> str:
    return (SVG_DIR / f"{name}.svg").read_text(encoding="utf-8")


def figure(name: str, caption: str) -> str:
    cls = "diagram compact" if name in COMPACT else "diagram"
    svg = inline_svg(name)
    return f'<figure class="{cls}"><div class="svg-diagram">{svg}</div><figcaption>{caption}</figcaption></figure>\n'


def build_body() -> str:
    return f"""
<div class="cover">
  <h1>Warmth</h1>
  <p class="tagline">Turn conference chaos into meaningful relationships — before, during, and after every event.</p>
  <p class="meta">Product overview for users &amp; stakeholders · June 2026</p>
</div>

<h2>The problem</h2>
<p class="lead">At a single conference you might meet dozens of people. Names blur together. Notes never get typed up. Follow-ups slip for weeks — or never happen.</p>
<p>Most tools only help <em>after</em> you're back at your desk, when half the context is already gone. Warmth is built for the full arc of conference networking: preparing while there's still time, capturing while you're still in the room, and following up while the conversation is fresh.</p>

<h2>What Warmth does</h2>
<div class="pillars">
  <div class="pillar"><strong>Prepare</strong> — See who is worth your time before you step on the floor.</div>
  <div class="pillar"><strong>Capture</strong> — Record conversations hands-free, without breaking the moment.</div>
  <div class="pillar"><strong>Route</strong> — Know who deserves a direct follow-up vs. a warm intro to someone in your network.</div>
  <div class="pillar"><strong>Follow up</strong> — Send emails that reference what you actually talked about, not generic templates.</div>
</div>

<div class="callout">
  <strong>In one sentence:</strong> Warmth is your conference copilot — a personal CRM that listens, remembers, and helps you act on every connection.
</div>

<h2>Who it's for</h2>
<ul>
  <li><strong>Founders</strong> building relationships at industry events</li>
  <li><strong>Sales &amp; GTM teams</strong> working a crowded conference floor</li>
  <li><strong>Anyone</strong> who meets too many people and loses track of who mattered most</li>
</ul>

<h2>How you experience Warmth</h2>
<p>Warmth meets you where you are — on your phone at the event, and at your desk before and after.</p>

{figure("stakeholder-touchpoints", "Your phone captures. Your dashboard helps you decide. Warmth connects the two.")}

<table>
  <thead><tr><th>Where</th><th>What you do</th><th>When</th></tr></thead>
  <tbody>
    <tr><td><strong>iPhone &amp; Apple Watch</strong></td><td>Start capture with a phrase or a tap; see who you've met today</td><td>On the conference floor</td></tr>
    <tr><td><strong>Web dashboard</strong></td><td>Review events, ranked connections, warmth scores, and follow-up drafts</td><td>Before the event and back at your desk</td></tr>
  </tbody>
</table>

<h2>The Warmth journey</h2>
<p>Every conference connection moves through four natural stages:</p>

{figure("stakeholder-lifecycle", "From setup to follow-up — Warmth supports the full lifecycle of every connection.")}

<h3>1 · Get set up</h3>
<p>Connect your calendar and email. Warmth detects upcoming conferences and gets everything ready before you travel.</p>

<h3>2 · Before the event</h3>
<p>Review a prioritized list of people worth meeting. Draft personalized outreach so you're not starting from zero on day one.</p>

<h3>3 · During the conversation</h3>
<p>When you meet someone, say <em>"hey, it's nice to meet you"</em> — or tap record on your phone or Apple Watch. Warmth captures names, companies, interests, and key moments while you stay present in the conversation.</p>

<h3>4 · After you meet</h3>
<p>Warmth prepares follow-up email drafts grounded in what you discussed. You review, tweak if needed, and send — always in your voice, always your decision.</p>

<h2>A day at the conference</h2>

{figure("stakeholder-journey", "What a typical conference day looks like with Warmth.")}

<h2>What makes Warmth different</h2>
<p>Most CRMs ask: <em>Does this person fit our ideal customer?</em> Warmth asks that too — but also: <em>How warm was the actual conversation?</em></p>

{figure("stakeholder-warmth", "Profile fit and conversational warmth work together to decide what happens next.")}

<p>A perfect-on-paper lead can still be cold in person. Someone outside your usual profile can become your most valuable introduction. Warmth captures both dimensions and compares what happened in the room to what you expected going in.</p>

<table>
  <thead><tr><th>If the meeting…</th><th>Warmth helps you…</th></tr></thead>
  <tbody>
    <tr><td><strong>Exceeded expectations</strong> — more interest than you predicted</td><td>Prioritize a direct follow-up, add them to your CRM, and draft a personalized email</td></tr>
    <tr><td><strong>Was lukewarm or better suited elsewhere</strong></td><td>Introduce them to the right person in your founder or partner network</td></tr>
  </tbody>
</table>

<div class="callout-green callout">
  <strong>The key insight:</strong> Warmth doesn't just score people — it compares before and after the conversation to surface who truly moved the needle.
</div>

<h2>Trust &amp; control</h2>
<ul>
  <li><strong>You always send the email.</strong> Warmth creates drafts; nothing goes out without your approval.</li>
  <li><strong>Capture stays private on your device</strong> until you're ready to sync — designed for sensitive conversations on a busy floor.</li>
  <li><strong>Your data, your relationships.</strong> Warmth organizes your network; it doesn't replace your judgment.</li>
</ul>

<h2>What success looks like</h2>
<ul>
  <li>Walk into every event knowing who to prioritize</li>
  <li>Never lose a name or a detail from a conversation that mattered</li>
  <li>Follow up within hours, with context — not weeks later with a generic note</li>
  <li>Spend less time on admin and more time on relationships that count</li>
</ul>

<div class="callout-blue callout">
  <strong>Warmth = conference capture + relationship scoring + intelligent routing + human-approved follow-up.</strong>
</div>

<p class="footer">Warmth · Conference Intelligence Platform · GTM Hackathon 2026</p>
"""


def build_html() -> str:
    body = build_body()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Warmth — Product Overview</title>
<style>{PRINT_CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""


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


def verify_svgs() -> list[str]:
    issues = []
    for name in STAKEHOLDER_DIAGRAMS:
        path = SVG_DIR / f"{name}.svg"
        if not path.exists():
            issues.append(f"missing {name}.svg")
            continue
        text = path.read_text(encoding="utf-8")
        vb = re.search(r'viewBox="\s*[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)\s*"', text)
        if not vb:
            issues.append(f"{name}: no viewBox")
    return issues


def main() -> int:
    issues = verify_svgs()
    if issues:
        for i in issues:
            print(f"ERR {i}", file=sys.stderr)
        print("Run: python3 docs/diagrams/render_diagrams.py", file=sys.stderr)
        return 1

    html = build_html()
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {HTML_OUT}")

    build_pdf(HTML_OUT, PDF_OUT)
    print(f"Wrote {PDF_OUT} ({PDF_OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
