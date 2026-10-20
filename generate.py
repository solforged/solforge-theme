#!/usr/bin/env python3
"""Generate the Solforge themes: Omarchy palettes, backgrounds, previews and app ports.

The palettes extend the solforged.io sheet tokens (desk, sheet, ink, gilt,
rubric, line, grid) into a full Omarchy colors.toml. Backgrounds are
construction drawings after Leonardo's notebooks, drawn as wireframes on the
site's sheet-on-desk layout. Requires rsvg-convert and ImageMagick.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from drawings import FONT, PLATES, Sheet
from mask import face_of_judgment

ROOT = Path(__file__).resolve().parent

# Site tokens come first in each palette; the rest extend them for terminals.
THEMES = {
    "dark": {
        "name": "Solforge Dark",
        "icons": "Yaru-red",
        "site": {
            "desk": "#290401",
            "sheet": "#130807",
            "slip": "#211411",
            "ink": "#ece1ce",
            "muted": "#c2ab98",
            "gilt": "#dfb15a",
            "rubric": "#de8a70",
            "line": "#694135",
            "grid": "#36231c",
        },
        "colors": {
            "mode": "dark",
            "accent": "#dfb15a",
            "selection": "#4d1c15",
            "selection_foreground": "#faf3e4",
            "muted": "#8f7262",
            "background": "#130807",
            "dark_background": "#0e0605",
            "darker_background": "#090303",
            "lighter_background": "#211411",
            "foreground": "#ece1ce",
            "dark_foreground": "#8f7262",
            "light_foreground": "#c2ab98",
            "bright_foreground": "#faf3e4",
            "hyprland_active_border": "rgba(dfb15aee) rgba(8f2c1cee) 45deg",
            "hyprland_inactive_border": "rgba(4a2e25aa)",
            "red": "#d9654f",
            "yellow": "#dfb15a",
            "orange": "#d98c4a",
            "green": "#94ad7f",
            "cyan": "#6fa9a3",
            "blue": "#8798c7",
            "magenta": "#c98597",
            "brown": "#a87a55",
            "bright_red": "#de8a70",
            "bright_yellow": "#efcd85",
            "bright_green": "#b5cba0",
            "bright_cyan": "#96c7c0",
            "bright_blue": "#aab8de",
            "bright_magenta": "#dfa7b6",
        },
        # omp and Tern surfaces; Tern draws its tab bar in `chrome`, the oxblood desk.
        "ui": {
            "bg": "#130807", "bg_alt": "#190d0a", "bg_hl": "#211411",
            "border": "#694135", "border_muted": "#36231c",
            "comment": "#a58876", "gray": "#c2ab98", "fg": "#ece1ce", "fg_bright": "#faf3e4",
            "gilt": "#dfb15a", "rubric": "#de8a70", "red": "#d9654f", "orange": "#d98c4a",
            "green": "#94ad7f", "cyan": "#6fa9a3", "blue": "#8798c7", "madder": "#c98597",
            "sel": "#4d1c15", "diff_add": "#1b2414", "diff_delete": "#33100b",
            "chrome": "#290401", "widget": "#211411",
            "ansi0": "#4a2e25", "ansi7": "#c2ab98", "ansi15": "#faf3e4",
        },
    },
    "light": {
        "name": "Solforge Light",
        "icons": "Yaru-red",
        "site": {
            "desk": "#290401",
            "sheet": "#f6f1e6",
            "slip": "#e8dfd0",
            "ink": "#2a2120",
            "muted": "#65534a",
            "gilt": "#765411",
            "rubric": "#863f3d",
            "line": "#a39380",
            "grid": "#ddd3c1",
        },
        "colors": {
            "mode": "light",
            "accent": "#765411",
            "selection": "#ebd3c8",
            "selection_foreground": "#1a1312",
            "muted": "#857265",
            "background": "#f6f1e6",
            "dark_background": "#eee7da",
            "darker_background": "#e4d9c5",
            "lighter_background": "#e8dfd0",
            "foreground": "#2a2120",
            "dark_foreground": "#857265",
            "light_foreground": "#4f403a",
            "bright_foreground": "#1a1312",
            "hyprland_active_border": "rgba(765411ee) rgba(863f3dee) 45deg",
            "hyprland_inactive_border": "rgba(c9bba6aa)",
            "red": "#a3302a",
            "yellow": "#8a6212",
            "orange": "#a5531c",
            "green": "#4f6b3a",
            "cyan": "#2f6e6a",
            "blue": "#334f8a",
            "magenta": "#8a3a63",
            "brown": "#6b4423",
            "bright_red": "#b8402f",
            "bright_yellow": "#946a0c",
            "bright_green": "#5a7642",
            "bright_cyan": "#347a74",
            "bright_blue": "#4a66a3",
            "bright_magenta": "#a3507a",
        },
        "ui": {
            "bg": "#f6f1e6", "bg_alt": "#eee7da", "bg_hl": "#e8dfd0",
            "border": "#a39380", "border_muted": "#d9cebb",
            "comment": "#70605a", "gray": "#65534a", "fg": "#2a2120", "fg_bright": "#1a1312",
            "gilt": "#765411", "rubric": "#863f3d", "red": "#a3302a", "orange": "#a5531c",
            "green": "#4f6b3a", "cyan": "#2f6e6a", "blue": "#334f8a", "madder": "#8a3a63",
            "sel": "#ebd3c8", "diff_add": "#e2e8d3", "diff_delete": "#f3dbd3",
            "chrome": "#e8dfd0", "widget": "#fcfaf4",
            "ansi0": "#2a2120", "ansi7": "#8a7a6d", "ansi15": "#c9bba6",
        },
    },
}

# omp color roles, as names of `ui` vars. Tern reads the same file.
OMP_ROLES = {
    "accent": "gilt", "border": "border", "borderAccent": "gilt", "borderMuted": "border_muted",
    "success": "green", "error": "red", "warning": "orange", "muted": "gray", "dim": "comment",
    "text": "fg", "thinkingText": "gray",
    "selectedBg": "sel", "userMessageBg": "bg_hl", "userMessageText": "fg_bright",
    "customMessageBg": "bg_alt", "customMessageText": "gray", "customMessageLabel": "rubric",
    "toolPendingBg": "bg_alt", "toolSuccessBg": "diff_add", "toolErrorBg": "diff_delete",
    "statusLineBg": "bg", "toolTitle": "fg_bright", "toolOutput": "gray",
    "mdHeading": "gilt", "mdLink": "gilt", "mdLinkUrl": "comment", "mdCode": "rubric",
    "mdCodeBlock": "fg", "mdCodeBlockBorder": "border", "mdQuote": "gray", "mdQuoteBorder": "rubric",
    "mdHr": "border", "mdListBullet": "rubric",
    "toolDiffAdded": "green", "toolDiffRemoved": "red", "toolDiffContext": "gray",
    "syntaxComment": "comment", "syntaxKeyword": "madder", "syntaxFunction": "blue",
    "syntaxVariable": "fg", "syntaxString": "green", "syntaxNumber": "orange", "syntaxType": "gilt",
    "syntaxOperator": "gray", "syntaxPunctuation": "gray",
    "thinkingOff": "border", "thinkingMinimal": "comment", "thinkingLow": "cyan",
    "thinkingMedium": "blue", "thinkingHigh": "gilt", "thinkingXhigh": "rubric", "thinkingMax": "red",
    "bashMode": "cyan", "pythonMode": "madder",
    "statusLineSep": "border", "statusLineModel": "gilt", "statusLinePath": "blue",
    "statusLineGitClean": "green", "statusLineGitDirty": "orange", "statusLineContext": "cyan",
    "statusLineSpend": "blue", "statusLineStaged": "green", "statusLineDirty": "orange",
    "statusLineUntracked": "rubric", "statusLineOutput": "fg_bright", "statusLineCost": "gilt",
    "statusLineSubagents": "madder",
}

# Hermes skin color keys, as names of `ui` vars. The dark palette fills `colors`
# and the light one `light_colors`; the TUI overlays the block that matches the
# terminal's polarity. Neither sets `background`, so the terminal keeps its sheet.
HERMES_ROLES = {
    "ui_text": "fg", "ui_primary": "gilt", "ui_accent": "gilt", "ui_border": "border", "ui_label": "rubric",
    "ui_ok": "green", "ui_warn": "orange", "ui_error": "red", "ui_tool": "cyan", "ui_thinking": "comment",
    "banner_border": "rubric", "banner_title": "gilt", "banner_accent": "gilt", "banner_dim": "comment",
    "banner_text": "fg", "prompt": "fg_bright", "input_rule": "border", "response_border": "rubric",
    "shell_dollar": "blue", "selection_bg": "sel", "session_label": "gilt", "session_border": "border",
    "status_bar_bg": "bg_alt", "status_bar_text": "fg", "status_bar_strong": "gilt", "status_bar_dim": "comment",
    "status_bar_good": "green", "status_bar_warn": "gilt", "status_bar_bad": "orange", "status_bar_critical": "red",
    "voice_status_bg": "bg_alt", "completion_menu_bg": "bg_hl", "completion_menu_current_bg": "sel",
    "completion_menu_meta_bg": "bg_hl", "completion_menu_meta_current_bg": "sel",
    "diff_added": "diff_add", "diff_removed": "diff_delete", "diff_added_word": "green", "diff_removed_word": "red",
    "syntax_string": "green", "syntax_number": "orange", "syntax_keyword": "madder", "syntax_comment": "comment",
}

# Banner art takes one fixed color per row, whatever the terminal's polarity, so
# it uses the light palette's mid tones, which clear 3:1 on both sheets. A row
# without a color draws in the terminal's own foreground: the mask's silver.
HERO_TONES = {"hood": "bright_red", "trim": "orange", "gilt": "bright_yellow"}
HERO_ROWS = ["hood"] * 2 + [None] * 10 + ["gilt"] * 3
LOGO_ROWS = ["hood", "hood", "trim", "trim", "gilt", "gilt"]
LOGO_GLYPHS = {
    "T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
    "U": ["██╗   ██╗", "██║   ██║", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    "O": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
}

# Every glyph here is plain one-cell text. Hermes measures emoji such as the
# scales (U+2696) as two cells while Ghostty draws them in one, and that drift
# leaves stale characters beside the prompt.
TUNON = {
    "name": "tunon",
    "description": "Tunon the Adjudicator: the Face of Judgment in Solforge oxblood and gilt",
    "spinner": {
        "waiting_faces": ["(⊕)", "(◇)", "(✦)", "(◆)"],
        "thinking_faces": ["(⊕)", "(⌁)", "(◈)", "(◇)"],
        "thinking_verbs": [
            "weighing testimony", "hearing all sides", "consulting Kyros' law", "citing the Edicts",
            "examining evidence", "deliberating", "drafting the verdict", "binding fate"],
        "wings": [["⟪⊕", "⊕⟫"], ["⟪◇", "◇⟫"], ["⟪╸", "╺⟫"]],
    },
    "branding": {
        "agent_name": "Tunon",
        "welcome": "The court is in session. State your matter, or /help for commands.",
        "goodbye": "The court is adjourned. ⊕",
        "response_label": " ⊕ Tunon ",
        # Hermes trims whitespace off the symbol and adds one space; a braille
        # blank survives the trim and gives the sigil a second cell of room.
        "prompt_symbol": "⊕\u2800",
        "help_header": "(⊕) Available Commands",
    },
    "tool_prefix": "╎",
}

GENERATED = "Generated by solforge-theme/generate.py; edit that, not this."

# Zed syntax captures, as names of `ui` vars, in the pigments omp uses: madder
# keywords, lapis functions, verdigris escapes. A tuple adds a style or weight.
ZED_SYNTAX = {
    "attribute": "rubric", "boolean": "orange", "comment": ("comment", "italic"),
    "comment.doc": ("comment", "italic"), "constant": "orange", "constructor": "gilt", "embedded": "fg",
    "emphasis": ("fg", "italic"), "emphasis.strong": ("fg", "bold"), "enum": "gilt", "function": "blue",
    "hint": "comment", "keyword": "madder", "label": "rubric", "link_text": "gilt", "link_uri": "comment",
    "number": "orange", "operator": "gray", "predictive": ("comment", "italic"), "preproc": "madder",
    "primary": "fg", "property": "fg", "punctuation": "gray", "punctuation.bracket": "gray",
    "punctuation.delimiter": "gray", "punctuation.list_marker": "rubric", "punctuation.special": "rubric",
    "string": "green", "string.escape": "cyan", "string.regex": "cyan", "string.special": "cyan",
    "string.special.symbol": "cyan", "tag": "rubric", "text.literal": "rubric", "title": ("gilt", "bold"),
    "type": "gilt", "variable": "fg", "variable.special": "rubric", "variant": "orange",
}

# Helix scopes over a palette of `ui` vars plus `muted`; the same pigments as Zed.
HELIX_SCOPES = {
    "attribute": "rubric", "comment": {"fg": "comment", "modifiers": ["italic"]},
    "constant": "orange", "constant.character.escape": "cyan", "constant.numeric": "orange",
    "constructor": "gilt", "function": "blue", "function.macro": "madder", "function.special": "madder",
    "keyword": "madder", "label": "rubric", "namespace": "fg", "operator": "gray",
    "punctuation": "gray", "punctuation.special": "rubric", "special": "rubric",
    "string": "green", "string.regexp": "cyan", "string.special": "cyan", "tag": "rubric",
    "type": "gilt", "type.enum.variant": "orange", "variable": "fg", "variable.builtin": "rubric",
    "markup.heading": {"fg": "gilt", "modifiers": ["bold"]}, "markup.list": "rubric",
    "markup.bold": {"modifiers": ["bold"]}, "markup.italic": {"modifiers": ["italic"]},
    "markup.strikethrough": {"modifiers": ["crossed_out"]},
    "markup.link.url": {"fg": "comment", "modifiers": ["underlined"]}, "markup.link.text": "gilt",
    "markup.quote": {"fg": "gray", "modifiers": ["italic"]}, "markup.raw": "rubric",
    "diff.plus": "green", "diff.minus": "red", "diff.delta": "gilt", "diff.delta.moved": "cyan",
    "error": "red", "warning": "orange", "info": "blue", "hint": "comment",
    "diagnostic.error": {"underline": {"color": "red", "style": "curl"}},
    "diagnostic.warning": {"underline": {"color": "orange", "style": "curl"}},
    "diagnostic.info": {"underline": {"color": "blue", "style": "curl"}},
    "diagnostic.hint": {"underline": {"color": "comment", "style": "curl"}},
    "diagnostic.unnecessary": {"modifiers": ["dim"]}, "diagnostic.deprecated": {"modifiers": ["crossed_out"]},
    "ui.background": {"bg": "bg"}, "ui.text": "fg", "ui.text.focus": {"fg": "fg_bright", "bg": "sel"},
    "ui.text.inactive": "comment", "ui.text.directory": "blue", "ui.window": "border",
    "ui.cursor": {"fg": "bg", "bg": "gray"}, "ui.cursor.primary": {"fg": "bg", "bg": "gilt"},
    "ui.cursor.match": {"fg": "gilt", "modifiers": ["bold", "underlined"]},
    "ui.cursorline.primary": {"bg": "bg_alt"}, "ui.selection": {"bg": "bg_hl"}, "ui.selection.primary": {"bg": "sel"},
    "ui.highlight": {"bg": "bg_hl"}, "ui.linenr": "muted", "ui.linenr.selected": "gilt",
    "ui.statusline": {"fg": "fg", "bg": "chrome"}, "ui.statusline.inactive": {"fg": "comment", "bg": "bg_alt"},
    "ui.statusline.normal": {"fg": "bg", "bg": "gilt", "modifiers": ["bold"]},
    "ui.statusline.insert": {"fg": "bg", "bg": "green", "modifiers": ["bold"]},
    "ui.statusline.select": {"fg": "bg", "bg": "madder", "modifiers": ["bold"]},
    "ui.statusline.separator": "border",
    "ui.popup": {"fg": "fg", "bg": "widget"}, "ui.help": {"fg": "fg", "bg": "widget"},
    "ui.menu": {"fg": "fg", "bg": "widget"}, "ui.menu.selected": {"fg": "fg_bright", "bg": "sel"},
    "ui.menu.scroll": {"fg": "border", "bg": "widget"},
    "ui.virtual.whitespace": "border", "ui.virtual.wrap": "border", "ui.virtual.indent-guide": "border_muted",
    "ui.virtual.ruler": {"bg": "bg_alt"}, "ui.virtual.inlay-hint": {"fg": "comment", "modifiers": ["italic"]},
    "ui.virtual.jump-label": {"fg": "rubric", "modifiers": ["bold"]},
    "ui.bufferline": {"fg": "comment", "bg": "chrome"}, "ui.bufferline.background": {"bg": "chrome"},
    "ui.bufferline.active": {"fg": "fg_bright", "bg": "bg", "modifiers": ["bold"]},
    "ui.debug.breakpoint": "red", "ui.debug.active": "gilt",
}

# Nushell color_config: values and shapes, as `ui` vars or records of them.
NU_COLORS = {
    "separator": "comment", "header": {"fg": "gilt", "attr": "b"}, "row_index": "comment",
    "bool": "orange", "int": "orange", "float": "orange", "filesize": "cyan", "duration": "gilt",
    "date": "madder", "range": "gray", "binary": "madder", "string": "fg", "nothing": "comment",
    "record": "fg", "list": "fg", "block": "fg", "closure": "fg", "cell-path": "fg", "hints": "comment",
    "search_result": {"fg": "bg", "bg": "gilt"},
    "shape_and": "madder", "shape_binary": "madder", "shape_block": "gray", "shape_bool": "orange",
    "shape_closure": "gray", "shape_custom": "gilt", "shape_datetime": "madder", "shape_directory": "cyan",
    "shape_external": "blue", "shape_externalarg": "fg", "shape_external_resolved": "blue",
    "shape_filepath": "cyan", "shape_flag": "rubric", "shape_float": "orange",
    "shape_garbage": {"fg": "bg", "bg": "red"}, "shape_glob_interpolation": "cyan",
    "shape_globpattern": "cyan", "shape_int": "orange", "shape_internalcall": "blue",
    "shape_keyword": "madder", "shape_list": "gray", "shape_literal": "orange",
    "shape_match_pattern": "green", "shape_matching_brackets": {"attr": "u"}, "shape_nothing": "orange",
    "shape_operator": "gray", "shape_or": "madder", "shape_pipe": "madder", "shape_range": "gray",
    "shape_record": "gray", "shape_redirection": "madder", "shape_signature": "gilt",
    "shape_string": "green", "shape_string_interpolation": "cyan", "shape_table": "gray",
    "shape_variable": "rubric", "shape_vardecl": "rubric",
}

# Neovim highlight groups over the swatches plus washes, pigments faded into the
# sheet for backgrounds. A string links to another group.
NVIM_GROUPS = {
    "Normal": {"fg": "fg", "bg": "bg"}, "NormalNC": "Normal",
    "NormalFloat": {"fg": "fg", "bg": "widget"}, "FloatBorder": {"fg": "border", "bg": "widget"},
    "FloatTitle": {"fg": "gilt", "bg": "widget", "bold": True},
    "Cursor": {"fg": "bg", "bg": "gilt"}, "lCursor": "Cursor", "CursorIM": "Cursor", "TermCursor": "Cursor",
    "CursorLine": {"bg": "bg_alt"}, "CursorColumn": {"bg": "bg_alt"}, "ColorColumn": {"bg": "bg_alt"},
    "CursorLineNr": {"fg": "gilt", "bold": True}, "LineNr": {"fg": "muted"},
    "SignColumn": {"bg": "bg"}, "FoldColumn": {"fg": "muted", "bg": "bg"}, "Folded": {"fg": "gray", "bg": "bg_hl"},
    "WinSeparator": {"fg": "border"}, "VertSplit": "WinSeparator",
    "StatusLine": {"fg": "fg", "bg": "chrome"}, "StatusLineNC": {"fg": "comment", "bg": "bg_alt"},
    "TabLine": {"fg": "comment", "bg": "chrome"}, "TabLineFill": {"bg": "chrome"},
    "TabLineSel": {"fg": "fg_bright", "bg": "bg", "bold": True},
    "WinBar": {"fg": "gray", "bg": "bg"}, "WinBarNC": {"fg": "comment", "bg": "bg"},
    "Pmenu": {"fg": "fg", "bg": "widget"}, "PmenuSel": {"fg": "fg_bright", "bg": "sel"},
    "PmenuSbar": {"bg": "bg_hl"}, "PmenuThumb": {"bg": "border"},
    "PmenuKind": {"fg": "blue", "bg": "widget"}, "PmenuExtra": {"fg": "comment", "bg": "widget"},
    "PmenuMatch": {"fg": "gilt", "bg": "widget", "bold": True}, "PmenuMatchSel": {"fg": "gilt", "bg": "sel", "bold": True},
    "WildMenu": "PmenuSel", "Visual": {"bg": "sel"}, "VisualNOS": "Visual",
    "Search": {"bg": "gilt_wash_strong"}, "IncSearch": {"fg": "bg", "bg": "gilt"}, "CurSearch": "IncSearch",
    "Substitute": {"fg": "bg", "bg": "rubric"}, "MatchParen": {"fg": "gilt", "bold": True, "underline": True},
    "NonText": {"fg": "border"}, "Whitespace": {"fg": "border_muted"}, "SpecialKey": {"fg": "border"},
    "EndOfBuffer": {"fg": "bg"}, "Conceal": {"fg": "comment"},
    "Title": {"fg": "gilt", "bold": True}, "Directory": {"fg": "blue"},
    "ErrorMsg": {"fg": "red"}, "WarningMsg": {"fg": "orange"}, "MoreMsg": {"fg": "green"},
    "ModeMsg": {"fg": "gilt", "bold": True}, "Question": {"fg": "green"},
    "QuickFixLine": {"bg": "bg_hl", "bold": True},
    "SpellBad": {"sp": "red", "undercurl": True}, "SpellCap": {"sp": "orange", "undercurl": True},
    "SpellRare": {"sp": "madder", "undercurl": True}, "SpellLocal": {"sp": "cyan", "undercurl": True},
    "DiffAdd": {"bg": "diff_add"}, "DiffDelete": {"fg": "red", "bg": "diff_delete"},
    "DiffChange": {"bg": "gilt_wash"}, "DiffText": {"bg": "gilt_wash_strong"},
    "Added": {"fg": "green"}, "Changed": {"fg": "gilt"}, "Removed": {"fg": "red"},
    "Comment": {"fg": "comment", "italic": True}, "Constant": {"fg": "orange"}, "String": {"fg": "green"},
    "Character": "String", "Number": "Constant", "Boolean": "Constant", "Float": "Constant",
    "Identifier": {"fg": "fg"}, "Function": {"fg": "blue"}, "Statement": {"fg": "madder"},
    "Conditional": "Statement", "Repeat": "Statement", "Keyword": "Statement", "Exception": "Statement",
    "Label": {"fg": "rubric"}, "Operator": {"fg": "gray"},
    "PreProc": {"fg": "madder"}, "Include": "PreProc", "Define": "PreProc", "Macro": "PreProc", "PreCondit": "PreProc",
    "Type": {"fg": "gilt"}, "StorageClass": "Type", "Structure": "Type", "Typedef": "Type",
    "Special": {"fg": "rubric"}, "SpecialChar": {"fg": "cyan"}, "Tag": {"fg": "rubric"}, "Delimiter": {"fg": "gray"},
    "SpecialComment": {"fg": "comment", "bold": True}, "Debug": {"fg": "orange"},
    "Underlined": {"underline": True}, "Error": {"fg": "red"}, "Todo": {"fg": "bg", "bg": "gilt", "bold": True},
    "DiagnosticError": {"fg": "red"}, "DiagnosticWarn": {"fg": "orange"}, "DiagnosticInfo": {"fg": "blue"},
    "DiagnosticHint": {"fg": "comment"}, "DiagnosticOk": {"fg": "green"},
    "DiagnosticUnderlineError": {"sp": "red", "undercurl": True},
    "DiagnosticUnderlineWarn": {"sp": "orange", "undercurl": True},
    "DiagnosticUnderlineInfo": {"sp": "blue", "undercurl": True},
    "DiagnosticUnderlineHint": {"sp": "comment", "undercurl": True},
    "DiagnosticUnderlineOk": {"sp": "green", "undercurl": True},
    "DiagnosticVirtualTextError": {"fg": "red", "bg": "red_wash"},
    "DiagnosticVirtualTextWarn": {"fg": "orange", "bg": "orange_wash"},
    "DiagnosticVirtualTextInfo": {"fg": "blue", "bg": "blue_wash"},
    "DiagnosticVirtualTextHint": {"fg": "comment", "bg": "bg_alt"},
    "DiagnosticVirtualTextOk": {"fg": "green", "bg": "green_wash"},
    "DiagnosticUnnecessary": {"fg": "muted"}, "DiagnosticDeprecated": {"strikethrough": True},
    "LspReferenceText": {"bg": "bg_hl"}, "LspReferenceRead": {"bg": "bg_hl"},
    "LspReferenceWrite": {"bg": "bg_hl", "underline": True},
    "LspInlayHint": {"fg": "comment", "bg": "bg_alt", "italic": True},
    "LspSignatureActiveParameter": {"fg": "gilt", "bold": True},
    "@comment": "Comment", "@keyword": "Keyword", "@function": "Function", "@function.builtin": "Function",
    "@function.macro": "Macro", "@string": "String", "@string.escape": {"fg": "cyan"},
    "@string.regexp": {"fg": "cyan"}, "@string.special": {"fg": "cyan"},
    "@string.special.url": {"fg": "comment", "underline": True}, "@number": "Number", "@boolean": "Boolean",
    "@constant": "Constant", "@constant.builtin": "Constant", "@type": "Type", "@type.builtin": "Type",
    "@constructor": {"fg": "gilt"}, "@variable": {"fg": "fg"}, "@variable.builtin": {"fg": "rubric"},
    "@variable.parameter": {"fg": "fg"}, "@variable.member": {"fg": "fg"}, "@property": {"fg": "fg"},
    "@attribute": {"fg": "rubric"}, "@tag": "Tag", "@tag.attribute": {"fg": "gilt"}, "@tag.delimiter": "Delimiter",
    "@punctuation": "Delimiter", "@punctuation.bracket": "Delimiter", "@punctuation.delimiter": "Delimiter",
    "@punctuation.special": {"fg": "rubric"}, "@operator": "Operator", "@label": "Label", "@module": {"fg": "fg"},
    "@markup.heading": {"fg": "gilt", "bold": True}, "@markup.strong": {"bold": True},
    "@markup.italic": {"italic": True}, "@markup.strikethrough": {"strikethrough": True},
    "@markup.underline": {"underline": True}, "@markup.link": {"fg": "gilt"}, "@markup.link.label": {"fg": "gilt"},
    "@markup.link.url": {"fg": "comment", "underline": True}, "@markup.raw": {"fg": "rubric"},
    "@markup.quote": {"fg": "gray", "italic": True}, "@markup.list": {"fg": "rubric"},
    "@diff.plus": "Added", "@diff.minus": "Removed", "@diff.delta": "Changed",
    "GitSignsAdd": "Added", "GitSignsChange": "Changed", "GitSignsDelete": "Removed",
    "FlashLabel": {"fg": "bg", "bg": "rubric", "bold": True},
}


COLOR_ORDER = [
    "mode",
    None,
    "accent", "selection", "selection_foreground", "muted",
    None,
    "background", "dark_background", "darker_background", "lighter_background",
    None,
    "foreground", "dark_foreground", "light_foreground", "bright_foreground",
    None,
    "hyprland_active_border", "hyprland_inactive_border",
    None,
    "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown",
    None,
    "bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue", "bright_magenta",
]


# ---------------------------------------------------------------- color math

def rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(hex_color: str) -> float:
    def lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb(hex_color)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a: str, b: str, t: float) -> str:
    """`a` moved toward `b` by `t`."""
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(rgb(a), rgb(b)))


def alpha(hex_color: str, a: float) -> str:
    return f"{hex_color}{round(a * 255):02x}"


# ---------------------------------------------------------------- preview

def preview_overlay(theme: dict) -> str:
    c, p = theme["colors"], theme["site"]
    PW, PH = 2560, 1440
    gap, bar = 14, 40
    grad_stops = [part for part in c["hyprland_active_border"].split() if part.startswith("rgba")]
    stops = []
    for k, g in enumerate(grad_stops):
        hexpart = g[5:-1]
        stops.append(f'<stop offset="{k / max(1, len(grad_stops) - 1)}" stop-color="#{hexpart[:6]}"/>')
    inactive = "#" + c["hyprland_inactive_border"][5:11]
    mono = FONT
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}">',
           f'<defs><linearGradient id="ab" x1="0" y1="0" x2="1" y2="1">{"".join(stops)}</linearGradient></defs>']
    # Bar.
    out.append(f'<rect width="{PW}" height="{bar}" fill="{c["background"]}"/>')
    for k in range(5):
        col = c["accent"] if k == 0 else c["foreground"]
        op = "1" if k < 3 else "0.45"
        out.append(f'<text x="{28 + k * 34}" y="27" font-family="{mono}" font-size="18" fill="{col}" fill-opacity="{op}">{k + 1}</text>')
    out.append(f'<text x="{PW / 2}" y="27" font-family="{mono}" font-size="18" fill="{c["foreground"]}" text-anchor="middle">Monday 14:32</text>')
    out.append(f'<text x="{PW - 28}" y="27" font-family="{mono}" font-size="18" fill="{c["foreground"]}" text-anchor="end">⏻  ◐  ▲  ≡</text>')

    def window(x, y, w, h, active):
        border = "url(#ab)" if active else inactive
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c["background"]}" fill-opacity="0.97" '
                   f'stroke="{border}" stroke-width="3"/>')

    # Left column: editor above an active terminal. The drawing stays visible on the right.
    lw = 1120
    ex, ey, eh = gap * 2, bar + gap, 420
    window(ex, ey, lw, eh, False)
    lx, ly = gap * 2, ey + eh + gap * 2
    lh = PH - ly - gap * 2
    window(lx, ly, lw, lh, True)
    nw, nh = 640, 150
    nx, ny = PW - gap * 2 - nw, bar + gap * 2
    window(nx, ny, nw, nh, True)

    def spans(x, y, parts, size=22):
        s = f'<text x="{x}" y="{y}" font-family="{mono}" font-size="{size}" xml:space="preserve">'
        for text, key in parts:
            s += f'<tspan fill="{c[key]}">{escape(text)}</tspan>'
        out.append(s + "</text>")

    ty = ly + 50
    lines = [
        [("~/src/tessera", "blue"), (" on ", "foreground"), (" main", "magenta"), (" ⇡1", "cyan")],
        [("❯ ", "green"), ("git log --oneline -4", "foreground")],
        [("3f9c2e1 ", "yellow"), ("feat(notes): added perspective compare", "foreground")],
        [("a17d0b4 ", "yellow"), ("fix(sync): kept highlights on rename", "foreground")],
        [("9be4410 ", "yellow"), ("docs: described the reading sheet", "foreground")],
        [("27c81fa ", "yellow"), ("chore: bumped astro to 6", "muted")],
        [("", "foreground")],
        [("❯ ", "green"), ("ls", "foreground")],
        [("anacyclosis.md  ", "foreground"), ("assets/  ", "blue"), ("build.sh  ", "green"), ("notes/  ", "blue"), ("README.md", "foreground")],
        [("", "foreground")],
        [("❯ ", "green"), ("cargo test", "foreground")],
        [("   Compiling ", "green"), ("tessera-core v0.9.2", "foreground")],
        [("warning", "yellow"), (": unused import `Highlight`", "foreground")],
        [("error[E0502]", "red"), (": cannot borrow `sheet` as mutable", "foreground")],
        [("test result: ", "foreground"), ("ok", "green"), (". 214 passed; 0 failed", "foreground")],
        [("", "foreground")],
        [("❯ ", "green"), ("█", "foreground")],
    ]
    for k, parts in enumerate(lines):
        spans(lx + 34, ty + k * 38, parts)
    # Palette strip.
    sy = ly + lh - 128
    names = ["background", "red", "green", "yellow", "blue", "magenta", "cyan", "foreground"]
    brights = ["muted", "bright_red", "bright_green", "bright_yellow", "bright_blue", "bright_magenta", "bright_cyan", "bright_foreground"]
    for row, keys in enumerate((names, brights)):
        for k, key in enumerate(keys):
            out.append(f'<rect x="{lx + 34 + k * 136}" y="{sy + row * 52}" width="124" height="40" fill="{c[key]}" '
                       f'stroke="{p["line"]}" stroke-width="1"/>')

    code = [
        [("// The reading sheet keeps each perspective distinct.", "muted")],
        [("pub fn ", "magenta"), ("compare", "blue"), ("(", "foreground"), ("notes", "foreground"), (": &[", "foreground"), ("Note", "yellow"), ("]) -> ", "foreground"), ("Sheet", "yellow"), (" {", "foreground")],
        [("    let ", "magenta"), ("mut ", "magenta"), ("sheet = ", "foreground"), ("Sheet", "yellow"), ("::", "foreground"), ("new", "blue"), ("(", "foreground"), ('"anacyclosis"', "green"), (");", "foreground")],
        [("    for ", "magenta"), ("note ", "foreground"), ("in ", "magenta"), ("notes.", "foreground"), ("iter", "blue"), ("().", "foreground"), ("take", "blue"), ("(", "foreground"), ("6", "orange"), (") {", "foreground")],
        [("        sheet.", "foreground"), ("holder", "blue"), ("(note.", "foreground"), ("author", "cyan"), (", note.", "foreground"), ("shape", "cyan"), (");", "foreground")],
        [("    }", "foreground")],
        [("    sheet", "foreground")],
        [("}", "foreground")],
    ]
    for k, parts in enumerate(code):
        spans(ex + 34, ey + 56 + k * 38, parts)
    # Selection sample in the editor.
    out.append(f'<rect x="{ex + 30}" y="{ey + 56 + 2 * 38 - 27}" width="560" height="36" fill="{c["selection"]}" fill-opacity="0.85"/>')
    spans(ex + 34, ey + 56 + 2 * 38, code[2])
    status_y = ey + eh - 24
    out.append(f'<rect x="{ex + 3}" y="{status_y - 26}" width="{lw - 6}" height="40" fill="{c["lighter_background"]}"/>')
    spans(ex + 30, status_y, [(" NORMAL ", "accent"), ("  sheet.rs", "foreground"), ("   rust · utf-8", "muted")], 20)

    # Notification card.
    spans(nx + 30, ny + 46, [("Solforge", "accent")], 22)
    spans(nx + 30, ny + 86, [("Tessera synced 214 notes and 11 questions.", "foreground")], 22)
    spans(nx + 30, ny + 122, [("Anacyclosis · six perspectives compared", "light_foreground")], 22)
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- output

def write_colors(theme: dict, dest: Path) -> None:
    c = theme["colors"]
    lines = [f"# {theme['name']}: oxblood desk, vellum sheet, clockwork gilt. After solforged.io."]
    for key in COLOR_ORDER:
        if key is None:
            lines.append("")
        else:
            lines.append(f'{key} = "{c[key]}"')
    (dest / "colors.toml").write_text("\n".join(lines) + "\n")
    (dest / "icons.theme").write_text(theme["icons"] + "\n")
    (dest / "chromium.theme").write_text(",".join(str(v) for v in rgb(c["background"])) + "\n")


def ansi16(theme: dict) -> list[str]:
    """The 16 terminal colors that omp/Tern, Ghostty and Zed's terminal share."""
    u, c = theme["ui"], theme["colors"]
    return [u["ansi0"], c["red"], c["green"], c["yellow"], c["blue"], c["magenta"], c["cyan"], u["ansi7"],
            c["muted"], c["bright_red"], c["bright_green"], c["bright_yellow"], c["bright_blue"],
            c["bright_magenta"], c["bright_cyan"], u["ansi15"]]


