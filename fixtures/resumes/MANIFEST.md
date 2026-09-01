# Synthetic resume fixture corpus

Every name, address, email address, employer, school, and work claim in this corpus is invented solely for testing. No fixture contains real third-party personal data.

| File | RM-TEST-002 c1 case | What it tests | Provenance |
| --- | --- | --- | --- |
| `01-single-column.pdf` | single-column PDF | Conventional linear reading order | Authored synthetic PDF |
| `02-two-column.pdf` | two-column PDF | Column clustering and left-before-right reading order | Authored synthetic PDF |
| `03-table-based.pdf` | table-based PDF | Table cell geometry and reading order | Authored synthetic PDF |
| `04-text-box.pdf` | text-box PDF | Positioned text inside a bordered text box | Authored synthetic PDF |
| `05-multi-page.pdf` | multi-page PDF | Page transition and offsets | Authored synthetic PDF |
| `06-missing-sections.pdf` | missing sections | A resume without education or skills sections | Authored synthetic PDF |
| `07-duplicate-headings.pdf` | duplicate headings | Repeated `Experience` headings | Authored synthetic PDF |
| `08-unusual-headings.pdf` | unusual section headings | Non-standard heading names | Authored synthetic PDF |
| `09-malformed-encoding.pdf` | malformed encoding | Deliberate mojibake text | Authored synthetic PDF |
| `10-image-only.pdf` | image-only PDF | A raster-image page with no PDF text layer | Authored synthetic PDF |
| `11-docx-resume.docx` | DOCX | Paragraphs and a table | Authored synthetic DOCX |
