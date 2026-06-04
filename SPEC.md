# LGFXFontCatalog Specification (English)

> Japanese version: [SPEC.ja.md](SPEC.ja.md). Keep both in sync.

## 1. Purpose

A static website that lets you inspect **each individual preset font** bundled with
LovyanGFX (and the identical font set shipped by M5GFX / M5Unified).

Core use cases:

- **Check "does this font include this character" via the browser's in-page find (Ctrl+F).**
  Each font's covered characters are listed **as text**, so string search works — not images.
- Inspect, per font: metrics (height / baseline / advances), flash footprint, fixed vs.
  proportional, **glyph count**, and a preview image.
- Search and filter a list to reach a specific font's detail page quickly.

The sibling project [LGFXScreenBuilder](https://github.com/(user)/LGFXScreenBuilder)
(the authoring tool) **links here by font name** (§6). Data generation is fully
self-contained and does not depend on LGFXScreenBuilder (§3).

## 2. Overview

- **Separate repository, hosted on GitHub Pages.** A static site (no build step for
  visitors; the generator runs offline / in CI once per refresh).
- **Self-contained.** Generates all data itself from a pinned LovyanGFX. It does not
  consume LGFXScreenBuilder's artifacts (it only reuses the *technique*, §10).
- **Rarely updated.** Regenerated only when LovyanGFX's font set changes — which is
  exactly why this SPEC exists for future-you.
- **Loosely coupled.** LGFXScreenBuilder links by font name only; the site always shows
  its own latest version (no version coordination, §6).

## 3. Data generation

### 3.1 Source

- A **pinned LovyanGFX** `lgfx_fonts.hpp` (the `extern` font declarations in `namespace fonts`).
- The font set is identical to M5GFX / M5Unified, so LovyanGFX v1 is treated as the
  representative catalog.
- The pinned version is recorded in the repo and shown in the site footer as `LovyanGFX x.y.z`.

### 3.2 Extraction method (reuse of a proven technique)

Render each font on a host LovyanGFX backend (lang-ship:host style, SDL/PC build) to
gather its information — same approach as the LGFXScreenBuilder introspection harness (§10).

- **Metrics**: height / baseline / x_advance / y_advance / width via `IFont::getDefaultMetric()`.
- **Fixed vs. proportional**: compare the x_advance of `'i'` and `'W'` (CJK-only fonts fall
  back to comparing full-width / Hangul glyphs).
- **Coverage (which characters) — determined reliably in two stages**:
  1. **Candidates**: across the BMP (0x0000–0xFFFF, excluding surrogates 0xD800–0xDFFF
     etc.), collect every codepoint for which `IFont::updateFontMetric(c)` returns true
     (no rendering, fast).
  2. **Confirm by rendering**: draw each candidate to a sprite and scan with `readPixel`
     for a lit pixel. `updateFontMetric` can return true even for glyphs the font cannot
     actually draw (e.g. the 7-segment Font7 claims to "cover" letters), so the
     **render-and-scan is the only reliable signal**.
  - Candidate ranges may be narrowed per script (latin → Basic Latin / Latin-1 / Latin
    Extended; ja → Kana / CJK Unified / CJK Symbols / Halfwidth-Fullwidth Forms;
    cn/tw → CJK Unified + Ext-A; ko → Hangul Syllables / Jamo). A full-BMP scan with
    candidate pruning is the most robust against missing a block.
- **Flash footprint**: attribute symbol sizes from a single linked ELF (`nm -C --print-size`).
  GFX fonts use name-prefixed Bitmaps/Glyphs; classic/U8g2/efont parse the data symbols
  from `lgfx_fonts.cpp`.
- **Preview image**: render a representative string at the font's native size, cropped to
  the text box, as a PNG. The string is script-specific and rendered in **two variants —
  brief (for the index) and rich (for the detail page)** (§5.4).

### 3.3 Artifacts

Keyed by font name, output data including:

- Classification (§5): family / size / unit / bold / italic / script / category.
- Metrics: height / baseline / xAdvance / yAdvance / width.
- mono (true = fixed / false = proportional / null = unknown).
- **Glyph count (total) and a per-Unicode-block breakdown.**
- **The list of covered codepoints** (for the real text baked into the detail page).
- flash (bytes).
- Preview images (PNG): two variants, brief (index) + rich (detail). Per-font file or
  atlas + box is an implementation choice.

For the index, emit a separate lightweight JSON (name, classification, facets, glyph
count, preview reference); bake the large coverage listing into each detail-page HTML so
the index stays light.

### 3.4 Build automation (GitHub Actions) + committing artifacts

Generation runs **on GitHub Actions**, not locally, and the **generated artifacts (under
the published directory) are committed back to the repository**. GitHub Pages serves the
committed output.

- **Workflow**: checkout → install toolchain (arduino-cli + host core, SDL deps,
  Python/Pillow, binutils for `nm`) → fetch the pinned LovyanGFX → run the generator
  (§3.2) → produce the published directory (`fonts/*.html`, `index.html`, `data/*.json`,
  `assets/*`) → **commit & push if there is a diff**.
- **Triggers**: manual (`workflow_dispatch`) as the baseline. May also run on push to the
  pinned-version file or to the generator (`generator/`). No scheduled runs needed since it
  is rarely updated.
- **Commit**: a bot commit (e.g. `chore: regenerate catalog (LovyanGFX x.y.z)`). To avoid
  **re-trigger loops**, add `[skip ci]` to the message or exclude artifact paths from the
  triggers.
- **Permissions**: `contents: write` (`GITHUB_TOKEN`) to push to the repo.
- **Why commit artifacts**: the site stays static with no visitor-facing build, decoupling
  the heavy host build (LovyanGFX/SDL) from Pages delivery. With artifacts committed, the
  last published output survives even if Actions fails.
- Watch repo bloat from large binaries (preview PNGs). Whether to split the published
  output to a dedicated branch (e.g. `gh-pages`) is an implementation decision.

## 4. Site structure

### 4.1 Index (navigation) page

- A font list (preview [**brief**, §5.4] + name + family + size + flash + **glyph count**).
  Each entry links to the detail page `/fonts/<name>.html`.
- **Search**: text search over font name / family.
- **Filters (facets, §5)**: script/content, height bucket, style (regular/bold/italic),
  fixed/proportional, family.
- **Sort**: default height → family → name (same as LGFXScreenBuilder). Also sortable by
  **glyph count**.
- A cross-font "character → fonts that contain it" search is **not** included (use per-page
  Ctrl+F instead; future extension §9).
- Reads only the lightweight JSON.

### 4.2 Per-font detail page (static HTML, `/fonts/<name>.html`)

- Header: font name, family, script, size, fixed/proportional, flash, **total glyph count**.
- **Glyph count breakdown**: counts per Unicode block (e.g. Basic Latin 95 / Hiragana 83 /
  CJK Unified Ideographs 6879 …).
- **Covered-character listing (the Ctrl+F target)**: per Unicode block, list the covered
  characters **as real text**, each annotated with its codepoint (U+XXXX). Control/space
  shown as placeholders. This makes in-page find work even without JS.
- Metrics table.
- Preview image (**rich specimen**, §5.4).
- Footer with license/attribution (§8) and an optional "how to use in LGFXScreenBuilder" note.
- **Baked into static HTML** (real files, not SPA hash routes): searchable without JS,
  deep link is a real URL.

## 5. Classification & facets

Vocabulary kept aligned with LGFXScreenBuilder (porting source in §10).

### 5.1 script (language / writing system)
Derived from the font name: `latin` / `cn` (Simplified) / `tw` (Traditional) / `ko`
(Hangul) / `ja` (Japanese).
- efontCN→cn, efontTW→tw, efontKR→ko, efontJA / lgfxJapan / Mincho / Gothic etc.→ja,
  otherwise latin.

### 5.2 content (character-set kind, for filtering)
`['latin','digits','ja','cn','tw','ko']`.
- CJK scripts adopt their script value directly.
- A non-CJK font that cannot draw letters but can draw digits is `digits` (e.g. the
  clock/7-segment Font6/Font7/Font8). Letter presence is decided by **rendering uppercase
  `ABC`** (clock fonts carry only lowercase a/p/m, so probing `a` would wrongly classify
  them as text fonts). Everything else is `latin`.

### 5.3 Height buckets
`xs ≤10` / `s 11–16` / `m 17–24` / `l 25–36` / `xl 37+` (based on measured height).

### 5.4 Representative preview strings (brief = index / rich = detail page)

Two preview variants. **Brief** is for the index thumbnail (short; language and width
character obvious at a glance). **Rich** is the detail-page specimen (a natural sample
exercising many glyphs, like a typical font-preview site). Both are rendered with the
actual font; uncovered glyphs come out blank (which is itself coverage information). Exact
wording is adjustable at implementation time.

**Brief (index)**
- latin (has letters): a width-contrasting phrase (e.g. `Wax Lily 12`).
- digits (digits only): `0123456789`.
- CJK: a self-naming word plus ASCII (CJK fonts also carry ASCII, so show letters too).
  ja=`日本語 ABC123` / cn=`简体中文 ABC123` / tw=`繁體中文 ABC123` / ko=`한국어 ABC123`.

**Rich (detail page, standard specimen)**
- latin (has letters): a pangram + digits + symbols.
  e.g. `The quick brown fox jumps over the lazy dog` / `0123456789 !?.,&@#%`.
- digits (digits only): a clock-friendly sample. `0123456789` + `12:34:56` + whatever
  punctuation it carries (`-.`).
- ja (Japanese): the classic specimen text. `新しい朝が来た、希望の朝だ。` + the iroha
  `いろはにほへと ちりぬるを` + kana/kanji samples `永 あ ア ＡＢＣ 0123`.
- cn (Simplified): a classic verse. `床前明月光，疑是地上霜。` + `0123 ABC`.
- tw (Traditional): a classic verse (traditional). `牀前明月光，疑是地上霜。` + `0123 ABC`.
- ko (Hangul): the classic pangram. `다람쥐 헌 쳇바퀴에 타고파` + `0123 ABC`.

## 6. Link contract from LGFXScreenBuilder

- **URL**: `<BASE>/fonts/<name>.html`, where `<name>` is the font symbol name (e.g. `Font6`,
  `lgfxJapanGothic_16`, `FreeSans12pt7b`).
- **No version in the URL (font name only, latest fixed)**. The site always shows its own
  latest version.
- LGFXScreenBuilder places a "detail ↗" link on font-grid tiles and the Text font picker,
  opening in a **new tab** (`target=_blank rel=noopener`). `<BASE>` lives as a single
  constant in the tool; if unset, the link is hidden.
- **Version skew tolerance**: if the tool later updates LovyanGFX while this site lags,
  names are stable enough to still match. If the name is absent, redirect to the index or
  tolerate a 404.
- This contract (URL shape, name-only, new tab) is also recorded in LGFXScreenBuilder's SPEC.

## 7. Directory layout (intended)

```
LGFXFontCatalog/
  SPEC.ja.md / SPEC.md      # this spec
  LICENSE                   # MIT
  NOTICE                    # attribution (§8)
  .github/workflows/        # generate-and-commit GitHub Actions (§3.4)
  generator/                # offline generator (self-contained)
  site/ (or docs/)          # GitHub Pages output (committed by Actions)
    index.html              # index (search / filter)
    fonts/<name>.html       # font detail (covered chars baked in)
    data/index.json         # lightweight data for the index
    assets/...              # preview images, etc.
```
The published directory (`docs/` vs `site/` vs a `gh-pages` branch) is finalized at
implementation time per the GitHub Pages setting (artifact-commit policy in §3.4).

## 8. License & attribution

- **Generator and site code = MIT** ([LICENSE](LICENSE), same as LGFXScreenBuilder).
- The displayed **glyph samples / preview images are rendered from fonts bundled with
  LovyanGFX**, and each font follows its own original license (FreeFonts/GFX, efont, M+,
  TomThumb, etc.). `NOTICE` credits LovyanGFX and states that the samples derive from its
  bundled fonts, linking to LovyanGFX's font-license documentation.
- **Font binaries are not redistributed.** Only rendered PNGs and codepoint listings
  (factual coverage data) are published.

## 9. Future extensions (undecided, post-MVP)

- A cross-font "character → fonts that contain it" search (feasible by shipping a coverage
  JSON with the index; not included initially).
- Hosting multiple LovyanGFX versions in parallel, with a version added to the §6 URL.
- Showing the actual LGFX-rendered glyph image next to each covered character (heavy;
  optional).

## 10. Reference implementation (LGFXScreenBuilder side)

Port / reuse the **technique** of these files (a handoff of the approach, not a code copy).

- `tests/manual/font_introspect/gen.py` —
  `parse_fonts` / `script_of` / `classify` / `sample_for` / `font_flash_sizes` /
  pinned-version resolution, header fetch, download. Font-table generation.
- `tests/manual/font_introspect/font_introspect.ino` —
  `drawsGlyph` (render + readPixel = reliable coverage) / `detectMono` / ASCII & CJK
  probes. **This site extends that into full-codepoint enumeration** (§3.2).
- `tests/manual/font_introspect/font_introspect.py` —
  atlas packing and `font-metrics.json` output (reference for the output fields).
- `docs/src/fonts.js` —
  `HEIGHT_BUCKETS` / `CONTENT_TYPES` / `contentOf` / `filterCatalog` / `sampleFor` /
  `fmtBytes` / `approxCss` / `describe` (facet and label definitions).
- `docs/src/fontsview.js` — the filter UI and sort (height → family → name).
- LGFXScreenBuilder `SPEC.ja.md` / `SPEC.md` §8.7 (font strategy).
