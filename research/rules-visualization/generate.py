#!/usr/bin/env python3
"""Generate the isolated, static, trilingual rules-visualization prototype.

No JavaScript, no graph library, no server. The presentation model is the
single source for both views; the generator emits semantic HTML plus one
numbered SVG per locale.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = json.loads((ROOT / 'model' / 'presentation.json').read_text(encoding='utf-8'))
LANGS = ('en', 'fr', 'ar')

SCROLL_JS = r"""<script>
(() => {
  document.querySelectorAll('.graph-scroll, .table-scroll').forEach((region) => {
    region.addEventListener('keydown', (event) => {
      const amount = 60;
      const rtl = getComputedStyle(region).direction === 'rtl';
      if (event.key === 'ArrowRight') {
        region.scrollLeft += rtl ? -amount : amount;
        event.preventDefault();
      } else if (event.key === 'ArrowLeft') {
        region.scrollLeft += rtl ? amount : -amount;
        event.preventDefault();
      }
    });
  });
})();
</script>"""

CSS = r"""
:root {
  color-scheme: light;
  --ink: #17202a; --muted: #4d5966; --paper: #ffffff; --wash: #f3f6f9;
  --line: #6b7785; --accent: #0b4f8a; --accent-ink: #ffffff;
  --input: #dcecf8; --constant: #f3e8c8; --computed: #e2e8f5;
}
* { box-sizing: border-box; }
html { font-family: system-ui, -apple-system, "Segoe UI", Tahoma, "Noto Sans Arabic", sans-serif; line-height: 1.55; }
body { margin: 0; color: var(--ink); background: var(--paper); }
a { color: var(--accent); text-underline-offset: 0.18em; }
a:focus-visible, button:focus-visible, [tabindex]:focus-visible { outline: 3px solid var(--ink); outline-offset: 3px; }
.skip { position: absolute; inset-inline-start: 0.5rem; inset-block-start: -4rem; background: var(--ink); color: var(--paper); padding: 0.6rem 0.9rem; z-index: 5; }
.skip:focus { inset-block-start: 0.5rem; }
header, main, footer { max-inline-size: 68rem; margin-inline: auto; padding-inline: 1rem; }
header { padding-block: 1.2rem 0.6rem; }
.badge { display: inline-block; border: 2px solid var(--ink); border-radius: 0.4rem; padding: 0.15rem 0.45rem; font-weight: 700; font-size: 0.82rem; }
h1 { font-size: clamp(1.7rem, 4vw, 2.5rem); line-height: 1.15; margin-block: 0.6rem 0.4rem; }
h2 { font-size: clamp(1.25rem, 2.5vw, 1.6rem); margin-block: 2rem 0.6rem; border-block-end: 2px solid var(--line); padding-block-end: 0.25rem; }
h3 { font-size: 1.05rem; margin-block: 0 0.35rem; }
.node-input rect { fill: var(--input); stroke: #17202a; stroke-width: 2; }
.node-constant rect { fill: var(--constant); stroke: #17202a; stroke-width: 2; }
.node-computed rect { fill: var(--computed); stroke: #17202a; stroke-width: 2; }
.node-id { font-weight: 700; }
svg text { font-family: system-ui, -apple-system, "Segoe UI", Tahoma, "Noto Sans Arabic", sans-serif; font-size: 14px; fill: #17202a; }
.edge { fill: none; stroke: #4d5966; stroke-width: 2; }
p, li { max-inline-size: 68ch; }
.lead { font-size: 1.08rem; color: var(--muted); }
nav.langs ul { list-style: none; display: flex; flex-wrap: wrap; gap: 0.5rem; padding: 0; margin-block: 0.5rem; }
nav.langs a { display: inline-block; border: 1px solid var(--line); border-radius: 0.35rem; padding: 0.35rem 0.6rem; text-decoration: none; }
nav.langs a[aria-current="page"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
section { margin-block: 1.4rem; }
figure { margin: 1rem 0 1.5rem; }
figcaption { color: var(--muted); margin-block-start: 0.4rem; }
.graph-scroll { overflow-x: auto; border: 2px solid var(--line); border-radius: 0.5rem; background: var(--paper); }
.graph-scroll:focus-visible { outline: 3px solid var(--ink); outline-offset: 3px; }
svg { display: block; inline-size: 100%; block-size: auto; min-inline-size: 46rem; }
.legend { display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.9rem; margin-block: 0.4rem; }
.legend span::before { content: ""; display: inline-block; inline-size: 0.8rem; block-size: 0.8rem; margin-inline-end: 0.35rem; border: 2px solid var(--line); vertical-align: -0.1rem; }
.legend .li::before { background: var(--input); }
.legend .lc::before { background: var(--constant); }
.legend .lp::before { background: var(--computed); }
.table-scroll { overflow-x: auto; max-inline-size: 100%; margin-block: 0.8rem 1.2rem; }
.table-scroll:focus-visible { outline: 3px solid var(--ink); outline-offset: 3px; }
table { border-collapse: collapse; inline-size: 100%; margin-block: 0.8rem 1.2rem; }
caption { text-align: start; font-weight: 700; padding-block-end: 0.4rem; }
th, td { border: 1px solid var(--line); padding: 0.45rem 0.55rem; text-align: start; vertical-align: top; }
th { background: var(--wash); }
code, .id { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.92em; }
.foreign { unicode-bidi: isolate; }
.ladder { list-style: none; padding: 0; margin: 0; }
.ladder li { border: 2px solid var(--line); border-radius: 0.5rem; padding: 0.8rem 1rem; margin-block-end: 0.75rem; background: var(--wash); }
.ladder .step { font-weight: 800; color: var(--muted); margin: 0 0 0.2rem; }
.ladder dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 0.75rem; margin-block: 0.5rem; }
.ladder dt { font-weight: 700; }
.ladder dd { margin: 0; }
.cite { font-size: 0.92rem; color: var(--muted); }
.note { font-size: 0.92rem; }
.disclaimer { border-inline-start: 6px solid var(--ink); background: var(--wash); padding: 0.8rem 1rem; }
.integration { overflow-wrap: anywhere; }
footer { border-block-start: 2px solid var(--line); margin-block-start: 2.5rem; padding-block: 1rem 2rem; color: var(--muted); font-size: 0.92rem; }
@media (max-width: 40rem) {
  body { font-size: 1rem; }
  header, main, footer { padding-inline: 0.75rem; }
  table { font-size: 0.92rem; }
}
@media (forced-colors: active) {
  .graph-scroll, .ladder li, .disclaimer { border-color: CanvasText; }
  nav.langs a[aria-current="page"] { background: Highlight; color: HighlightText; }
}
@media print { .skip, nav.langs { display: none; } a { color: inherit; } }
"""


def clean_html(text: str) -> str:
    return re.sub(r'[ \t]+$', '', text, flags=re.M).rstrip() + '\n'


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def foreign(text: str) -> str:
    return f'<span class="foreign" lang="en" dir="ltr">{esc(text)}</span>'


def svg_graph(lang: str) -> str:
    nodes = MODEL['nodes']
    by_id = {node['id']: node for node in nodes}
    width, height = 1020, 680
    edges = []
    for target in nodes:
        for source_id in target['depends_on']:
            source = by_id[source_id]
            sx, sy = source['position'][0] + 70, source['position'][1] + 54
            tx, ty = target['position'][0] + 70, target['position'][1]
            mid = (sy + ty) / 2
            edges.append(
                f'<path class="edge" d="M {sx} {sy} C {sx} {mid}, {tx} {mid}, {tx} {ty}" '
                f'marker-end="url(#arrow)" />')
    shapes = []
    for node in nodes:
        x, y = node['position']
        cls = {'input': 'node-input', 'constant': 'node-constant',
               'computed': 'node-computed'}[node['kind']]
        direction = 'rtl' if lang == 'ar' else 'ltr'
        shapes.append(
            f'<g class="{cls}"><rect x="{x}" y="{y}" width="140" height="54" rx="9" />'
            f'<text x="{x+70}" y="{y+18}" text-anchor="middle" direction="{direction}">'
            f'<tspan class="node-id">{esc(node["id"])}</tspan></text>'
            f'<text x="{x+70}" y="{y+38}" text-anchor="middle" direction="{direction}">'
            f'{esc(node["short"][lang])}</text></g>')
    ui = MODEL['ui'][lang]
    legend = (
        f'<div class="legend" role="group" aria-label="{esc({"en":"Node kinds","fr":"Types de nœuds","ar":"أنواع العقد"}[lang])}">'
        f'<span class="li">{esc(ui["input"])}</span>'
        f'<span class="lc">{esc(ui["constant"])}</span>'
        f'<span class="lp">{esc(ui["computed"])}</span></div>')
    return f"""
    <div class="graph-scroll" tabindex="0" role="region" aria-label="{esc(ui['graph_title'])}">
      <svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="graph-title" aria-describedby="graph-desc" focusable="false" direction="ltr">
        <title id="graph-title">{esc(ui['graph_title'])}</title>
        <desc id="graph-desc">{esc(ui['graph_desc'])}</desc>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#17202a" />
          </marker>
        </defs>
        {''.join(edges)}
        {''.join(shapes)}
      </svg>
    </div>
    {legend}
    """

def node_table(lang: str) -> str:
    ui = MODEL['ui'][lang]
    rows = []
    for node in MODEL['nodes']:
        kind = {'input': ui['input'], 'constant': ui['constant'], 'computed': ui['computed']}[node['kind']]
        depends = ', '.join(node['depends_on']) if node['depends_on'] else '—'
        value = node.get('value') or node['dtype']
        rows.append(
            f'<tr><th scope="row"><code lang="en" dir="ltr">{esc(node["id"])}</code></th>'
            f'<td>{esc(node["label"][lang])}</td><td>{esc(kind)}</td><td><code lang="en" dir="ltr">{esc(node["dtype"])}</code></td>'
            f'<td><code lang="en" dir="ltr">{esc(value)}</code></td><td><code lang="en" dir="ltr">{esc(depends)}</code></td>'
            f'<td><code lang="en" dir="ltr">{esc(node["citation"])}</code></td></tr>')
    return f"""
    <div class="table-scroll" tabindex="0" role="region" aria-label="{esc(ui['graph_table_caption'])}">
    <table>
      <caption>{esc(ui['graph_table_caption'])}</caption>
      <thead><tr><th scope="col">{esc(ui['table_node'])}</th><th scope="col">{esc(ui['table_label'])}</th>
      <th scope="col">{esc(ui['table_kind'])}</th><th scope="col">Dtype</th><th scope="col">{esc(ui['table_value'])}</th>
      <th scope="col">{esc(ui['table_depends'])}</th><th scope="col">{esc(ui['table_citation'])}</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    </div>"""


def ladder(lang: str) -> str:
    ui = MODEL['ui'][lang]
    items = []
    for step in MODEL['ladder']:
        items.append(f"""
        <li>
          <p class="step">{esc(ui['step'])} {step['step']}</p>
          <h3>{esc(step['condition'][lang])}</h3>
          <dl>
            <dt>{esc(ui['if_true'])}</dt><dd>{esc(step['true'][lang])}</dd>
            <dt>{esc(ui['if_false'])}</dt><dd>{esc(step['false'][lang])}</dd>
          </dl>
          <p class="cite">{esc(ui['citation'])}: <code lang="en" dir="ltr">{esc(step['citation'])}</code>. {esc(step['note'][lang])}</p>
        </li>""")
    return f'<ol class="ladder">{"".join(items)}</ol>'


def text_equivalent(lang: str) -> str:
    ui = MODEL['ui'][lang]
    # The linear explanation is deliberately explicit about branches, unknown
    # states and citations; it does not depend on the SVG or the ladder layout.
    steps = MODEL['ladder']
    def cite(i: int) -> str:
        return f'<code lang="en" dir="ltr">{esc(steps[i]["citation"])}</code>'
    return f"""
    <ol>
      <li>{esc(ui['step'])} 1: {esc(steps[0]['condition'][lang])} {esc(ui['if_false']).lower()}: <strong>{esc(steps[0]['false'][lang])}</strong> ({cite(0)}). {esc(ui['if_true']).lower()}: {esc(steps[0]['true'][lang])}.</li>
      <li>{esc(ui['step'])} 2: {esc(steps[1]['condition'][lang])} {esc(ui['if_false']).lower()}: <strong>{esc(steps[1]['false'][lang])}</strong> ({cite(1)}). {esc(ui['if_true']).lower()}: {esc(steps[1]['true'][lang])}.</li>
      <li>{esc(ui['step'])} 3: {esc(steps[2]['condition'][lang])} {esc(ui['if_false']).lower()}: <strong>{esc(steps[2]['false'][lang])}</strong> ({cite(2)}). {esc(ui['if_true']).lower()}: {esc(steps[2]['true'][lang])}.</li>
      <li>{esc(ui['step'])} 4: {esc(steps[3]['condition'][lang])} {esc(ui['if_true']).lower()}: <strong>{esc(steps[3]['true'][lang])}</strong> ({cite(3)}). {esc(ui['if_false']).lower()}: {esc(steps[3]['false'][lang])} ({cite(3)}).</li>
      <li>{esc(ui['step'])} 5: {esc(steps[4]['condition'][lang])} {esc(ui['if_true']).lower()}: <strong>{esc(steps[4]['true'][lang])}</strong> ({cite(4)}). {esc(ui['if_false']).lower()}: <strong>{esc(steps[4]['false'][lang])}</strong>.</li>
    </ol>"""


def test_table(lang: str) -> str:
    ui = MODEL['ui'][lang]
    rows = []
    for test in MODEL['tests']:
        rows.append(
            f'<tr><th scope="row">{esc(test["label"][lang])}</th><td>{esc(test["facts"][lang])}</td>'
            f'<td>{foreign(test["axiom"])}</td><td>{foreign(test["l4"])}</td><td>{esc(test["agreement"][lang])}</td></tr>')
    return f"""
    <div class="table-scroll" tabindex="0" role="region" aria-label="{esc(ui['tests_h'])}">
    <table>
      <caption>{esc(ui['tests_h'])}</caption>
      <thead><tr><th scope="col">{esc(ui['case'])}</th><th scope="col">{esc(ui['facts'])}</th>
      <th scope="col">{esc(ui['axiom'])}</th><th scope="col">{esc(ui['l4'])}</th><th scope="col">{esc(ui['agreement'])}</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    </div>"""


def source_list(lang: str) -> str:
    items = []
    for source in MODEL['sources']:
        items.append(f'<li><code lang="en" dir="ltr">{esc(source["id"])}</code> — {esc(source["citation"][lang])}. '
                     f'<a href="{esc(source["url"])}">{esc(source["label"][lang])}</a></li>')
    return f'<ul>{"".join(items)}</ul>'


def page(lang: str) -> str:
    ui = MODEL['ui'][lang]
    nav = ''.join(
        f'<li><a lang="{code}" hreflang="{code}" href="../{code}/"'
        + (' aria-current="page"' if code == lang else '') + f'>{esc(MODEL["ui"][code]["lang_name"])}</a></li>'
        for code in LANGS)
    return f"""<!doctype html>
<html lang="{lang}" dir="{ui['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(ui['title'])}</title>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">{esc(ui['skip'])}</a>
<header>
  <p><span class="badge">{esc(ui['synthetic'])}</span></p>
  <nav class="langs" aria-label="{esc({'en':'Language','fr':'Langue','ar':'اللغة'}[lang])}"><ul>{nav}</ul></nav>
  <h1>{esc(ui['title'])}</h1>
  <p class="lead">{esc(ui['lead'])}</p>
</header>
<main id="main" tabindex="-1">
  <p class="disclaimer">{esc(ui['footer'])}</p>

  <section aria-labelledby="summary-h">
    <h2 id="summary-h">{esc(ui['summary_h'])}</h2>
    <p>{esc(ui['summary'])}</p>
  </section>

  <section aria-labelledby="graph-h">
    <h2 id="graph-h">{esc(ui['graph_h'])}</h2>
    <p>{esc(ui['graph_note'])}</p>
    <figure>
      {svg_graph(lang)}
      <figcaption>{esc(ui['graph_desc'])}</figcaption>
    </figure>
    <p class="note">{esc(ui['scroll_note'])}</p>
    {node_table(lang)}
  </section>

  <section aria-labelledby="ladder-h">
    <h2 id="ladder-h">{esc(ui['ladder_h'])}</h2>
    <p>{esc(ui['ladder_intro'])}</p>
    {ladder(lang)}
  </section>

  <section aria-labelledby="text-h">
    <h2 id="text-h">{esc(ui['text_h'])}</h2>
    <p>{esc(ui['text_intro'])}</p>
    {text_equivalent(lang)}
    <h3>{esc(ui['unknown_h'])}</h3>
    <p>{esc(ui['unknown'])}</p>
  </section>

  <section aria-labelledby="tests-h">
    <h2 id="tests-h">{esc(ui['tests_h'])}</h2>
    <p>{esc(ui['tests_intro'])}</p>
    {test_table(lang)}
  </section>

  <section aria-labelledby="sources-h">
    <h2 id="sources-h">{esc(ui['sources_h'])}</h2>
    <p>{esc(ui['sources_intro'])}</p>
    {source_list(lang)}
  </section>

  <section aria-labelledby="integration-h">
    <h2 id="integration-h">{esc(ui['integration_h'])}</h2>
    <p>{esc(ui['integration_intro'])}</p>
    <p class="integration">{esc(ui['chain'])}</p>
  </section>

  <section aria-labelledby="unsupported-h">
    <h2 id="unsupported-h">{esc({'en':'Unsupported or out of scope','fr':'Non pris en charge ou hors périmètre','ar':'غير مدعوم أو خارج النطاق'}[lang])}</h2>
    <ul>{''.join(f'<li><strong>{esc(item["label"][lang])}</strong>: {esc(item["reason"][lang])}</li>' for item in MODEL["unsupported"])}</ul>
  </section>

  <section aria-labelledby="limits-h">
    <h2 id="limits-h">{esc(ui['limits_h'])}</h2>
    <p>{esc(ui['limits'])}</p>
    <h3>{esc(ui['a11y_h'])}</h3>
    <p>{esc(ui['a11y'])}</p>
  </section>

  <p><a href="../">{esc(ui['back'])}</a> · <a href="../../README.md">{esc(ui['source_code'])}</a></p>
</main>
{SCROLL_JS}
<footer>
  <p lang="en" dir="ltr">Prototype: <code>synthetic-procurement-v1</code>. Axiom <code>{esc(MODEL['engines']['axiom']['version'])}</code>
  (<code>{esc(MODEL['engines']['axiom']['commit'][:7])}</code>), L4 <code>{esc(MODEL['engines']['l4']['version'])}</code>
  (<code>{esc(MODEL['engines']['l4']['commit'][:7])}</code>).</p>
</footer>
</body>
</html>
"""


def index() -> str:
    links = ''.join(f'<li><a lang="{lang}" hreflang="{lang}" href="{lang}/">{esc(MODEL["ui"][lang]["lang_name"])}</a></li>' for lang in LANGS)
    return f"""<!doctype html>
<html lang="en" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rules-visualization prototype</title><style>{CSS}</style></head>
<body><a class="skip" href="#main">Skip to main content</a><main id="main" tabindex="-1"><h1>Rules-visualization prototype</h1>
<p>Synthetic procurement policy; no legal effect.</p><ul>{links}</ul>
<p><a href="../README.md">Prototype documentation</a></p></main></body></html>"""


def main() -> None:
    for lang in LANGS:
        target = ROOT / 'prototype' / lang
        target.mkdir(parents=True, exist_ok=True)
        (target / 'index.html').write_text(clean_html(page(lang)), encoding='utf-8')
    (ROOT / 'prototype' / 'index.html').write_text(clean_html(index()), encoding='utf-8')
    print('generated', len(LANGS) + 1, 'pages')


if __name__ == '__main__':
    main()