def swatches(theme: dict) -> dict[str, str]:
    """The `ui` vars plus the palette's `muted`, which the editor ports name directly."""
    return {**theme["ui"], "muted": theme["colors"]["muted"]}


def omp_theme(variant: str, theme: dict) -> str:
    """omp theme with a `terminal` section, which Tern uses for its panes and chrome."""
    u = theme["ui"]
    doc = {
        "$schema": "https://raw.githubusercontent.com/can1357/oh-my-pi/main/packages/coding-agent/src/modes/theme/theme-schema.json",
        "name": f"solforge-{variant}",
        "vars": u,
        "colors": OMP_ROLES,
        "export": {"pageBg": "bg", "cardBg": "bg_alt", "infoBg": "bg_hl"},
        "terminal": {"background": "bg", "foreground": "fg", "chrome": "chrome", "widget": "widget",
                     "ansi": ansi16(theme)},
    }
    return json.dumps(doc, indent=2) + "\n"


def omp_report(theme: dict) -> None:
    """Lowest contrast of each text role over the surfaces omp draws it on."""
    u = theme["ui"]
    surfaces = ["bg", "bg_alt", "bg_hl", "sel", "diff_add", "diff_delete"]
    texts = ["fg", "fg_bright", "gray", "comment", "gilt", "rubric", "red", "orange", "green", "cyan", "blue", "madder"]
    low = sorted((contrast(u[t], u[s]), t, s) for t in texts for s in surfaces)[:3]
    print("  omp lowest: " + ", ".join(f"{t} on {s} {r:.1f}" for r, t, s in low))


