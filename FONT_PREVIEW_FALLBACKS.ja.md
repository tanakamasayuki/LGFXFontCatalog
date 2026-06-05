# フォントプレビュー代替フォント一覧

LovyanGFX のフォントファミリーについて、ファミリー名から推定できる WebFont 候補と、名前だけでは分かりにくい標準ビットマップフォントの画像ベース分類をまとめる。

| family | 判定 | 推奨描画 | WebFont 候補 | 根拠 |
|---|---|---|---|---|
| `DejaVu` | DejaVu Sans 系サンセリフ | normal webfont | `DejaVu Sans`, `Noto Sans`, `Arial` | ファミリー名から DejaVu 系。WebFont として DejaVu を同梱できるならそれが最も近い。 |
| `FreeMono` | GNU FreeFont モノスペース | normal webfont | `Cousine`, `Roboto Mono`, `Courier New` | FreeMono は Courier 系のモノスペース。Web では Cousine が実用的。 |
| `FreeSans` | GNU FreeFont サンセリフ | normal webfont | `Arimo`, `Noto Sans`, `Arial` | FreeSans は Helvetica/Arial 系。 |
| `FreeSerif` | GNU FreeFont セリフ | normal webfont | `Tinos`, `Noto Serif`, `Times New Roman` | FreeSerif は Times 系。 |
| `Orbitron_Light` | 幾何学的ディスプレイフォント | normal webfont | `Orbitron` weight 300 | 名前通り Orbitron Light。 |
| `Roboto_Thin` | 細ウェイトサンセリフ | normal webfont | `Roboto` weight 100 | 名前通り Roboto Thin。 |
| `Satisfy` | スクリプト体 | normal webfont | `Satisfy` | 名前通り Satisfy。 |
| `Yellowtail` | スクリプト体 | normal webfont | `Yellowtail` | 名前通り Yellowtail。 |
| `efontCN` | 簡体字 CJK ビットマップ系 | normal webfont | `Noto Sans SC`, `Microsoft YaHei` | efont 中国語系。WebFont では文字種カバー優先で Noto Sans SC、ビットマップ感は再現しない。 |
| `efontJA` | 日本語 CJK ビットマップ系 | normal webfont | `Noto Sans JP`, `M PLUS 1p` | efont 日本語系。WebFont では文字種カバー優先。 |
| `efontKR` | 韓国語 CJK ビットマップ系 | normal webfont | `Noto Sans KR`, `Malgun Gothic` | efont 韓国語系。WebFont では文字種カバー優先。 |
| `efontTW` | 繁体字 CJK ビットマップ系 | normal webfont | `Noto Sans TC`, `Microsoft JhengHei` | efont 台湾繁体字系。WebFont では文字種カバー優先。 |
| `lgfxJapanGothic` | 日本語ゴシック | normal webfont | `M PLUS 1p`, `Noto Sans JP` | ファミリー名から日本語ゴシック。M PLUS 系に寄せるのが実用的。 |
| `lgfxJapanGothicP` | 日本語プロポーショナルゴシック | normal webfont | `M PLUS 1p`, `Noto Sans JP` | `P` 付きのプロポーショナル版。 |
| `lgfxJapanMincho` | 日本語明朝 | normal webfont | `Noto Serif JP`, `Yu Mincho` | ファミリー名から日本語明朝。 |
| `lgfxJapanMinchoP` | 日本語プロポーショナル明朝 | normal webfont | `Noto Serif JP`, `Yu Mincho` | `P` 付きのプロポーショナル版。 |
| `Font0` | 小型 6x8 GLCD 風ビットマップサンセリフ | pixel webfont | `Pixelify Sans`, `DotGothic16`, `monospace` | 画像上は極小の固定幅系 LCD UI フォント。ソース上は `GLCDfont Font0`。 |
| `Font2` | 中型ビットマップサンセリフ | pixel webfont | `Pixelify Sans`, `DotGothic16`, `monospace` | 画像上は組み込み LCD 風。完全一致 WebFont よりピクセル系で近似。 |
| `Font4` | 大型ビットマップサンセリフ | pixel webfont | `Pixelify Sans`, `DotGothic16`, `monospace` | 画像上は `Font2` を大きくしたような丸み少なめの組み込み UI 文字。 |
| `Font6` | 丸みのある LCD 数字・時計用 | custom canvas / DSEG fallback | `DSEG7 Classic` | ソースコメントに「numbers and time」用途、収録文字は数字・コロン・マイナス・ドット・`a/p/m` 等。画像は7セグより丸い LCD 数字。 |
| `Font7` | 7セグ数字・時計用 | custom canvas / DSEG fallback | `DSEG7 Classic` | ソースコメントに「7 segment font intended to display numbers and time」。 |
| `Font8` | 大型 Arial 系数字 | normal webfont | `Arial`, `Helvetica Neue`, `sans-serif` | ソースコメントに「Arial 75 pixel height font intended to display large numbers」。 |
| `Font8x8C64` | Commodore 64 風 8x8 ビットマップ | pixel webfont | `C64 Pro Mono`, `Pixelify Sans`, `monospace` | ソースコメントが `https://github.com/hugovangalen/C64_Font8x8` を original source としている。 |
| `AsciiFont8x16` | 固定幅 8x16 端末ビットマップ | pixel webfont | `Web437 IBM VGA 8x16`, `Perfect DOS VGA 437`, `monospace` | 画像上は VGA/DOS 端末風の固定幅ビットマップ。 |
| `AsciiFont24x48` | 固定幅 24x48 端末ビットマップ | pixel webfont | `Web437 IBM VGA 8x16`, `Perfect DOS VGA 437`, `monospace` | `AsciiFont8x16` を大型化したような端末系ビットマップ。 |
| `TomThumb` | 極小ビットマップセリフ | TomThumb webfont / pixel webfont | `Tom Thumb`, `Pixelify Sans`, `monospace` | LovyanGFX に `TomThumb.h` として同梱される既知 GFX フォント。可能なら TomThumb 自体を WebFont 化するのが最も近い。 |

実装方針:

- `recommendedRenderer: "webFont"` は通常の `ctx.font` で描画する。
- `recommendedRenderer: "pixelWebFont"` は WebFont で近似しつつ、必要なら `imageSmoothingEnabled = false` や整数座標配置でビットマップ感を保つ。
- `recommendedRenderer: "sevenSegmentCanvas"` は `fillText()` より専用 Canvas 描画の方が近い。数字・コロン・ドット・マイナス中心なので、セグメント幅、角丸、傾き、文字間隔をパラメータ化すると再現しやすい。
