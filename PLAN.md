# Question Bank Extraction Plan

Goal: get every MCQ out of the scanned PDFs and into Excel, organised by subject and chapter. Each row holds the question, its options, the correct option and the explanation, all transcribed **exactly as printed**. The pipeline must take in new PDFs as they are added to the repo.

---

## 1. What the source looks like (findings)

| Item | Finding | Impact |
|---|---|---|
| Format | `Microsoft: Print To PDF` of **scanned pages**. **No text layer** (`pdftotext` gives an empty result). Each page is stitched from ~36 JPEG strips at 300 ppi. | Needs OCR / vision transcription. Text cannot be copied directly. |
| Book | Civil Engineering objective book. 18 chapters plus Appendix A and B (contents on PDF p.1 of `1-92.pdf`). | Chapters are known up front, so we can build a fixed chapter map. |
| Layout | 2 columns, with a slight skew and **bleed from the neighbouring page** at the left/right edge. | Each page must be cropped to its own page area. Bleed text must be ignored. |
| Question markers | `*` before the number = explanation is in Appendix B. `[ES 99]` = exam/year tag. | Capture both as columns. |
| Answers | **Handwritten** letters in the left margin (a/b/c/d). The book note says: *"See Appendix B for explanation to the answer given in Appendix A."* So the **official key is Appendix A** (book p.479+). | Official answer comes from Appendix A. The handwritten mark is kept as a second signal and cross-checked. |
| Content types | Plain MCQ, Assertion–Reason, "Consider the following statements", Match List I/II with code tables, formulas (fractions, Greek letters, superscripts), some figures. | Needs per-type formatting rules (§4). |
| Files | `Civil/1-92.pdf` (92 pp), `Civil/93-179.pdf` (87 pp), `Civil/180-281.pdf` (102 pp), **`Civil/282-392.pdf` = 0 bytes (empty/corrupt upload)**. | ⚠ The file must be re-uploaded. Book pages 282–392 and **Appendix A/B (p.479–495+)** are missing, so there is no official key or explanations yet. |

PDF page → book page offsets (sampled): `1-92.pdf` p.N → book p.N-1. `93-179.pdf` p.50 → book p.141. The exact offset will be recorded per file in the manifest.

---

## 2. Output

```
output/
  Civil/
    Civil_QuestionBank.xlsx      # one workbook per subject
  _ALL_Subjects.xlsx             # optional master (all subjects, filterable)
  review/Civil_review.xlsx       # only rows flagged for human check
```

**Workbook per subject** contains:
- `Index` sheet: chapter no, chapter name, question count, starred count, answered %, flagged count.
- **One sheet per chapter**, e.g. `01 Fluid Mechanics`, `02 Surveying`, …
- `All` sheet: every chapter stacked, with an autofilter.

**Columns (every chapter sheet):**

| Col | Field | Notes |
|---|---|---|
| A | Subject | Civil |
| B | Chapter No | 1 |
| C | Chapter | Fluid Mechanics |
| D | Q No | Printed number |
| E | Starred | Y if `*` |
| F | Question | Exact text: line breaks kept for statements and lists |
| G–J | Option a / b / c / d | Exact text |
| K | (Option e / extra) | Rare; empty otherwise |
| L | Correct Option | Letter from **Appendix A** |
| M | Correct Option Text | Copied from G–J |
| N | Explanation | From **Appendix B** (starred Qs only), exact |
| O | Exam Tag | e.g. `ES 99` |
| P | Handwritten Mark | Letter written in the margin |
| Q | Key Match | `OK` / `MISMATCH` / `NO_KEY` |
| R | Has Figure/Table | Y + the image is embedded in the cell or linked |
| S | Source File | `Civil/1-92.pdf` |
| T | PDF Page / Book Page | `2 / 1` |
| U | Confidence | `HIGH` / `CHECK` |
| V | Notes | Why it was flagged |

---

## 3. Pipeline

```
scripts/
  manifest.py      # hash + detect new/changed PDFs → manifest.json
  render.py        # pdf → 300-dpi page PNGs (pdftoppm), deskew, crop out bleed
  transcribe.py    # vision model → structured JSON per page (pass A & pass B)
  reconcile.py     # diff A vs B, third pass on disagreements
  stitch.py        # join Qs split across columns/pages, assign chapters
  appendix.py      # parse Appendix A (keys) + B (explanations), join by chapter+Qno
  validate.py      # all checks in §5 → confidence flags
  build_excel.py   # openpyxl → workbooks in §2
data/
  pages/<subject>/<file>/<page>.png
  json/<subject>/<file>/<page>.A.json / .B.json / .final.json
  chapters.yaml    # chapter map per subject (name, start book page)
manifest.json      # sha256, pages, offset, status per PDF
```

**Steps:**

