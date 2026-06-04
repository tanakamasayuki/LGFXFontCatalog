#!/usr/bin/env python3
"""Generate the LGFXFontCatalog static site.

Default mode is intentionally useful on a local machine before the Arduino host
harness is working: it parses the pinned LovyanGFX headers, writes the harness
font table, and emits a metadata-only site. With --use-probe-output it also
imports metrics, coverage, and preview PNGs produced by font_catalog_probe.ino.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "generator"
DOCS = ROOT / "docs"
PROBE = GEN / "font_catalog_probe"
INTERNAL = Path.home() / ".arduino15" / "internal"
PIN_SKETCH = GEN / "sketch.yaml"

CATEGORY = {
    "GLCDfont": "bitmap",
    "BMPfont": "bitmap",
    "RLEfont": "bitmap",
    "FixedBMPfont": "bitmap",
    "GFXfont": "gfx",
    "U8g2font": "u8g2",
    "BDFfont": "bdf",
    "VLWfont": "vlw",
}

BLOCKS = [
    (0x0000, 0x007F, "Basic Latin"),
    (0x0080, 0x00FF, "Latin-1 Supplement"),
    (0x0100, 0x017F, "Latin Extended-A"),
    (0x0180, 0x024F, "Latin Extended-B"),
    (0x2000, 0x206F, "General Punctuation"),
    (0x3000, 0x303F, "CJK Symbols and Punctuation"),
    (0x3040, 0x309F, "Hiragana"),
    (0x30A0, 0x30FF, "Katakana"),
    (0x3130, 0x318F, "Hangul Compatibility Jamo"),
    (0x31F0, 0x31FF, "Katakana Phonetic Extensions"),
    (0x3400, 0x4DBF, "CJK Unified Ideographs Extension A"),
    (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
    (0xAC00, 0xD7AF, "Hangul Syllables"),
    (0xFF00, 0xFFEF, "Halfwidth and Fullwidth Forms"),
]


@dataclass
class Font:
    type: str
    name: str
    category: str
    family: str
    bold: bool
    italic: bool
    size: int | None
    unit: str | None
    script: str

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "family": self.family,
            "bold": self.bold,
            "italic": self.italic,
            "size": self.size,
            "unit": self.unit,
            "script": self.script,
        }


def pinned_version(name: str = "LovyanGFX") -> str:
    text = PIN_SKETCH.read_text()
    m = re.search(rf"^\s*-\s*{re.escape(name)}\s*\(([^)]+)\)", text, re.M)
    if not m:
        raise RuntimeError(f"{PIN_SKETCH} must pin {name}")
    return m.group(1).strip()


def ensure_downloaded(version: str) -> None:
    prefix = f"LovyanGFX_{version}_"
    if INTERNAL.exists() and any(d.name.startswith(prefix) for d in INTERNAL.iterdir()):
        return
    raise RuntimeError(
        f"LovyanGFX {version} was not found under {INTERNAL}. "
        "Build generator/download_lgfx first to download pinned libraries."
    )


def resolve_header(name: str, version: str) -> Path:
    if not INTERNAL.exists():
        raise RuntimeError(f"{INTERNAL} does not exist. Build generator/download_lgfx first.")
    prefix = f"{name}_{version}_"
    dirs = sorted(d for d in INTERNAL.iterdir() if d.name.startswith(prefix))
    if not dirs:
        raise RuntimeError(f"{name} {version} was not found under {INTERNAL}. Build generator/download_lgfx first.")
    header = dirs[0] / name / "src" / "lgfx" / "v1" / "lgfx_fonts.hpp"
    if header.exists():
        return header
    raise RuntimeError(
        f"{header} missing. Build generator/download_lgfx first to download pinned libraries."
    )


def parse_fonts(header: Path) -> list[tuple[str, str]]:
    src = header.read_text()
    block = src[src.index("namespace fonts") :]
    return re.findall(r"extern\s+const\s+lgfx::(\w*[Ff]ont)\s+(\w+)\s*;", block)


def script_of(name: str) -> str:
    if re.match(r"efontCN", name):
        return "cn"
    if re.match(r"efontTW", name):
        return "tw"
    if re.match(r"efontKR", name):
        return "ko"
    if re.search(r"efontJA|lgfxJapan|Mincho|Gothic|Japan|Kanji", name):
        return "ja"
    return "latin"


def classify(type_sym: str, name: str) -> Font:
    category = CATEGORY.get(type_sym, "other")
    bold = bool(re.search(r"Bold|_bi?$", name))
    italic = bool(re.search(r"Oblique|Italic|_b?i$", name))
    script = script_of(name)
    family, size, unit = name, None, None

    if m := re.match(r"^(.*?)(\d+)pt7b$", name):
        family = re.sub(r"(Bold|Oblique|Italic)+$", "", m.group(1))
        size, unit = int(m.group(2)), "pt"
    elif m := re.match(r"^efont([A-Z]{2})?_(\d+)(_(b|i|bi))?$", name):
        family = "efont" + (m.group(1) or "")
        size, unit = int(m.group(2)), "px"
    elif m := re.match(r"^(.*?)_(\d+)$", name):
        family = re.sub(r"_+$", "", m.group(1))
        size, unit = int(m.group(2)), "px"
    elif category != "bitmap" and (m := re.match(r"^([A-Za-z]+?)(\d+)$", name)):
        family, size, unit = m.group(1), int(m.group(2)), "px"

    if category == "bitmap":
        family, size, unit = name, None, None
    return Font(type_sym, name, category, family, bold, italic, size, unit, script)


def brief_sample(f: Font) -> str:
    if f.script == "cn":
        return "简体中文 ABC123"
    if f.script == "tw":
        return "繁體中文 ABC123"
    if f.script == "ko":
        return "한국어 ABC123"
    if f.script == "ja":
        return "日本語 ABC123"
    return "Wax Lily 12"


def rich_sample(f: Font) -> str:
    if f.script == "ja":
        return "新しい朝が来た、希望の朝だ。 いろはにほへと ちりぬるを 永 あ ア ＡＢＣ 0123"
    if f.script == "cn":
        return "床前明月光，疑是地上霜。 0123 ABC"
    if f.script == "tw":
        return "牀前明月光，疑是地上霜。 0123 ABC"
    if f.script == "ko":
        return "다람쥐 헌 쳇바퀴에 타고파 0123 ABC"
    return "The quick brown fox jumps over the lazy dog 0123456789 !?.,&@#%"


def c_string(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def write_table(fonts: list[Font], version: str) -> None:
    rows = []
    for f in fonts:
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", f.name):
            raise RuntimeError(f"unsafe font symbol name: {f.name}")
        rows.append(
            f'  {{ "{f.name}", &lgfx::v1::fonts::{f.name}, '
            f'"{c_string(brief_sample(f))}", "{c_string(rich_sample(f))}" }},'
        )
    text = (
        "// GENERATED by generator/generate.py from lgfx_fonts.hpp. Do not edit by hand.\n"
        f"// Source: LovyanGFX {version}.\n"
        "#pragma once\n"
        "#include <LovyanGFX.hpp>\n\n"
        "struct FontEntry {\n"
        "  const char* name;\n"
        "  const lgfx::v1::IFont* font;\n"
        "  const char* brief;\n"
        "  const char* rich;\n"
        "};\n\n"
        "static const FontEntry kFonts[] = {\n"
        + "\n".join(rows)
        + "\n};\n"
        "static const size_t kFontCount = sizeof(kFonts) / sizeof(kFonts[0]);\n"
    )
    (PROBE / "fonts_table.h").write_text(text)


def load_jsonl(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[row["name"]] = row
    return out


def flash_sizes(elf_path: Path | None, names: list[str], version: str) -> dict[str, int]:
    if not elf_path or not elf_path.exists():
        return {}
    try:
        cpp = resolve_header("LovyanGFX", version).with_name("lgfx_fonts.cpp").read_text()
        nm = subprocess.run(
            ["nm", "-C", "--print-size", "--radix=d", str(elf_path)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except Exception:
        return {}

    dmap = {}
    for m in re.finditer(r"const\s+\w*[Ff]ont\s+(\w+)\s*=\s*\{([^}]*)\}", cpp):
        ids = [re.sub(r"\([^)]*\)", "", t).strip() for t in m.group(2).split(",")]
        dmap[m.group(1)] = [t for t in ids if re.fullmatch(r"[A-Za-z_]\w*", t)]

    leaf = {}
    for line in nm.splitlines():
        parts = line.split(maxsplit=3)
        if len(parts) == 4 and parts[1].isdigit():
            key = parts[3].split("::")[-1]
            leaf[key] = leaf.get(key, 0) + int(parts[1])

    def syms(name: str) -> list[str]:
        return dmap[name] if name in dmap else [name + "Bitmaps", name + "Glyphs"]

    return {name: leaf.get(name, 0) + sum(leaf.get(sym, 0) for sym in syms(name)) for name in names}


def block_name(cp: int) -> str:
    for start, end, name in BLOCKS:
        if start <= cp <= end:
            return name
    return "Other BMP"


def cp_label(cp: int) -> str:
    if cp == 0x20:
        return "[space]"
    if cp == 0x3000:
        return "[ideographic space]"
    if cp < 0x20 or cp == 0x7F:
        return f"[control U+{cp:04X}]"
    return chr(cp)


def content_of(f: Font, metrics: dict | None) -> str:
    if f.script != "latin":
        return f.script
    if metrics and metrics.get("letters") is False and metrics.get("digits") is True:
        return "digits"
    return "latin"


def height_bucket(h: int | None) -> str | None:
    if h is None:
        return None
    if h <= 10:
        return "xs"
    if h <= 16:
        return "s"
    if h <= 24:
        return "m"
    if h <= 36:
        return "l"
    return "xl"


def page_shell(title: str, body: str, version: str, asset_prefix: str = "", extra_head: str = "") -> str:
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{asset_prefix}styles.css">
{extra_head}
</head>
<body>
{body}
<footer>Source: LovyanGFX {html.escape(version)}. Generated by LGFXFontCatalog.</footer>
</body>
</html>
"""


