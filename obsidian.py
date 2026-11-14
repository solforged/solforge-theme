"""Obsidian's Solforge layout: the site's sheet-on-desk page in CSS.

`generate.py` writes the colors as one variable block per palette; the rules
here name only variables, so every hex value stays in the palettes. They
follow solforged.io: the open note is a sheet on the oxblood desk with
registration corners, chrome sits on the sheet behind hairline rules, labels
are mono, and slips carry a short rubric insertion mark.
"""

MANIFEST = {
    "name": "Solforge",
    "version": "1.0.0",
    "minAppVersion": "1.9.0",
    "author": "solforged",
    "authorUrl": "https://solforged.io",
}

# Type and shape shared by both palettes. Obsidian's font settings still win:
# its `--font-*-override` variables come before the theme's in each stack.
TYPE = {
    "--font-interface-theme": '"IBM Plex Sans", "Helvetica Neue"',
    "--font-text-theme": '"IBM Plex Serif", Georgia, serif',
    "--font-monospace-theme": '"Berkeley Mono", "IBM Plex Mono"',
    "--solforge-desk-width": "20px",
    "--file-line-width": "680px",
    "--line-height-normal": "1.53",
    "--code-size": ".86em",
    "--h1-size": "1.76em", "--h2-size": "1.353em", "--h3-size": "1.118em",
    "--h4-size": "1em", "--h5-size": "1em", "--h6-size": ".8em",
    "--h1-weight": "400", "--h2-weight": "500", "--h3-weight": "500",
    "--h4-weight": "500", "--h5-weight": "500", "--h6-weight": "400",
    "--h1-line-height": "1.1", "--h2-line-height": "1.22", "--h3-line-height": "1.35",
    "--h5-style": "italic", "--h6-font": "var(--font-monospace)",
    "--inline-title-size": "2.3em", "--inline-title-weight": "400",
    "--inline-title-line-height": "1.05", "--inline-title-margin-bottom": ".6em",
    "--blockquote-border-thickness": "1px", "--hr-thickness": "1px",
    "--file-header-font": "var(--font-monospace)", "--metadata-label-font": "var(--font-monospace)",
    "--titlebar-text-weight": "400", "--nav-heading-weight": "400",
    # Square corners, as on the site's sheets, slips and letter boxes.
    "--radius-s": "0", "--radius-m": "0", "--radius-l": "0", "--radius-xl": "0",
    "--input-radius": "0", "--search-input-radius": "0", "--tag-radius": "0", "--pill-radius": "0", "--hotkey-radius": "0",
    "--image-radius": "0", "--swatch-radius": "0", "--status-bar-radius": "0",
    "--tab-curve": "0", "--tab-radius-active": "0",
    "--tag-padding-x": ".45em", "--tag-padding-y": ".1em", "--tag-border-width": "1px",
}

