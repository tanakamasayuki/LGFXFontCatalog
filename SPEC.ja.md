# LGFXFontCatalog 仕様書（日本語）

> 英語版は [SPEC.md](SPEC.md)。両者は同期して更新する。

## 1. 目的

LovyanGFX（および M5GFX / M5Unified が同梱する同一フォントセット）に収録された
**プリセットフォント1つ1つの詳細**を、静的Webサイトとして閲覧できるようにする。

中心的なユースケース:

- **「このフォントにこの文字は入っているか」をブラウザのページ内検索（Ctrl+F）で確認する。**
  各フォントの収録文字を **テキストとして** 列挙するので、画像ではなく文字列検索が効く。
- メトリクス（高さ・ベースライン・送り幅）、フラッシュ消費サイズ、等幅/可変、
  **収録文字数**、プレビュー画像をフォント単位で確認する。
- 一覧から検索・フィルタして目的のフォント詳細へ素早く辿り着く。

このサイトは姉妹プロジェクト [LGFXScreenBuilder](https://github.com/（user）/LGFXScreenBuilder)
（オーサリングツール）から **フォント名でリンク** される（§6）。ただしデータ生成は完全に
self-contained で、LGFXScreenBuilder には依存しない（§3）。

## 2. 全体像

- **別リポジトリ・GitHub Pages ホスト。** 静的サイト（ビルドステップ無しを基本とするが、
  生成スクリプトはオフラインで一度だけ走らせる）。
- **自己完結。** ピン留めした LovyanGFX のフォントから自前で全データを生成する。
  LGFXScreenBuilder の生成物には依存しない（手法のみ参照＝§10）。
- **あまり更新しない。** LovyanGFX のフォントセットが変わったときだけ再生成する想定。
  だからこそ将来の自分のためにこの SPEC を残す。
- **疎結合。** LGFXScreenBuilder からはフォント名のみでリンクされる。サイトは常に自分の
  最新版を表示する（バージョン連携はしない、§6）。

## 3. データ生成

### 3.1 ソース

- **ピン留めした LovyanGFX** の `lgfx_fonts.hpp`（`namespace fonts` の `extern` フォント宣言）。
- フォントセットは M5GFX / M5Unified と同一なので、LovyanGFX 1系を代表カタログとして扱う。
- ピン留めバージョンはリポジトリ内に明記し、サイトのフッタにも `LovyanGFX x.y.z` を表示する。

### 3.2 抽出方式（実証済みの手法を踏襲）

ホスト上の LovyanGFX バックエンド（lang-ship:host 相当、SDL/PC ビルド）で各フォントを実際に
描画して情報を得る。LGFXScreenBuilder の introspection harness と同じ考え方（§10 参照）。

- **メトリクス**: `IFont::getDefaultMetric()` から height / baseline / x_advance / y_advance / width。
- **等幅/可変判定**: `'i'` と `'W'` の x_advance を比較（CJK専用フォントは全角/ハングルで代替比較）。
- **収録文字（カバレッジ）= 2段階で確実に求める**:
  1. **候補抽出**: BMP（0x0000–0xFFFF、サロゲート 0xD800–0xDFFF 等は除外）にわたって
     `IFont::updateFontMetric(c)` が真を返すコードポイントを候補とする（描画不要で高速）。
  2. **実描画で確定**: 候補それぞれをスプライトへ描画し、`readPixel` で点灯ピクセルが
     あるかを走査して確定する。`updateFontMetric` は実際には描けない文字でも真を返す
     ことがある（例: 7セグの Font7 が英字を「収録」と主張する）ため、**実描画走査が
     唯一信頼できる判定**。
  - スクリプト別に候補範囲を絞ってもよい（latin系=Basic Latin/Latin-1/Latin Extended、
    ja=かな・CJK統合漢字・CJK記号・半角全角形、cn/tw=CJK統合漢字＋拡張A、
    ko=ハングル音節・字母）。ただし取りこぼし防止には BMP 全走査＋候補プルーニングが堅い。
- **フラッシュ消費サイズ**: リンク済み単一 ELF からシンボルサイズを属性付け（`nm -C --print-size`）。
  GFX系は名前接頭辞付き Bitmaps/Glyphs、classic/U8g2/efont は `lgfx_fonts.cpp` のデータシンボルを解析。
- **プレビュー画像**: フォントのネイティブサイズで代表文字列を描画し、テキスト箱にクロップした PNG。
  代表文字列はスクリプト別で**簡易（一覧用）と豪華（詳細用）の2種**を描画する（§5.4）。

### 3.3 生成物

フォント名をキーに、以下を含むデータを出力する:

- 分類（§5）: family / size / unit / bold / italic / script / category。
- メトリクス: height / baseline / xAdvance / yAdvance / width。
- mono（true=等幅 / false=可変 / null=不明）。
- **収録文字数（総数）と Unicode ブロック別の内訳数**。
- **収録コードポイント一覧**（詳細ページに焼き込む実テキスト用）。
- flash（バイト）。
- プレビュー画像（PNG）: 簡易（一覧用）＋豪華（詳細用）の2種。フォント単位 or アトラス＋box は実装判断。

インデックス用には軽量 JSON（名前・分類・facet・収録文字数・プレビュー参照）を別に出し、
巨大な収録文字一覧は各詳細ページ HTML に焼き込んでインデックスを軽く保つ。

### 3.4 生成の自動化（GitHub Actions）＋生成物コミット

生成はローカルではなく **GitHub Actions 上で実行**し、**生成物（公開ディレクトリ配下）を
リポジトリにコミットして戻す**。GitHub Pages はコミット済みの公開物から配信する。

- **ワークフロー処理**: チェックアウト → ツールチェイン導入（arduino-cli ＋ host コア、
  SDL 等の依存、Python/Pillow、`nm` 用 binutils）→ ピン留め LovyanGFX 取得 →
  生成器を実行（§3.2）→ `docs/` 公開ディレクトリ（`fonts/*.html`・`index.html`・`data/*.json`・
  `assets/*`）を生成 → **差分があればコミット＆プッシュ**。
- **トリガ**: 手動（`workflow_dispatch`）を基本。加えてピン留めバージョンを書いたファイルや
  生成器（`generator/`）への push でも走らせてよい。「あまり更新しない」ので定期実行は不要。
- **コミット**: ボットがコミット（例 `chore: regenerate catalog (LovyanGFX x.y.z)`）。
  **再実行ループ防止**のためコミットメッセージに `[skip ci]` を付ける、または生成物コミットを
  トリガ対象パスから除外する。
- **権限**: `contents: write`（`GITHUB_TOKEN`）でリポジトリへプッシュ。
- **生成物をコミットする理由**: サイトは静的でビルドステップ無しを基本とし、重いホストビルド
  （LovyanGFX/SDL）を閲覧者・Pages 配信から切り離すため。生成物がコミットされていれば、
  Actions が落ちても直近の公開物は維持される。
- 生成物のうち巨大バイナリ（プレビュー PNG 群）はリポジトリ肥大に注意。必要なら公開専用ブランチ
  （例 `gh-pages`）へ分離するかは実装時判断。

## 4. サイト構成

### 4.1 インデックス（ナビゲーション）ページ

- フォント一覧（プレビュー〔**簡易**、§5.4〕＋名前＋ファミリ＋サイズ＋flash＋**収録文字数**）。
  各項目が詳細ページ `/fonts/<name>.html` へのリンク。
- **検索**: フォント名・ファミリのテキスト検索。
- **フィルタ（facet、§5）**: script/content・高さバケット・スタイル（regular/bold/italic）・
  等幅/可変・ファミリ。
- **ソート**: 既定は 高さ→ファミリ→名前（LGFXScreenBuilder と同じ）。**収録文字数**でも並べ替え可。
- 横断的な「文字→収録フォント」検索は **付けない**（各詳細ページの Ctrl+F で代替。将来拡張§9）。
- 軽量 JSON のみを読む。

### 4.2 フォント詳細ページ（静的 HTML、`/fonts/<name>.html`）

- ヘッダ: フォント名・ファミリ・script・サイズ・等幅/可変・flash・**総収録文字数**。
- **収録文字数の内訳**: Unicode ブロック別の個数（例: Basic Latin 95 / ひらがな 83 /
  CJK統合漢字 6879 …）。
- **収録文字の羅列（Ctrl+F の対象）**: Unicode ブロックごとに、収録している文字を
  **実テキストで** 列挙する。各文字にコードポイント（U+XXXX）を併記。
  制御文字・空白はプレースホルダ表記。これにより JS 無しでもページ内検索が効く。
- メトリクス表。
- プレビュー画像（**豪華 specimen**、§5.4）。
- 末尾にライセンス/帰属（§8）と「LGFXScreenBuilder で使うには」程度の案内（任意）。
- **静的 HTML に焼き込む**（SPA ハッシュではなく実ファイル）。JS 無しで検索可・直リンクが実 URL。

## 5. 分類・facet 定義

LGFXScreenBuilder と用語を揃える（移植元は §10）。

### 5.1 script（言語/文字体系）
フォント名から導出: `latin` / `cn`（簡体）/ `tw`（繁体）/ `ko`（ハングル）/ `ja`（日本語）。
- efontCN→cn、efontTW→tw、efontKR→ko、efontJA・lgfxJapan・Mincho・Gothic 等→ja、その他→latin。

### 5.2 content（収録文字種、フィルタ用）
`['latin','digits','ja','cn','tw','ko']`。
- CJK系は script をそのまま採用。
- 非CJKで「英字を描けず数字のみ描ける」フォントは `digits`（例: Font6/Font7/Font8 のクロック・
  7セグ系）。英字判定は **大文字 `ABC` の実描画**で行う（クロック系は小文字 a/p/m しか
  持たないため、`a` 判定だと誤って text 扱いになる）。それ以外は `latin`。

### 5.3 高さバケット
`xs ≤10` / `s 11–16` / `m 17–24` / `l 25–36` / `xl 37+`（実測 height ベース）。

### 5.4 代表プレビュー文字列（簡易＝一覧用 / 豪華＝詳細ページ用）

プレビューは2種類。**簡易**はインデックスのサムネイル用（短く、言語と幅特性が一目で分かる）。
**豪華**は詳細ページの specimen 用（よくあるフォント確認サイトのように、多くのグリフを使った
自然な例文）。どちらもフォントの実描画でレンダリングし、収録外グリフは空白になる（＝それも
カバレッジ情報）。具体的な文面は実装時に微調整可。

**簡易（一覧用）**
- latin（英字あり）: 幅コントラストの出る語（例: `Wax Lily 12`）。
- digits（数字のみ）: `0123456789`。
- CJK: 自己説明の語＋ASCII（CJKフォントもASCIIを持つので英字も見せる）。
  ja=`日本語 ABC123` / cn=`简体中文 ABC123` / tw=`繁體中文 ABC123` / ko=`한국어 ABC123`。

**豪華（詳細ページ用、定番 specimen）**
- latin（英字あり）: パングラム＋数字＋記号。
  例: `The quick brown fox jumps over the lazy dog` / `0123456789 !?.,&@#%`。
- digits（数字のみ）: 時計系で映える例。`0123456789` ＋ `12:34:56` ＋ `-.` など収録の記号。
- ja（日本語）: 定番の見本文。`新しい朝が来た、希望の朝だ。` ＋ いろは `いろはにほへと ちりぬるを` ＋
  かな/漢字サンプル `永 あ ア ＡＢＣ 0123`。
- cn（簡体）: 定番詩文。`床前明月光，疑是地上霜。` ＋ `0123 ABC`。
- tw（繁体）: 定番詩文（繁体字）。`牀前明月光，疑是地上霜。` ＋ `0123 ABC`。
- ko（ハングル）: 定番パングラム。`다람쥐 헌 쳇바퀴에 타고파` ＋ `0123 ABC`。

## 6. LGFXScreenBuilder からのリンク契約

- **URL**: `<BASE>/fonts/<name>.html`。`<name>` はフォントのシンボル名（例 `Font6`,
  `lgfxJapanGothic_16`, `FreeSans12pt7b`）。
- **バージョンは含めない（フォント名のみ・最新固定）**。サイトは常に自分の最新版を表示する。
- LGFXScreenBuilder 側はフォントグリッドのタイルと Text の font 選択UIに「詳細 ↗」リンクを置き、
  **新規タブ**（`target=_blank rel=noopener`）で開く。`<BASE>` はツール内の定数1か所で持ち、
  未設定ならリンクを出さない。
- **版差の許容**: ツールが将来 LovyanGFX を更新し、当サイトが旧版のままでも、フォント名は
  安定しているため概ね一致する。サイトに当該名が無ければインデックスへ誘導 or 404 で許容する。
- この契約（URL 形・名前のみ・新規タブ）は LGFXScreenBuilder 側 SPEC にも記載する。

## 7. ディレクトリ構成（想定）

```
LGFXFontCatalog/
  SPEC.ja.md / SPEC.md      # 本仕様
  LICENSE                   # MIT
  NOTICE                    # 帰属（§8）
  .github/workflows/        # 生成＆コミットの GitHub Actions（§3.4）
  generator/                # オフライン生成器（self-contained）
  docs/                     # GitHub Pages 公開物（Actions がコミット）
    index.html              # インデックス（検索・フィルタ）
    fonts/<name>.html       # フォント詳細（収録文字を焼き込み）
    data/index.json         # インデックス用軽量データ
    assets/...              # プレビュー画像など
```
GitHub Pages は `docs/` を公開元にする。生成物コミット方針は §3.4。プレビュー PNG などで
リポジトリが肥大する場合のみ、将来 `gh-pages` ブランチへの分離を検討する。

## 8. ライセンス・帰属

- **生成器およびサイトのコード = MIT**（[LICENSE](LICENSE)、LGFXScreenBuilder と同一）。
- 表示する **グリフ見本・プレビュー画像は LovyanGFX 同梱フォントを描画したもの**で、各フォントは
  それぞれの元ライセンスに従う（FreeFonts/GFX系・efont・M+系・TomThumb など）。`NOTICE` に
  LovyanGFX への帰属と、見本が同梱フォント由来である旨を明記し、LovyanGFX のフォント
  ライセンス記載へリンクする。
- **フォントのバイナリ実体は再配布しない。** 公開するのは描画済み PNG とコードポイント一覧
  （収録の有無という事実情報）のみ。

## 9. 将来拡張（未確定・post-MVP）

- 「文字 → その字を収録しているフォント一覧」の横断検索（インデックスにカバレッジ JSON を同梱
  すれば実現可。当初は付けない）。
- 複数 LovyanGFX バージョンの並行ホストと、§6 の URL へのバージョン付与。
- 各収録文字に LGFX 実描画グリフ画像を併記（重いので任意）。

## 10. 参考実装（LGFXScreenBuilder 側）

以下のファイルの**手法**を移植・流用する（コードのコピーではなく考え方の引き継ぎ）。

- `tests/manual/font_introspect/gen.py` —
  `parse_fonts` / `script_of` / `classify` / `sample_for` / `font_flash_sizes` /
  ピン留めバージョン解決・ヘッダ取得・ダウンロード。フォント表生成。
- `tests/manual/font_introspect/font_introspect.ino` —
  `drawsGlyph`（実描画＋readPixel ＝ 信頼できるカバレッジ判定）/ `detectMono` /
  ASCII・CJK プローブ。**本サイトはここを「全コードポイント列挙」に拡張する**（§3.2）。
- `tests/manual/font_introspect/font_introspect.py` —
  アトラス梱包と `font-metrics.json` 出力（出力フィールドの参考）。
- `docs/src/fonts.js` —
  `HEIGHT_BUCKETS` / `CONTENT_TYPES` / `contentOf` / `filterCatalog` / `sampleFor` /
  `fmtBytes` / `approxCss` / `describe`（facet とラベルの定義）。
- `docs/src/fontsview.js` — フィルタUIとソート（高さ→ファミリ→名前）。
- LGFXScreenBuilder `SPEC.ja.md` / `SPEC.md` の §8.7（フォント戦略）。