def render_index(fonts: list[Font], metrics: dict, coverage: dict, flash: dict, version: str) -> None:
    items = []
    index = []
    for f in sorted(fonts, key=lambda x: ((metrics.get(x.name) or {}).get("height", 9999), x.family, x.name)):
        m = metrics.get(f.name, {})
        cps = coverage.get(f.name, {}).get("codepoints", [])
        img = m.get("brief")
        glyph_count = len(cps) if cps else None
        row = {
            **f.as_dict(),
            "height": m.get("height"),
            "baseline": m.get("baseline"),
            "xAdvance": m.get("xAdvance"),
            "yAdvance": m.get("yAdvance"),
            "width": m.get("width"),
            "mono": m.get("mono"),
            "content": content_of(f, m),
            "heightBucket": height_bucket(m.get("height")),
            "flash": flash.get(f.name),
            "glyphCount": glyph_count,
            "preview": img,
            "url": f"fonts/{f.name}.html",
        }
        index.append(row)
        preview = f'<img src="{html.escape(img)}" alt="">' if img else f'<span>{html.escape(brief_sample(f))}</span>'
        facts = [
            f.family,
            f.category,
            f"{m['height']}px" if "height" in m else None,
            f"{glyph_count} chars" if glyph_count is not None else "coverage pending",
            f"{flash[f.name]} B" if f.name in flash else None,
        ]
        fact_text = " · ".join(x for x in facts if x)
        items.append(
            f'<a class="font-card" href="fonts/{f.name}.html" '
            f'data-name="{html.escape(f.name.lower())}" data-family="{html.escape(f.family.lower())}" '
            f'data-content="{row["content"]}" data-family-key="{html.escape(f.family)}" '
            f'data-bucket="{row["heightBucket"] or ""}" data-mono="{row["mono"]}">'
            f'<div class="preview">{preview}</div><strong>{html.escape(f.name)}</strong>'
            f'<small>{html.escape(fact_text)}</small></a>'
        )

    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "data" / "index.json").write_text(json.dumps({"source": f"LovyanGFX {version}", "fonts": index}, ensure_ascii=False, indent=2))
    body = f"""<main class="index">
<header>
  <h1>LGFXFontCatalog</h1>
  <input id="q" type="search" placeholder="Search font name or family" autocomplete="off">
</header>
<section class="toolbar">
  <select id="content"><option value="">All scripts</option><option value="latin">Latin</option><option value="digits">Digits</option><option value="ja">Japanese</option><option value="cn">Simplified Chinese</option><option value="tw">Traditional Chinese</option><option value="ko">Korean</option></select>
  <select id="bucket"><option value="">All heights</option><option value="xs">xs ≤10</option><option value="s">s 11-16</option><option value="m">m 17-24</option><option value="l">l 25-36</option><option value="xl">xl 37+</option></select>
</section>
<p id="count" class="count"></p>
<section id="grid" class="grid">
{''.join(items)}
</section>
<section class="notice">
  <h2>Notice</h2>
  <p>LGFXFontCatalog displays metadata and rendered previews derived from preset fonts bundled with LovyanGFX.</p>
  <p><a href="https://github.com/lovyan03/LovyanGFX">LovyanGFX</a></p>
  <p>The generated preview PNGs are rendered samples. This project does not redistribute LovyanGFX font binary data.</p>
</section>
</main>
<script src="app.js"></script>"""
    (DOCS / "index.html").write_text(page_shell("LGFXFontCatalog", body, version))


