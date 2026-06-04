# LGFXFontCatalog

English version: [README.md](README.md)

LovyanGFX / M5GFX / M5Unified に同梱されているプリセットフォントの静的カタログサイトです。

このサイトは、ピン留めした LovyanGFX から生成し、GitHub Pages で公開する想定です。各フォントは
`docs/fonts/<name>.html` の詳細ページを持つため、他のツールから LovyanGFX のフォントシンボル名で
直接リンクできます。

## 表示する情報

- フォント名、ファミリ、カテゴリ、script、スタイル、公称サイズ
- host introspection で取得したメトリクス: height、baseline、advance、width、等幅/可変
- リンク済み host ELF から属性付けした flash 使用量
- 実際の LovyanGFX フォントで描画したプレビュー PNG
- Unicode ブロック別に grouped した収録文字一覧

コミット済みの `docs/` ディレクトリが GitHub Pages の公開物です。full host probe を走らせる前でも、
メタデータのみの `docs/` サイトをローカル生成できます。

## ディレクトリ構成

```text
docs/                     GitHub Pages 公開物
generator/                サイト生成器と host probe
generator/download_lgfx/  ピン留めライブラリの取得用最小 sketch
generator/font_catalog_probe/
                          LovyanGFX host introspection sketch
SPEC.md / SPEC.ja.md      仕様書
NOTICE                    帰属表示
```

## ローカル生成

Python 依存をローカル環境に入れます。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r generator/requirements.txt
```

メタデータのみのサイトを生成します。

```bash
.venv/bin/python generator/generate.py
```

これにより `docs/index.html`、`docs/data/index.json`、フォントごとの詳細ページが生成されます。
ピン留めした LovyanGFX が `~/.arduino15/internal` に取得済みなら、重い full coverage probe は不要です。

## Host Probe

完全なカタログ生成には、lang-ship host Arduino core と SDL 依存が必要です。GitHub workflow では
これを自動実行します。ローカルで軽く確認する場合は、先頭数フォントだけに制限します。

```bash
LGFX_FONT_CATALOG_LIMIT=2 .venv/bin/python -m pytest generator/font_catalog_probe/font_catalog_probe.py
.venv/bin/python generator/generate.py --use-probe-output
```

`LGFX_FONT_CATALOG_LIMIT` を指定しない場合、全フォントについて BMP 全コードポイントを走査するため、
かなり時間がかかります。

## GitHub Pages / Actions

`.github/workflows/generate.yml` の workflow は次を行います。

1. Python、Arduino CLI、SDL、binutils をインストールする。
2. ピン留めした LovyanGFX メタデータから probe 用 font table を生成する。
3. host probe を実行する。
4. メトリクス、coverage、flash サイズ、プレビュー PNG を含む `docs/` を再生成する。
5. 生成差分を `[skip ci]` 付きでコミットする。

GitHub Pages は `docs/` ディレクトリを公開元に設定してください。

## ライセンスと帰属

生成器とサイトコードは MIT ライセンスです。プレビュー PNG は LovyanGFX 同梱フォントを描画した
サンプルです。このプロジェクトは LovyanGFX のフォントバイナリデータを再配布しません。詳細は
`NOTICE` を参照してください。
