# LGFXFontCatalog

日本語版: [README.ja.md](README.ja.md)

Static catalog site for preset fonts bundled with LovyanGFX, M5GFX, and
M5Unified.

The site is generated from a pinned LovyanGFX release and is intended for GitHub
Pages. Each font gets a detail page under `docs/fonts/<name>.html`, so another
tool can link directly by the LovyanGFX font symbol name.

Published site: <https://tanakamasayuki.github.io/LGFXFontCatalog/>

## What It Shows

- Font name, family, category, script, style, and nominal size
- Host-introspected metrics: height, baseline, advance, width, fixed/proportional
- Flash footprint attributed from the linked host ELF
- Rendered preview PNGs from the actual LovyanGFX font
- Covered characters grouped by Unicode block, as searchable text

The committed `docs/` directory is the Pages output. A metadata-only `docs/`
site can be generated locally before running the full host probe.

`generator/sketch.yaml` records both the LovyanGFX and M5GFX pins. The current
generator uses LovyanGFX as the representative catalog; M5GFX is recorded for
version context only. The download and probe sketches intentionally depend only
on LovyanGFX, because building LovyanGFX and M5GFX in the same host sketch links
duplicate LGFX symbols.

## Repository Layout

```text
docs/                     GitHub Pages output
generator/                Site generator and host probe
generator/download_lgfx/  Minimal sketch used to download pinned libraries
generator/font_catalog_probe/
                          Host-side LovyanGFX introspection sketch
SPEC.md / SPEC.ja.md      Specification
NOTICE                    Attribution note
```

## Local Generation

Install Python dependencies into a local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r generator/requirements.txt
```

Generate the metadata-only site:

```bash
.venv/bin/python generator/generate.py
```

This writes `docs/index.html`, `docs/data/index.json`, and one detail page per
font. It does not require running the heavy full coverage probe if the pinned
LovyanGFX copy is already available under `~/.arduino15/internal`.

## Host Probe

The full catalog requires the lang-ship host Arduino core and SDL dependencies.
The GitHub workflow runs this automatically. For a quick local smoke test, limit
the probe to the first few fonts:

```bash
LGFX_FONT_CATALOG_LIMIT=2 .venv/bin/python -m pytest generator/font_catalog_probe/font_catalog_probe.py
.venv/bin/python generator/generate.py --use-probe-output
```

Without `LGFX_FONT_CATALOG_LIMIT`, the probe scans all BMP codepoints for every
font and can take a long time.

## GitHub Pages / Actions

The workflow in `.github/workflows/generate.yml`:

1. Installs Python, Arduino CLI, SDL, and binutils.
2. Builds `generator/download_lgfx` to download the pinned LovyanGFX copy.
3. Writes the probe font table from pinned LovyanGFX metadata.
4. Runs the host probe.
5. Regenerates `docs/` with metrics, coverage, flash sizes, and preview PNGs.
6. Commits generated changes back with `[skip ci]`.

Configure GitHub Pages to serve from the `docs/` directory.

## License And Attribution

Generator and site code are MIT licensed. Preview PNGs are rendered samples from
fonts bundled with LovyanGFX. The project does not redistribute LovyanGFX font
binary data. See `NOTICE`.