def render_detail(f: Font, metrics: dict, cov: dict, flash: int | None, version: str) -> None:
    cps = cov.get("codepoints", [])
    grouped: dict[str, list[int]] = {}
    for cp in cps:
        grouped.setdefault(block_name(cp), []).append(cp)

    block_rows = []
    char_sections = []
    for name, points in grouped.items():
        block_rows.append(f"<tr><td>{html.escape(name)}</td><td>{len(points)}</td></tr>")
        chars = " ".join(f'<span class="glyph">{html.escape(cp_label(cp))}<small>U+{cp:04X}</small></span>' for cp in points)
        char_sections.append(f"<section><h2>{html.escape(name)}</h2><p class=\"chars\">{chars}</p></section>")

    metric_rows = "".join(
        f"<tr><td>{k}</td><td>{html.escape(str(metrics.get(k, '')))}</td></tr>"
        for k in ["height", "baseline", "xAdvance", "yAdvance", "width", "mono"]
        if k in metrics
    )
    rich = metrics.get("rich")
    preview = f'<img class="specimen" src="../{html.escape(rich)}" alt="">' if rich else f'<div class="fallback-specimen">{html.escape(rich_sample(f))}</div>'
    body = f"""<main class="detail">
<p><a href="../index.html">← Index</a></p>
<header>
  <h1>{html.escape(f.name)}</h1>
  <p>{html.escape(f.family)} · {html.escape(f.category)} · {html.escape(f.script)} · {len(cps) if cps else "coverage pending"} chars</p>
</header>
{preview}
<section class="facts">
  <table><tbody>
    <tr><td>flash</td><td>{html.escape(str(flash)) + " B" if flash is not None else ""}</td></tr>
    {metric_rows}
  </tbody></table>
</section>
<section>
  <h2>Unicode Blocks</h2>
  <table><tbody>{''.join(block_rows) if block_rows else '<tr><td>Coverage has not been generated yet.</td><td></td></tr>'}</tbody></table>
</section>
<section>
  <h2>Covered Characters</h2>
  <p class="note">Use browser find to search this page. Control and space characters are shown as labels.</p>
  {''.join(char_sections) if char_sections else '<p class="note">Run the host probe to generate the full character listing.</p>'}
</section>
</main>"""
    out = DOCS / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{f.name}.html").write_text(page_shell(f"{f.name} - LGFXFontCatalog", body, version, asset_prefix="../"))