RULES = r"""
/* The open note is a sheet on the desk: an oxblood strip frames each root
   leaf, so split panes read as sheets side by side. Sidebars stay off it. */
.workspace-split.mod-root .workspace-leaf-content {
  border-inline: var(--solforge-desk-width) solid var(--solforge-desk);
}
.workspace-split.mod-root .workspace-leaf-content[data-type="markdown"]::before,
.workspace-split.mod-root .workspace-leaf-content[data-type="markdown"]::after {
  content: "";
  position: absolute;
  z-index: 2;
  width: 11px;
  height: 11px;
  border: 0 solid var(--solforge-line);
  pointer-events: none;
}
.workspace-split.mod-root .workspace-leaf-content[data-type="markdown"]::before {
  top: calc(var(--header-height) + 12px);
  left: 14px;
  border-width: 1px 0 0 1px;
}
.workspace-split.mod-root .workspace-leaf-content[data-type="markdown"]::after {
  /* Above the status bar, which floats over the bottom-right corner. */
  bottom: 40px;
  right: 14px;
  border-width: 0 1px 1px 0;
}
.is-mobile .workspace-split.mod-root .workspace-leaf-content { border-inline: 0; }
.is-mobile .workspace-leaf-content[data-type="markdown"]::before,
.is-mobile .workspace-leaf-content[data-type="markdown"]::after { display: none; }

/* Chrome sits on the sheet behind hairlines. The open tab takes the site's
   gilt underline instead of a raised tab. */
.workspace-tab-header-container { border-bottom: 1px solid var(--divider-color); }
.workspace-tab-header.is-active { outline: none; box-shadow: none; }
.workspace-tab-header::before, .workspace-tab-header::after { display: none; }
.mod-root .workspace-tab-header.is-active .workspace-tab-header-inner {
  box-shadow: inset 0 -2px 0 var(--interactive-accent);
}
.mod-root .workspace-tab-header-inner-title { font-family: var(--font-monospace); font-size: var(--font-ui-smaller); }

/* Breadcrumbs as the site's rubric eyebrow: mono parents, ink title. */
.view-header-title-container { font-family: var(--font-monospace); font-size: var(--font-ui-smaller); }
.view-header-breadcrumb, .view-header-title-parent { color: var(--solforge-rubric); }
.view-header-breadcrumb-separator { color: var(--text-faint); }
.view-header-title { color: var(--text-normal); }

.status-bar {
  font-family: var(--font-monospace);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  border-width: 1px 0 0 1px;
}

/* The file tree: folders as mono group labels, the open note marked by a
   gilt rule on its left edge, guides in hairline. */
.nav-folder-title-content {
  font-family: var(--font-monospace);
  font-size: 11.5px;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.tree-item-self.is-active { box-shadow: inset 2px 0 0 var(--interactive-accent); }
.tree-item-self.has-focus { box-shadow: 0 0 0 1px var(--background-modifier-border-focus); }
.tree-item-self.is-active.has-focus {
  box-shadow: inset 2px 0 0 var(--interactive-accent), 0 0 0 1px var(--background-modifier-border-focus);
}
.workspace-sidedock-vault-profile { font-family: var(--font-monospace); }

/* The properties heading is an eyebrow, as above the site's titles. */
.metadata-properties-heading .metadata-properties-title {
  font-family: var(--font-monospace);
  font-size: 11px;
  font-weight: 400;
  color: var(--text-muted);
  letter-spacing: .04em;
}

/* Headings and prose. */
.markdown-rendered h1, .markdown-rendered h2, .markdown-rendered h3, .markdown-rendered h4,
.HyperMD-header, .inline-title { letter-spacing: -.012em; text-wrap: balance; }
.markdown-rendered h6, .HyperMD-header-6 { letter-spacing: .02em; }
.inline-title { letter-spacing: 0; }
.markdown-rendered strong, .cm-strong { font-weight: 600; }
.markdown-rendered a, .cm-hmd-internal-link, .cm-link, .cm-url {
  text-decoration-thickness: 1px;
  text-underline-offset: 4px;
}
.markdown-rendered a:hover, .cm-hmd-internal-link:hover, .cm-link:hover { text-decoration-color: var(--solforge-rubric); }
.markdown-rendered ul > li::marker, .markdown-rendered ol > li::marker,
.cm-formatting-list-ol { font-family: var(--font-monospace); font-size: .85em; color: var(--list-marker-color); }

/* Footnote references are rubric numerals, as on the site's sidenotes. */
.markdown-rendered sup a, .footnote-link, .cm-footref {
  font-family: var(--font-monospace);
  color: var(--solforge-rubric);
  text-decoration: none;
}

/* Inline code on a slip; blocks on the darker plate. */
.markdown-rendered code, .cm-s-obsidian span.cm-inline-code { background-color: var(--solforge-slip); }
.markdown-rendered pre, .markdown-rendered pre code,
.cm-s-obsidian div.HyperMD-codeblock-bg { background-color: var(--code-background); }

/* Tables keep only horizontal rules, with mono column labels. */
.markdown-rendered th, .markdown-rendered td,
.markdown-source-view.mod-cm6 .cm-table-widget th, .markdown-source-view.mod-cm6 .cm-table-widget td {
  border-inline: 0;
}
.markdown-rendered th, .markdown-source-view.mod-cm6 .cm-table-widget th {
  font-family: var(--font-monospace);
  font-size: .72em;
  font-weight: 400;
  color: var(--table-header-color);
  text-align: start;
}
.markdown-rendered table, .markdown-source-view.mod-cm6 .cm-table-widget table { font-variant-numeric: tabular-nums; }

/* Tags look like the site's letter boxes. */
.tag, .cm-hashtag { font-family: var(--font-monospace); font-size: .8em; }

/* Slips: a card on the sheet with a hairline under it and a short insertion
   mark on top, in rubric or the callout's own pigment. */
.callout, .setting-items { position: relative; }
.callout {
  mix-blend-mode: normal;
  background-color: var(--solforge-slip);
  border: 0;
  border-bottom: 1px solid var(--solforge-line);
}
.callout::before, .setting-items::before, .popover.hover-popover::before {
  content: "";
  position: absolute;
  z-index: 1;
  top: 0;
  left: 20px;
  width: 30px;
  height: 2px;
  background: var(--solforge-rubric);
  pointer-events: none;
}
.callout::before { left: var(--size-4-6); background: var(--callout-color); }
.callout-title { color: var(--callout-color); }
.callout-title-inner { font-weight: 500; }
.setting-items { border: 0; border-bottom: 1px solid var(--solforge-line); }
.setting-group .setting-item-heading .setting-item-name, .vertical-tab-header-group-title {
  font-family: var(--font-monospace);
  font-size: 11px;
  font-weight: 400;
  color: var(--solforge-rubric);
  letter-spacing: .04em;
}

/* Popovers, menus and the palette float as slips with a hairline frame. */
.popover.hover-popover, .menu, .suggestion-container, .prompt, .modal {
  border: 1px solid var(--solforge-line);
  box-shadow: 0 12px 40px var(--background-modifier-box-shadow);
}
.suggestion-highlight { color: var(--text-accent); }
.prompt-instructions, .suggestion-hotkey, kbd, .setting-hotkey {
  font-family: var(--font-monospace);
}
"""
