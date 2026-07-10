# CJK Glyph Availability Notes

Checked on GCP VM (Linux, 2026-07-09).

## cwTeXKai (cwTeX 楷書)

| Glyph | Unicode | Available? |
|-------|---------|:----------:|
| ・ (nakaguro / 中黑) | U+30FB | ❌ **Missing** |
| ． (full-width dot) | U+FF0E | ✅ Available |
| · (middle dot) | U+00B7 | ✅ Available (Latin-1) |

**Fix:** Replace `・` (U+30FB) with `．` (U+FF0E) when generating PDFs with cwTeXKai.
The glyph renders as a small empty box / tofu in the PDF.

## See Also

- `inline-underline-fields.md` — Underlined placeholder field technique
- `fpdf2-cjk-pdf-generation/SKILL.md` — Main CJK PDF skill
