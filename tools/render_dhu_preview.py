#!/usr/bin/env python3
"""Render the checked-in DHU profiles on the reference WHD panel."""

import argparse
import configparser
from pathlib import Path

if __package__:
    from .projection_reference import PROFILES, PANEL, Layout, Profile
else:
    from projection_reference import PROFILES, PANEL, Layout, Profile

PANEL_WIDTH, PANEL_HEIGHT = PANEL
LABELS = {
    "central-720p": "Centrale 720p",
    "whd-1080p": "WHD 1080p",
    "wide-720p": "Panoramico 720p",
    "wide-480p": "Panoramico 480p",
}

PAGE = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Confronto dei profili Android Auto</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font: 16px/1.55 system-ui, sans-serif; background: #101721; color: #eaf2f9; }
  main { max-width: 1160px; margin: 0 auto; padding: 32px 20px 48px; }
  h1 { font-size: clamp(1.65rem, 4vw, 2.6rem); line-height: 1.13; margin: 0 0 10px; }
  h2 { font-size: 1.15rem; line-height: 1.25; margin: 0; }
  p { margin: 8px 0 0; color: #bfcddd; }
  .profiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 290px), 1fr));
              gap: 16px; margin-top: 24px; }
  article { background: #182432; padding: 16px; border-radius: 12px; }
  .panel { position: relative; margin: 16px 0;
           background: #090e14; outline: 1px solid #6b8298; }
  .picture { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
             display: grid; place-items: center; background: #145163;
             outline: 1px solid #75d9e8; outline-offset: -1px; }
  .picture::before, .picture::after { content: ""; position: absolute; inset: 5%; pointer-events: none;
    background: radial-gradient(circle, #9ae9f4 45%, transparent 51%) top left / 10px 10px no-repeat,
                radial-gradient(circle, #9ae9f4 45%, transparent 51%) top right / 10px 10px no-repeat; }
  .picture::after { transform: rotate(180deg); }
  .coverage { color: #dbf8fc; font-weight: 700; font-variant-numeric: tabular-nums; }
  dl { margin: 0; }
  dt { color: #aebed0; font-size: .85rem; }
  dd { margin: 0 0 5px; font-variant-numeric: tabular-nums; }
</style>
</head>
<body>
<main>
<h1>Android Auto sul pannello panoramico</h1>
<p>Anteprima geometrica su tela WHD di riferimento 1920 × 720. Le sagome rappresentano l’area utile dei profili.</p>
<div class="profiles">
@@CARDS@@
</div>
</main>
</body>
</html>
"""


def render_profile(name, label):
    profile = Profile.from_ini(PROFILES / f"{name}.ini")
    layout = Layout.fit(profile)
    width, height = profile.frame
    visible_width, visible_height = profile.source.width, profile.source.height
    scale = float(layout.scale)
    panel_width, panel_height = layout.destination.width, layout.destination.height
    coverage = 100 * panel_width / PANEL_WIDTH
    coverage_label = f"{coverage:.1f}".removesuffix(".0").replace(".", ",")
    scale_label = f"{scale:g}".replace(".", ",")
    return f"""
<article id="{name}">
  <h2>{label}</h2>
  <figure class="panel" style="aspect-ratio: {PANEL_WIDTH} / {PANEL_HEIGHT}" aria-label="Area utile sul pannello">
    <div class="picture" style="width: {coverage:.9f}%; height: {100 * panel_height / PANEL_HEIGHT:.9f}%">
      <span class="coverage">{coverage_label}%</span>
    </div>
  </figure>
  <dl>
    <dt>Fotogramma video</dt><dd>{width} × {height}</dd>
    <dt>Area utile prima della scala</dt><dd>{visible_width} × {visible_height}</dd>
    <dt>Area sul pannello</dt><dd>{panel_width:g} × {panel_height:g}</dd>
    <dt>Scala uniforme</dt><dd>×{scale_label}</dd>
  </dl>
</article>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Percorso del file HTML da generare")
    args = parser.parse_args()
    try:
        cards = "".join(render_profile(name, label) for name, label in LABELS.items())
        args.output.write_text(PAGE.replace("@@CARDS@@", cards), encoding="utf-8")
    except (OSError, ValueError, KeyError, configparser.Error) as error:
        parser.exit(1, f"{error}\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
