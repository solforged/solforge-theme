# Solforge themes

Dark and light Omarchy themes after [solforged.io](https://solforged.io): an
oxblood desk, a sheet of dark paper or vellum, clockwork gilt, and rubric red.
The backgrounds are construction drawings after Leonardo's notebooks, drawn as
wireframes on the site's sheet-on-desk layout.

| Theme | Directory |
| --- | --- |
| Solforge Dark | `omarchy-solforge-dark-theme/` |
| Solforge Light | `omarchy-solforge-light-theme/` |

## Palette

Both palettes start from the site's CSS tokens and extend them into a full
terminal palette in pigment colors: sanguine, ochre, verdigris, lapis, madder
and sepia. Body text clears 4.5:1 against the background and every ANSI color
clears 4:1. `generate.py` prints the contrast table on each run.

| Token | Dark | Light | Used for |
| --- | --- | --- | --- |
| desk | `#290401` | `#290401` | Wallpaper frame |
| sheet | `#130807` | `#f6f1e6` | `background` |
| ink | `#ece1ce` | `#2a2120` | `foreground` |
| gilt | `#dfb15a` | `#765411` | `accent`, `yellow`, active border |
| rubric | `#de8a70` | `#863f3d` | `bright_red`, active border |

## Backgrounds

Each background is a notebook page: one main figure, smaller studies in the
margins, Italian labels on leaders, and mirrored notes. `drawings.py` draws
them; the 3D figures use a small orthographic camera, so the wheels, solids and
rooms are true wireframes rather than flat outlines.

| File | Main figure | Margin studies |
| --- | --- | --- |
| `00-fucina.png` | A star forge on the sun's axis: four vanes round a core sphere, a crown wheel and an escape wheel, and a coiled nozzle driving a solar lance into the pole of a half-built sun | The forge in plan, one vane in elevation |
| `01-specchio.png` | A burning mirror on a worm-driven mount, gathering sunlight into a crucible over a brick forge | Parabola construction, anvil and hammer, gnomon, the sun's course over Florence |
| `02-orologio.png` | A weight-driven clock train between two plates, with anchor escapement and pendulum | Meshing teeth enlarged, lantern pinion, verge and foliot |
| `03-vacui.png` | The hollow rhombicuboctahedron from Pacioli's *De divina proportione* | Six hollow solids on rails, the golden spiral, the cube unfolded |
| `04-oculus.png` | The eye in section, a candle's rays inverting on the retina | Camera obscura, the visual pyramid, the iris as an escape wheel |

The mirrored notes are Leonardo's own lines, written right to left as he wrote
them.

## Regenerate

`colors.toml`, `icons.theme`, `chromium.theme`, the backgrounds, `preview.png`,
the omp themes in `omp/` and the Hermes skin in `hermes/` are all generated.
Edit `generate.py` (palettes), `drawings.py` (backgrounds) or `mask.py` (the
Hermes banner art), then run:

```sh
./generate.py
```

It needs `rsvg-convert`, ImageMagick and the Berkeley Mono font.

## Install locally

```sh
ln -s ~/src/solforge-theme/omarchy-solforge-dark-theme ~/.config/omarchy/themes/solforge-dark
ln -s ~/src/solforge-theme/omarchy-solforge-light-theme ~/.config/omarchy/themes/solforge-light
omarchy theme set solforge-dark
```

Omarchy renders the terminal, Hyprland, Neovim and shell configs from
`colors.toml`, so the themes ship no Lua or terminal files and install the same
way from a Git clone.

## omp and Tern

`omp/solforge-dark.json` and `omp/solforge-light.json` are oh-my-pi themes
with a `terminal` section. Tern reads that section for its panes and window
chrome, and draws the dark theme's tab bar in the oxblood desk color.

```sh
ln -s ~/src/solforge-theme/omp/solforge-dark.json ~/.omp/agent/themes/
ln -s ~/src/solforge-theme/omp/solforge-light.json ~/.omp/agent/themes/
```

Select them in omp's settings as the dark and light themes (`theme.dark`,
`theme.light`). Tern follows omp's choice unless its own `theme_dark` or
`theme_light` is set, and picks the slot from the system appearance, which the
Omarchy theme sets.

## Hermes

`hermes/tunon.yaml` is a Hermes Agent skin for Tunon the Adjudicator from
*Tyranny*. Its banner art is the Face of Judgment in its hood over Kyros'
sigil, drawn in braille at the caduceus's size (28 columns by 15 rows), with a
`TUNON` logo above it. `mask.py` draws the art on a 56x60 dot grid.

```sh
ln -s ~/src/solforge-theme/hermes/tunon.yaml ~/.hermes/skins/
hermes config set display.skin tunon
```

`colors` holds the dark palette and `light_colors` the light one. Neither
sets `background`, so the TUI keeps the terminal's own background and picks
the block that matches the terminal's polarity. The banner art takes a single
fixed color per row, so it uses mid tones from the light palette, which clear
3:1 on both backgrounds; the mask's rows have no color and draw in the
terminal's foreground. The classic CLI and the desktop app read only `colors`,
so they stay dark.