def hermes_skin() -> str:
    """Hermes skin YAML for Tunon: paired Solforge palettes and the Face of Judgment."""
    tones = {k: THEMES["light"]["colors"][v] for k, v in HERO_TONES.items()}

    def art(rows: list[str], roles: list[str | None]) -> list[str]:
        return [f"  [{tones[r]}]{row}[/]" if r else f"  {row}" for row, r in zip(rows, roles, strict=True)]

    def block(variant: str) -> list[str]:
        u = THEMES[variant]["ui"]
        return [f'  {key}: "{u[var]}"' for key, var in HERMES_ROLES.items()]

    logo = ["".join(LOGO_GLYPHS[ch][i] for ch in "TUNON") for i in range(6)]
    s = json.dumps
    out = [f"# {GENERATED}",
           f"name: {TUNON['name']}", f"description: {s(TUNON['description'])}", "",
           "colors:", *block("dark"), "", "light_colors:", *block("light"), "", "spinner:"]
    for key, values in TUNON["spinner"].items():
        out.append(f"  {key}:")
        out += [f"    - {s(v, ensure_ascii=False)}" for v in values]
    out += ["", "branding:"]
    out += [f"  {k}: {s(v, ensure_ascii=False)}" for k, v in TUNON["branding"].items()]
    out += ["", f"tool_prefix: {s(TUNON['tool_prefix'], ensure_ascii=False)}", "",
            "banner_logo: |-", *art(logo, LOGO_ROWS), "",
            "banner_hero: |-", *art(face_of_judgment(), HERO_ROWS)]
    return "\n".join(out) + "\n"