def write_static_assets() -> None:
    (DOCS / "styles.css").write_text("""*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;color:#1f2937;background:#f7f7f4}main{max-width:1180px;margin:0 auto;padding:24px}header{display:flex;gap:16px;align-items:center;justify-content:space-between;flex-wrap:wrap}h1{font-size:28px;margin:0}h2{font-size:18px;margin:28px 0 10px}input,select{height:36px;border:1px solid #c9c9c2;border-radius:6px;background:white;padding:0 10px}#q{min-width:min(460px,100%)}.toolbar{display:flex;gap:10px;margin:18px 0;flex-wrap:wrap}.count{color:#667085}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}.font-card{display:block;text-decoration:none;color:inherit;background:white;border:1px solid #ddded6;border-radius:8px;padding:10px;min-height:122px}.font-card:hover{border-color:#3b82f6}.preview{height:44px;display:flex;align-items:center;overflow:hidden;background:#111;margin:-2px -2px 8px;border-radius:5px;padding:4px;color:white}.preview img{max-width:100%;height:auto;image-rendering:auto}.preview span{font-size:20px;white-space:nowrap}.font-card strong{display:block;font-size:16px;line-height:1.2;font-weight:750;overflow-wrap:anywhere}.font-card small{display:block;color:#667085;margin-top:6px}.notice{margin-top:36px;border-top:1px solid #ddded6;padding-top:18px;color:#667085}.notice h2{color:#1f2937}.notice p{max-width:760px}.detail header{display:block}.detail table{border-collapse:collapse;background:white;border:1px solid #ddded6}.detail td{border-bottom:1px solid #e8e8e2;padding:7px 10px}.specimen{display:block;max-width:100%;background:#111;border-radius:6px;padding:8px;margin:16px 0}.fallback-specimen{font-size:28px;background:white;border:1px solid #ddded6;border-radius:6px;padding:16px;margin:16px 0}.note{color:#667085}.chars{display:flex;flex-wrap:wrap;gap:5px}.glyph{display:inline-flex;gap:4px;align-items:baseline;border:1px solid #e0e0da;background:white;border-radius:5px;padding:3px 5px}.glyph small{color:#667085;font-size:10px}footer{max-width:1180px;margin:0 auto;padding:24px;color:#667085}""")
    (DOCS / "app.js").write_text("""const q=document.querySelector('#q'),content=document.querySelector('#content'),bucket=document.querySelector('#bucket'),cards=[...document.querySelectorAll('.font-card')],count=document.querySelector('#count');function apply(){const query=(q.value||'').toLowerCase();let n=0;for(const c of cards){const ok=(!query||c.dataset.name.includes(query)||c.dataset.family.includes(query))&&(!content.value||c.dataset.content===content.value)&&(!bucket.value||c.dataset.bucket===bucket.value);c.hidden=!ok;if(ok)n++;}count.textContent=`${n} fonts`;}for(const el of [q,content,bucket])el.addEventListener('input',apply);apply();""")


