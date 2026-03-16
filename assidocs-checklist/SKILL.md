---
name: assidocs-checklist
description: >
  Create professional Korean-language analysis reports and checklist documents in .docx format
  using AIF (AI Factory) brand styling. Use this skill whenever the user asks to create an
  "issue analysis report", "checklist document", "post-mortem", "improvement task list",
  "운영 분석 보고서", "체크리스트 문서", "이슈 분석", "재발방지 보고서", or any structured
  document that combines: issue breakdown, root cause analysis (원인), response summary (대응),
  prevention proposals (재발방지), and actionable checklists. Also trigger when the user asks
  to "make a document like this one" after producing an assidocs-style report. Outputs a
  polished .docx with brand-consistent styling (Navy/Purple/Orange palette), section boxes,
  labeled issue tables, phase-based checklists with owner/complete columns, and a priority
  summary table.
---

# AssIDocs Checklist Skill

Creates structured Korean analysis + checklist `.docx` documents in AIF brand style.

## When to Use

- Post-mortem / 사후 분석 reports (시스템 장애, 대회 운영, 프로젝트 완료)
- 이슈 분석 + 원인/대응/재발방지 3-layer documents
- 체크리스트 문서 with owner columns and phase structure
- Any report combining "what went wrong → what we did → what to do next"

---

## Step 1: Read the docx skill

Before writing any code, always read the docx skill for syntax reference:

```
/mnt/skills/public/docx/SKILL.md
```

---

## Step 2: Document Structure

Every assidocs-checklist document follows this 4-section structure:

```
[Title Page]
  └─ Document title (Korean, large)
  └─ Subtitle (scope/data source)
  └─ Stat Badge Row (key metrics as colored boxes)

[Section 1: Issue Overview]
  └─ 4-layer issue structure table (color-coded left border strips)

[Section 2: Issue Detail Analysis]
  └─ Per-issue blocks (heading2 + heading3 pattern):
      └─ 원인 (callout box)
      └─ 대응 과정 (bullet list or detail table)
      └─ 재발방지 제안 (sectionBox with checklist items)

[Section 3: Pre-Launch Checklist]
  └─ Phase A / B / C tables (with #, 항목, 담당, 완료 columns)

[Section 4: Priority Summary]
  └─ P0~P3 priority table (우선순위, 과제, 임팩트, 예상 공수)
```

---

## Step 3: Brand Colors & Styles

```javascript
// Core palette — use these constants exactly
const BRAND_PURPLE = '7B3FFF';   // AIF primary
const NAVY        = '1E2D5A';   // headings, table headers
const ORANGE      = 'E87722';   // warnings, capacity issues
const RED         = 'D32F2F';   // critical issues, P0
const GREEN       = '2E7D32';   // P3 / low priority
const AMBER       = 'F57C00';   // caution callouts
const WHITE       = 'FFFFFF';
const LIGHT_GRAY  = 'F5F5F5';   // alternating table row
const DARK_TEXT   = '1A1A1A';   // body text

// Tinted backgrounds (for bordered sections, never use alpha)
const RED_BG    = 'FFE8E8';
const ORANGE_BG = 'FFF3E0';
const PURPLE_BG = 'F3E5F5';
const NAVY_BG   = 'E8EAF6';
const AMBER_BG  = 'FFF8E1';
```

---

## Step 4: Reusable UI Patterns

See `references/patterns.md` for full code snippets. Summary:

| Pattern | Purpose | Key params |
|---|---|---|
| `heading1(text)` | Section title with purple underline border | — |
| `heading2(text, color)` | Issue title, color = severity color | NAVY default |
| `heading3(text)` | Sub-section label (원인/대응/재발방지) | — |
| `body(text, opts)` | Normal paragraph | bold, italic opts |
| `bullet(text)` | Bullet list item | uses numbering ref |
| `space(n)` | Vertical spacer | lines count |
| `calloutBox(icon, text, bgColor, borderColor)` | Highlighted callout (원인 summary, quotes) | icon = '!' or '"' |
| `sectionBox(title, bgColor, rows[])` | Checklist/prevention items list | dark header + light rows |
| `issueLayerTable(layers[])` | 4-layer overview table | left color border strip |
| `statBadgeRow(badges[])` | Top stats (colored count boxes) | array of {label, count, color} |
| `threeColTable(headers, rows, widths)` | General data table | Navy header, alternating rows |
| `checklistTable(headerColor, rows[])` | Phase checklist | #, 항목, 담당, ☐ columns |
| `priorityTable(rows[])` | P0~P3 priority summary | Navy header |

---

## Step 5: Document Setup

```javascript
const doc = new Document({
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 20 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal',
        run: { size: 28, bold: true, font: 'Arial' },
        paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal',
        run: { size: 24, bold: true, font: 'Arial' },
        paragraph: { spacing: { before: 280, after: 100 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal',
        run: { size: 22, bold: true, font: 'Arial' },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },   // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [ /* content */ ]
  }]
});
```

---

## Step 6: Critical Rules

- **NEVER use alpha in hex colors** (e.g., `'D32F2F18'` is invalid — use `'FFE8E8'` for tinted bg)
- **Always set both `columnWidths` on Table AND `width` on each TableCell** (DXA only)
- **Never use `\n`** — use separate `Paragraph` elements
- **Never use unicode bullets** — use `LevelFormat.BULLET` with numbering config
- **`ShadingType.CLEAR` always**, never SOLID (causes black backgrounds)
- **PageBreak must be inside a Paragraph**
- **All sizes in DXA**: content width A4 with 1-inch margins = 9026 DXA ≈ use 9360 for safe rounding

---

## Step 7: Output & Validation

```bash
# Save output
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/claude/output.docx', buf);
});

# Validate (run after generation)
python3 /mnt/skills/public/docx/scripts/office/validate.py /home/claude/output.docx

# Copy to outputs
cp /home/claude/output.docx "/mnt/user-data/outputs/[한국어파일명].docx"
```

Then call `present_files` with the output path.

---

## Content Guidelines

### 원인 섹션
- Lead with a `calloutBox('!', ..., AMBER_BG, AMBER)` for the root cause summary
- Follow with a detail table if multiple contributing factors exist
- Be specific: quote actual system names, error codes, dates

### 재발방지 섹션
- Use `sectionBox(title, NAVY, items[])` with `[ ]` prefix on each item
- Items should be actionable, assignable, and testable
- Group into A/B/C phases for the integrated checklist

### Priority Table
- P0 = 🔴 immediate, no-cost fixes (config, policy docs)
- P1 = 🟠 high impact, moderate effort (feature additions)
- P2 = 🟡 medium impact (documentation, process)
- P3 = 🟢 nice-to-have (infra improvements)
- Always include 임팩트 + 예상 공수 columns

### Footer
- Always add a footer note paragraph with source description:
  `본 문서는 [데이터 출처] 분석하여 작성되었습니다. | 인공지능팩토리`

---

## Reference Files

- `references/patterns.md` — Full JavaScript helper function implementations
- `references/example-structure.md` — Annotated content outline from the inference stability report