def hermes_report() -> None:
    """Banner tones over both sheets; they get no polarity variant, so both must hold."""
    sheets = [THEMES[v]["colors"]["background"] for v in THEMES]
    for role, name in HERO_TONES.items():
        tone = THEMES["light"]["colors"][name]
        ratios = [contrast(tone, bg) for bg in sheets]
        print(f"  {role} {tone}: " + " ".join(f"{r:.1f} on {bg}" for r, bg in zip(ratios, sheets)))
        if min(ratios) < 3:
            raise SystemExit(f"banner tone {role} {tone} is under 3:1 on a sheet")


def ghostty_theme(theme: dict) -> str:
    """Ghostty theme; CLI tools that use ANSI color names take their colors from it."""
    u, c = theme["ui"], theme["colors"]
    out = [f"# {theme['name']}. {GENERATED}"]
    out += [f"palette = {i}={color}" for i, color in enumerate(ansi16(theme))]
    out += [f"background = {u['bg']}", f"foreground = {u['fg']}",
            f"cursor-color = {u['gilt']}", f"cursor-text = {u['bg']}",
            f"selection-background = {u['sel']}", f"selection-foreground = {c['selection_foreground']}",
            f"split-divider-color = {u['border']}"]
    return "\n".join(out) + "\n"


def zed_style(theme: dict) -> dict:
    """Zed theme style: desk-colored chrome around a sheet-colored editor."""
    v, c = swatches(theme), theme["colors"]
    clear = "#00000000"
    style = {
        "background": v["chrome"], "title_bar.background": v["chrome"],
        "title_bar.inactive_background": v["chrome"], "status_bar.background": v["chrome"],
        "tab_bar.background": v["chrome"], "tab.inactive_background": v["chrome"], "tab.active_background": v["bg"],
        "toolbar.background": v["bg"], "panel.background": v["bg_alt"], "surface.background": v["bg_alt"],
        "elevated_surface.background": v["widget"],
        "border": v["border"], "border.variant": v["border_muted"], "border.focused": v["gilt"],
        "border.selected": v["gilt"], "border.transparent": clear, "border.disabled": v["border_muted"],
        "pane.focused_border": v["gilt"], "pane_group.border": v["border"], "panel.focused_border": v["gilt"],
        "element.background": v["bg_hl"], "element.hover": v["border_muted"], "element.active": v["sel"],
        "element.selected": v["sel"], "element.disabled": v["bg_alt"],
        "ghost_element.background": clear, "ghost_element.hover": v["bg_hl"],
        "ghost_element.active": v["border_muted"], "ghost_element.selected": v["sel"],
        "ghost_element.disabled": clear, "drop_target.background": alpha(v["gilt"], 0.2),
        "text": v["fg"], "text.muted": v["gray"], "text.placeholder": v["comment"], "text.disabled": v["muted"],
        "text.accent": v["gilt"], "icon": v["fg"], "icon.muted": v["gray"], "icon.disabled": v["muted"],
        "icon.placeholder": v["comment"], "icon.accent": v["gilt"], "link_text.hover": v["gilt"],
        "editor.background": v["bg"], "editor.foreground": v["fg"], "editor.gutter.background": v["bg"],
        "editor.subheader.background": v["bg_alt"], "editor.active_line.background": v["bg_alt"],
        "editor.highlighted_line.background": v["bg_hl"], "editor.line_number": v["muted"],
        "editor.active_line_number": v["gilt"], "editor.invisible": v["border"],
        "editor.wrap_guide": v["border_muted"], "editor.active_wrap_guide": v["border"],
        "editor.indent_guide": v["border_muted"], "editor.indent_guide_active": v["border"],
        "editor.document_highlight.read_background": alpha(v["blue"], 0.15),
        "editor.document_highlight.write_background": alpha(v["orange"], 0.15),
        "editor.document_highlight.bracket_background": alpha(v["gilt"], 0.2),
        "search.match_background": alpha(v["gilt"], 0.25),
        "search.active_match_background": alpha(v["rubric"], 0.4),
        "scrollbar.thumb.background": alpha(v["border"], 0.5), "scrollbar.thumb.hover_background": v["border"],
        "scrollbar.thumb.border": clear, "scrollbar.track.background": clear, "scrollbar.track.border": clear,
        "minimap.thumb.background": alpha(v["border"], 0.4),
        "minimap.thumb.hover_background": alpha(v["border"], 0.6),
        "panel.indent_guide": v["border_muted"], "panel.indent_guide_active": v["border"],
        "panel.indent_guide_hover": v["border"],
        "version_control.added": v["green"], "version_control.modified": v["gilt"],
        "version_control.deleted": v["red"],
        "terminal.background": v["bg"], "terminal.ansi.background": v["bg"], "terminal.foreground": v["fg"],
        "terminal.bright_foreground": v["fg_bright"], "terminal.dim_foreground": v["muted"],
    }
    # Status colors: diff hunks use the created and deleted backgrounds.
    status = {
        "created": ("green", v["diff_add"]), "deleted": ("red", v["diff_delete"]),
        "success": ("green", v["diff_add"]), "error": ("red", v["diff_delete"]),
        "modified": ("gilt", None), "conflict": ("orange", None), "warning": ("orange", None),
        "renamed": ("blue", None), "info": ("blue", None), "hint": ("comment", None),
        "predictive": ("comment", None), "hidden": ("muted", None), "ignored": ("muted", None),
        "unreachable": ("muted", None),
    }
    for name, (var, bg) in status.items():
        style[name] = v[var]
        style[f"{name}.background"] = bg or alpha(v[var], 0.15)
        style[f"{name}.border"] = v[var]
    ansi = ansi16(theme)
    for i, name in enumerate(["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]):
        style[f"terminal.ansi.{name}"] = ansi[i]
        style[f"terminal.ansi.bright_{name}"] = ansi[i + 8]
        style[f"terminal.ansi.dim_{name}"] = mix(ansi[i], v["bg"], 0.35)
    peers = ["gilt", "blue", "green", "madder", "cyan", "orange", "rubric"]
    style["players"] = [{"cursor": v[p], "background": v[p], "selection": alpha(v[p], 0.25)} for p in peers]
    style["players"][0]["selection"] = v["sel"]
    style["accents"] = [v[p] for p in peers]
    syntax = {}
    for capture, spec in ZED_SYNTAX.items():
        var, flag = spec if isinstance(spec, tuple) else (spec, None)
        syntax[capture] = {"color": v[var], "font_style": "italic" if flag == "italic" else None,
                           "font_weight": 700 if flag == "bold" else None}
    style["syntax"] = syntax
    return style


def zed_theme() -> str:
    """Zed theme family with both variants; Zed picks one from the system appearance."""
    doc = {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": "Solforge",
        "author": "solforged",
        "themes": [{"name": t["name"], "appearance": variant, "style": zed_style(t)} for variant, t in THEMES.items()],
    }
    return json.dumps(doc, indent=2) + "\n"


def toml_inline(value) -> str:
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{k} = {toml_inline(x)}" for k, x in value.items()) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(toml_inline(x) for x in value) + "]"
    return json.dumps(value)


def helix_theme(theme: dict) -> str:
    """Helix theme: scopes name entries of its [palette], which holds the swatches."""
    v = swatches(theme)
    for scope, spec in HELIX_SCOPES.items():
        spec = spec if isinstance(spec, dict) else {"fg": spec}
        names = [spec.get("fg"), spec.get("bg"), spec.get("underline", {}).get("color")]
        if missing := [n for n in names if n and n not in v]:
            raise SystemExit(f"helix scope {scope} names unknown colors {missing}")
    out = [f"# {theme['name']}. {GENERATED}", ""]
    out += [f'"{scope}" = {toml_inline(spec)}' for scope, spec in HELIX_SCOPES.items()]
    out += ["", "[palette]", *(f'{name} = "{color}"' for name, color in v.items())]
    return "\n".join(out) + "\n"


def nushell_theme(theme: dict) -> str:
    """Nushell color_config, loaded by config.nu from the themes directory."""
    v = swatches(theme)

    def resolve(spec):
        if isinstance(spec, dict):
            return {k: x if k == "attr" else v[x] for k, x in spec.items()}
        return v[spec]

    return json.dumps({key: resolve(spec) for key, spec in NU_COLORS.items()}, indent=2) + "\n"


def btop_theme(theme: dict) -> str:
    """btop theme: each meter ramps from its pigment faded into the sheet up to the bright pigment."""
    v, c = swatches(theme), theme["colors"]

    def ramp(name: str) -> tuple[str, str, str]:
        return mix(c[name], v["bg"], 0.45), c[name], c[f"bright_{name}"]

    keys = {
        "main_bg": v["bg"], "main_fg": v["fg"], "title": v["gilt"], "hi_fg": v["rubric"],
        "selected_bg": v["sel"], "selected_fg": v["fg_bright"], "inactive_fg": v["muted"],
        "graph_text": v["gray"], "meter_bg": v["bg_hl"], "proc_misc": v["cyan"],
        "cpu_box": v["border"], "mem_box": v["border"], "net_box": v["border"], "proc_box": v["border"],
        "div_line": v["border_muted"],
    }
    gradients = {
        "temp": (v["blue"], v["gilt"], v["red"]), "cpu": (v["green"], v["gilt"], v["red"]),
        "process": (v["green"], v["gilt"], v["red"]), "free": ramp("green"), "cached": ramp("blue"),
        "available": ramp("cyan"), "used": ramp("red"), "download": ramp("blue"), "upload": ramp("magenta"),
    }
    for name, stops in gradients.items():
        keys.update(zip((f"{name}_start", f"{name}_mid", f"{name}_end"), stops))
    out = [f"# {theme['name']}. {GENERATED}"]
    out += [f'theme[{key}]="{color}"' for key, color in keys.items()]
    return "\n".join(out) + "\n"


def nvim_colorscheme() -> str:
    """One Neovim colorscheme for both palettes; 'background' picks the variant."""
    palettes, ansi = {}, {}
    for variant, theme in THEMES.items():
        v = swatches(theme)
        washes = {f"{n}_wash": mix(v[n], v["bg"], 0.85) for n in ("red", "orange", "blue", "green", "gilt")}
        palettes[variant] = {**v, **washes, "gilt_wash_strong": mix(v["gilt"], v["bg"], 0.7)}
        ansi[variant] = ansi16(theme)

    def lua(spec) -> str:
        if isinstance(spec, str):
            return f'{{ link = "{spec}" }}'
        parts = []
        for key, value in spec.items():
            if key in ("fg", "bg", "sp"):
                if value not in palettes["dark"]:
                    raise SystemExit(f"nvim group names unknown color {value}")
                parts.append(f"{key} = p.{value}")
            else:
                parts.append(f"{key} = {str(value).lower()}")
        return "{ " + ", ".join(parts) + " }"

    def table(colors: dict[str, str], indent: str) -> list[str]:
        return [f'{indent}{k} = "{c}",' for k, c in colors.items()]

    out = [f"-- Solforge for Neovim. {GENERATED}",
           "-- 'background' picks the palette: dark for Solforge Dark, light for Solforge Light.",
           "local palettes = {"]
    for variant in THEMES:
        out += [f"  {variant} = {{", *table(palettes[variant], "    "), "  },"]
    out += ["}", "local ansi = {"]
    for variant in THEMES:
        out.append(f"  {variant} = {{ " + ", ".join(f'"{c}"' for c in ansi[variant]) + " },")
    out += ["}", "",
            'vim.cmd("highlight clear")',
            'if vim.g.syntax_on then vim.cmd("syntax reset") end',
            'vim.g.colors_name = "solforge"',
            'local variant = vim.o.background == "light" and "light" or "dark"',
            "local p = palettes[variant]",
            "for i, color in ipairs(ansi[variant]) do",
            '  vim.g["terminal_color_" .. (i - 1)] = color',
            "end",
            "local function hl(name, spec)",
            "  vim.api.nvim_set_hl(0, name, spec)",
            "end",
            ""]
    out += [f'hl("{group}", {lua(spec)})' for group, spec in NVIM_GROUPS.items()]
    return "\n".join(out) + "\n"


def ports_report(theme: dict) -> None:
    """Editor text roles over the editor sheet and the desk-colored chrome."""
    v = swatches(theme)
    texts = ["fg", "gray", "comment", "muted", "gilt", "rubric", "red", "orange", "green", "cyan", "blue", "madder"]
    low = sorted((contrast(v[t], v[s]), t, s) for t in texts for s in ["bg", "bg_alt", "chrome", "widget"])[:3]
    print("  editor lowest: " + ", ".join(f"{t} on {s} {r:.1f}" for r, t, s in low))


def render(svg: str, png: Path, width: int | None = None) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as tmp:
        tmp.write(svg)
    cmd = ["rsvg-convert", tmp.name, "-o", str(png)]
    if width:
        cmd[1:1] = ["-w", str(width)]
    subprocess.run(cmd, check=True)
    Path(tmp.name).unlink()


def report(theme: dict) -> None:
    c = theme["colors"]
    bg = c["background"]
    keys = ["foreground", "light_foreground", "muted", "accent", "red", "yellow", "orange", "green", "cyan",
            "blue", "magenta", "brown", "bright_red", "bright_yellow", "bright_green", "bright_cyan",
            "bright_blue", "bright_magenta"]
    worst = min(keys, key=lambda k: contrast(c[k], bg))
    print(f"  contrast on {bg}: " + " ".join(f"{k}={contrast(c[k], bg):.1f}" for k in keys))
    print(f"  selection text {contrast(c['selection_foreground'], c['selection']):.1f}; lowest {worst}")


def main() -> int:
    for tool in ("rsvg-convert", "magick"):
        if not shutil.which(tool):
            print(f"missing {tool}", file=sys.stderr)
            return 1
    only = set(sys.argv[1:])
    for variant, theme in THEMES.items():
        dest = ROOT / f"omarchy-solforge-{variant}-theme"
        bgdir = dest / "backgrounds"
        bgdir.mkdir(parents=True, exist_ok=True)
        print(f"{theme['name']} -> {dest}")
        write_colors(theme, dest)
        report(theme)
        ports = {
            f"omp/solforge-{variant}.json": omp_theme(variant, theme),
            f"ghostty/solforge-{variant}": ghostty_theme(theme),
            f"helix/solforge-{variant}.toml": helix_theme(theme),
            f"nushell/solforge-{variant}.json": nushell_theme(theme),
            f"btop/solforge-{variant}.theme": btop_theme(theme),
        }
        for rel, text in ports.items():
            (ROOT / rel).parent.mkdir(exist_ok=True)
            (ROOT / rel).write_text(text)
        omp_report(theme)
        ports_report(theme)
        if not only:
            keep = {f"{slug}.png" for slug, *_ in PLATES}
            for old in bgdir.glob("*.png"):
                if old.name not in keep:
                    old.unlink()
        for slug, plate, title, draw in PLATES:
            if only and slug not in only:
                continue
            sheet = Sheet(theme["site"], plate, title)
            draw(sheet)
            render(sheet.svg(), bgdir / f"{slug}.png")
            print(f"  {slug}.png")
        # Preview: first background under a mock desktop.
        with tempfile.TemporaryDirectory() as tmp:
            overlay = Path(tmp) / "overlay.png"
            render(preview_overlay(theme), overlay)
            subprocess.run(
                ["magick", str(bgdir / f"{PLATES[0][0]}.png"), "-resize", "2560x1440", str(overlay),
                 "-composite", "-define", "png:exclude-chunks=date,time", str(dest / "preview.png")],
                check=True,
            )
        print("  preview.png")
    (ROOT / "zed").mkdir(exist_ok=True)
    (ROOT / "zed" / "solforge.json").write_text(zed_theme())
    print(f"Zed theme family -> {ROOT / 'zed' / 'solforge.json'}")
    (ROOT / "nvim" / "colors").mkdir(parents=True, exist_ok=True)
    (ROOT / "nvim" / "colors" / "solforge.lua").write_text(nvim_colorscheme())
    print(f"Neovim colorscheme -> {ROOT / 'nvim' / 'colors' / 'solforge.lua'}")
    (ROOT / "hermes").mkdir(exist_ok=True)
    (ROOT / "hermes" / "tunon.yaml").write_text(hermes_skin())
    print(f"Hermes skin -> {ROOT / 'hermes' / 'tunon.yaml'}")
    hermes_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