def generate(use_probe_output: bool, write_only_table: bool) -> None:
    version = pinned_version("LovyanGFX")
    ensure_downloaded(version)
    header = resolve_header("LovyanGFX", version)
    fonts = [classify(t, n) for t, n in parse_fonts(header)]
    write_table(fonts, version)
    if write_only_table:
        print(f"wrote fonts_table.h for {len(fonts)} fonts")
        return

    metrics = load_jsonl(PROBE / "output" / "metrics.jsonl") if use_probe_output else {}
    coverage = load_jsonl(PROBE / "output" / "coverage.jsonl") if use_probe_output else {}
    assets_src = PROBE / "output" / "assets"
    assets_dst = DOCS / "assets"

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    if use_probe_output and assets_src.exists():
        shutil.copytree(assets_src, assets_dst)

    elfs = sorted(PROBE.glob("build/**/*.out"))
    flash = flash_sizes(elfs[0] if elfs else None, [f.name for f in fonts], version) if use_probe_output else {}
    write_static_assets()
    render_index(fonts, metrics, coverage, flash, version)
    for f in fonts:
        render_detail(f, metrics.get(f.name, {}), coverage.get(f.name, {}), flash.get(f.name), version)
    print(f"generated docs for {len(fonts)} fonts (probe={'yes' if use_probe_output else 'no'})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-probe-output", action="store_true", help="import metrics/coverage/PNGs from generator/font_catalog_probe/output")
    ap.add_argument("--write-table", action="store_true", help="only write the Arduino fonts_table.h")
    args = ap.parse_args()
    generate(args.use_probe_output, args.write_table)


if __name__ == "__main__":
    main()