1. **Ingest.** Scan `*/*.pdf` (top folder = subject). Skip 0-byte or corrupt files and report them. Compare SHA-256 with `manifest.json` so that only new or changed files are processed. **This makes adding PDFs incremental.**
2. **Render.** 300 dpi PNG per page (native resolution, no upscaling loss). Deskew. Detect the page frame and crop away the neighbouring-page bleed.
3. **Transcribe** with a vision model (Claude), one page at a time, using a strict JSON schema: `{q_no, starred, question, options{a..d}, exam_tag, handwritten_mark, has_figure, continues_from_prev, continues_to_next}`. The prompt rule is **verbatim, do not correct spelling or grammar, do not solve**.
4. **Double transcription.** Run two independent passes (A and B, at different crops/temperature). Compare them field by field, after normalising whitespace only. Where they disagree, run pass C on a zoomed crop of that question; 2-of-3 agreement wins. If there is still no agreement, set `CHECK`.
5. **Stitch.** Merge questions that run across a column or page boundary. Assign chapters from the chapter headers plus `chapters.yaml`.
6. **Appendix.** Transcribe Appendix A (chapter → Q no → letter) and Appendix B (chapter → Q no → explanation) the same way. Join them onto the questions.
7. **Validate** (§5), then **Build Excel**.
8. Commit `output/` plus `manifest.json`. Re-running the pipeline is idempotent.

Why a vision LLM instead of Tesseract: the pages are skewed scans that contain formulas, fractions, Greek letters, match-tables and handwriting. Tesseract garbles math and misses the margin marks. The vision model, combined with two passes and an arbitration pass, gives far higher accuracy, and every disagreement is surfaced instead of being guessed.

---

## 4. "Exactly as printed" rules

- Text is kept verbatim, including the book's typos. Only the line-break hyphenation inside a word is joined (`tempe-rature` → `temperature`). This is configurable if the hyphen should be kept.
- Math uses Unicode: `m²`, `N/cm²`, `σ`, `γ`, `θ`, `√`, `π`. Stacked fractions are written inline as `(2σ)/(rγ)`. The original is preserved in a `*_latex` hidden column if needed.
- Statements `i) ii) iii)` / `1. 2. 3.` stay on their own lines within the Question cell.
- **Match List I/II**: both lists go into the Question cell as aligned lines (`A. Wire claw — 1. to clean the ballast`). Option cells hold the codes (`A-1, B-3, C-2, D-4`).
- Assertion–Reason: `Assertion A: …` / `Reason R: …` are kept on separate lines.
- Figures and diagram options: the region is cropped to PNG, embedded in the row, and `Has Figure` is set to Y.

---

## 5. Accuracy controls (for high confidence)

| Check | Rule → flag |
|---|---|
| Numbering | Q numbers in each chapter are continuous 1…N, with no gaps or duplicates |
| Options | Exactly 4 options (a–d); none empty |
| Two-pass agreement | Every field identical after normalisation, else arbitrate |
| Key coverage | Every Q has an Appendix A key; every `*` Q has an Appendix B explanation |
| Key vs handwriting | Appendix A ≠ handwritten mark → `MISMATCH` (one of them is wrong; worth a human look) |
| Bleed leak | Text from the neighbouring page (cut-off words at the edge) is rejected |
| Chapter totals | Count per chapter is compared with the last Q number on the chapter's final page |
| Spot audit | Random 5% of `HIGH` rows plus 100% of `CHECK` rows are compared against the page image. The audit sheet holds a thumbnail beside the text. |

The target is 0 unresolved `CHECK` rows before the file is marked final.

---

## 6. Adding new PDFs

1. Drop PDFs into a subject folder (`Civil/`, `Mechanical/`, …), keeping the page-range naming (`282-392.pdf`).
2. Run `python scripts/run_all.py` (later this can be a GitHub Action on push). Only new files are processed. The workbooks are rebuilt with the new chapters and rows. Existing rows stay unchanged unless their source PDF hash changed.
3. A new subject (new folder) needs a `chapters.yaml` entry. This can be auto-drafted from the book's Contents page.

---

## 7. Phases

| Phase | Work | Output |
|---|---|---|
| 0 | Fix inputs: re-upload `282-392.pdf`; add Appendix A/B pages | Complete source |
| 1 | Pilot: Ch 1 Fluid Mechanics (~1–51) end to end | `Civil_QuestionBank.xlsx` with 1 sheet + audit, for your sign-off on format |
| 2 | Remaining chapters in the available files (Ch 1–10 partial) | Full sheets, answer column empty until Appendix A arrives (handwritten mark filled) |
| 3 | Appendix A/B parse + join | Correct option + explanations filled |
| 4 | Automate the incremental runner (+ optional GitHub Action) | Hands-off for new PDFs |

---

## 8. Decisions needed from you

1. **Correct option source** when Appendix A is unavailable: use the handwritten margin mark (flagged `UNVERIFIED`), or leave it blank?
2. Formulas: **Unicode inline** (recommended, readable in Excel) or LaTeX?
3. Keep the `[ES 99]` exam tag inside the question text too, or only in its own column?
4. Should a figure be **embedded as an image** in Excel (recommended) or saved as a separate file with a link?
5. Re-upload `Civil/282-392.pdf` (currently 0 bytes) and the Appendix pages.
