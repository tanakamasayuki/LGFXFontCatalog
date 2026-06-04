#include <LovyanGFX.hpp>
#include <LGFX_AUTODETECT.hpp>
#include "fonts_table.h"

#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <string.h>

using lgfx::v1::FontMetrics;
using lgfx::v1::IFont;

static LGFX_Sprite canvas;
static const int kCanvasW = 760;
static const int kCanvasH = 160;

static int utf8(char *out, uint32_t cp)
{
  if (cp <= 0x7F) {
    out[0] = (char)cp; out[1] = 0; return 1;
  }
  if (cp <= 0x7FF) {
    out[0] = (char)(0xC0 | (cp >> 6));
    out[1] = (char)(0x80 | (cp & 0x3F));
    out[2] = 0; return 2;
  }
  out[0] = (char)(0xE0 | (cp >> 12));
  out[1] = (char)(0x80 | ((cp >> 6) & 0x3F));
  out[2] = (char)(0x80 | (cp & 0x3F));
  out[3] = 0; return 3;
}

static int advanceOf(const IFont *font, const FontMetrics &base, uint16_t c)
{
  FontMetrics t = base;
  if (!font->updateFontMetric(&t, c)) return -1;
  return (int)t.x_advance;
}

static bool drawsText(const IFont *font, const char *s)
{
  canvas.fillScreen(TFT_BLACK);
  canvas.setFont(font);
  canvas.setTextColor(TFT_WHITE, TFT_BLACK);
  canvas.setTextSize(1);
  canvas.setCursor(0, 0);
  canvas.print(s);
  int w = canvas.textWidth(s);
  int h = canvas.fontHeight();
  if (w <= 0) w = 8;
  if (w > kCanvasW) w = kCanvasW;
  if (h <= 0 || h > kCanvasH) h = kCanvasH;
  for (int y = 0; y < h; ++y) {
    for (int x = 0; x < w; ++x) {
      if (canvas.readPixel(x, y)) return true;
    }
  }
  return false;
}

static bool drawsCodepoint(const IFont *font, uint16_t cp)
{
  if (cp == 0x20 || cp == 0x3000) {
    FontMetrics m;
    font->getDefaultMetric(&m);
    return advanceOf(font, m, cp) > 0;
  }
  char s[4];
  utf8(s, cp);
  return drawsText(font, s);
}

static int detectMono(const IFont *font, const FontMetrics &base)
{
  int ai = advanceOf(font, base, 'i');
  int aw = advanceOf(font, base, 'W');
  if (ai > 0 && aw > 0) return ai == aw ? 1 : 0;
  static const uint16_t wide[] = { 0x65E5, 0x3042, 0xD55C, 0xAC00 };
  int first = -1;
  for (size_t i = 0; i < sizeof(wide) / sizeof(wide[0]); ++i) {
    int a = advanceOf(font, base, wide[i]);
    if (a <= 0) continue;
    if (first < 0) first = a;
    else if (a != first) return 0;
  }
  return first > 0 ? 1 : -1;
}

static bool savePngCrop(const char *path, int w, int h)
{
  if (w <= 0) w = 1;
  if (h <= 0) h = 1;
  if (w > kCanvasW) w = kCanvasW;
  if (h > kCanvasH) h = kCanvasH;
  size_t len = 0;
  void *png = canvas.createPng(&len, 0, 0, w, h);
  if (!png || len == 0) return false;
  FILE *fp = fopen(path, "wb");
  bool ok = false;
  if (fp) {
    ok = fwrite(png, 1, len, fp) == len;
    fclose(fp);
  }
  free(png);
  return ok;
}

static void renderSample(const IFont *font, const char *sample, const char *path, const FontMetrics &m)
{
  canvas.fillScreen(TFT_BLACK);
  canvas.setFont(font);
  canvas.setTextColor(TFT_WHITE, TFT_BLACK);
  canvas.setTextSize(1);
  canvas.setCursor(0, 0);
  canvas.print(sample);
  int tw = canvas.textWidth(sample) + 2;
  int th = m.height > 0 ? m.height + 2 : canvas.fontHeight() + 2;
  savePngCrop(path, tw, th);
}

void setup()
{
  Serial.begin(115200);
  Serial.println("TEST start font_catalog_probe");
  mkdir("output", 0755);
  mkdir("output/assets", 0755);

  canvas.setColorDepth(16);
  canvas.setPsram(false);
  if (!canvas.createSprite(kCanvasW, kCanvasH)) {
    Serial.println("FATAL createSprite failed");
    return;
  }

  FILE *meta = fopen("output/metrics.jsonl", "wb");
  FILE *cov = fopen("output/coverage.jsonl", "wb");
  if (!meta || !cov) {
    Serial.println("FATAL output files");
    return;
  }

  size_t limit = kFontCount;
  const char *limitEnv = getenv("LGFX_FONT_CATALOG_LIMIT");
  if (limitEnv && atoi(limitEnv) > 0 && (size_t)atoi(limitEnv) < limit) {
    limit = (size_t)atoi(limitEnv);
  }

  for (size_t i = 0; i < limit; ++i) {
    const FontEntry &e = kFonts[i];
    const IFont *font = e.font;
    FontMetrics m;
    font->getDefaultMetric(&m);

    bool letters = drawsText(font, "ABC");
    bool digits = drawsText(font, "0123456789");
    const char *brief = (!letters && digits) ? "0123456789" : e.brief;
    const char *rich = (!letters && digits) ? "0123456789 12:34:56 -." : e.rich;

    char briefPath[180];
    char richPath[180];
    snprintf(briefPath, sizeof(briefPath), "output/assets/%s-brief.png", e.name);
    snprintf(richPath, sizeof(richPath), "output/assets/%s-rich.png", e.name);
    renderSample(font, brief, briefPath, m);
    renderSample(font, rich, richPath, m);

    int mono = detectMono(font, m);
    const char *monoStr = mono == 1 ? "true" : mono == 0 ? "false" : "null";
    fprintf(meta,
            "{\"name\":\"%s\",\"height\":%d,\"baseline\":%d,\"xAdvance\":%d,"
            "\"yAdvance\":%d,\"width\":%d,\"mono\":%s,\"letters\":%s,\"digits\":%s,"
            "\"brief\":\"assets/%s-brief.png\",\"rich\":\"assets/%s-rich.png\"}\n",
            e.name, (int)m.height, (int)m.baseline, (int)m.x_advance,
            (int)m.y_advance, (int)m.width, monoStr,
            letters ? "true" : "false", digits ? "true" : "false",
            e.name, e.name);

    fprintf(cov, "{\"name\":\"%s\",\"codepoints\":[", e.name);
    bool first = true;
    for (uint32_t cp = 0; cp <= 0xFFFF; ++cp) {
      if (cp >= 0xD800 && cp <= 0xDFFF) continue;
      FontMetrics t = m;
      if (!font->updateFontMetric(&t, (uint16_t)cp)) continue;
      if (!drawsCodepoint(font, (uint16_t)cp)) continue;
      if (!first) fputc(',', cov);
      fprintf(cov, "%u", (unsigned)cp);
      first = false;
    }
    fprintf(cov, "]}\n");

    Serial.printf("PROGRESS %u/%u %s\n", (unsigned)(i + 1), (unsigned)limit, e.name);
  }

  fclose(meta);
  fclose(cov);
  Serial.printf("DONE fonts=%u\n", (unsigned)limit);
  Serial.println("TEST done");
}

void loop() { delay(1000); }
