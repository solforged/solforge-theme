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

| File | Drawing |
| --- | --- |
| `01-orrery.png` | A 76-tooth wheel driving a 28 and 18 tooth train, with compass orbits |
| `02-vacuus.png` | The hollow rhombicuboctahedron Leonardo drew for Pacioli's *De divina proportione* |
| `03-oculus.png` | A section of the eye with a candle's rays inverting on the retina, and the iris as an escape wheel |

The mirrored notes are Leonardo's own lines, written right to left as he wrote
them.

## Regenerate

`colors.toml`, `icons.theme`, `chromium.theme`, the backgrounds and
`preview.png` are all generated. Edit `generate.py`, then run:

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
