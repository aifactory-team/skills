# AssIDocs Checklist — UI Pattern Implementations

Full JavaScript helper functions for use in the document generation script.
Copy these into your `.js` file after the color constant declarations.

---

## Dependencies

```javascript
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign, LevelFormat, PageBreak
} = require('docx');
const fs = require('fs');
```

---

## Border Helpers

```javascript
const cellBorder = (color = 'CCCCCC') => ({
  top:    { style: BorderStyle.SINGLE, size: 1, color },
  bottom: { style: BorderStyle.SINGLE, size: 1, color },
  left:   { style: BorderStyle.SINGLE, size: 1, color },
  right:  { style: BorderStyle.SINGLE, size: 1, color },
});

const noBorder = {
  top:    { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
  bottom: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
  left:   { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
  right:  { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
};
```

---

## Typography Helpers

```javascript
function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BRAND_PURPLE, space: 4 } },
    children: [new TextRun({ text, font: 'Arial', size: 28, bold: true, color: NAVY })],
  });
}

function heading2(text, color = NAVY) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 100 },
    children: [new TextRun({ text, font: 'Arial', size: 24, bold: true, color })],
  });
}

function heading3(text, color = DARK_TEXT) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, font: 'Arial', size: 22, bold: true, color })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: 'Arial', size: 20, color: DARK_TEXT, ...opts })],
  });
}

function bullet(text, bold = false) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, font: 'Arial', size: 20, bold, color: DARK_TEXT })],
  });
}

function space(lines = 1) {
  return new Paragraph({
    spacing: { before: 0, after: lines * 100 },
    children: [new TextRun('')],
  });
}
```

---

## Callout Box

Used for: 원인 root cause summary, participant quotes, warnings.

```javascript
// icon: '!' for warning, '"' for quote
// bgColor/borderColor: use AMBER_BG/AMBER for caution, RED_BG/RED for critical,
//                      PURPLE_BG/BRAND_PURPLE for info quotes
function calloutBox(icon, text, bgColor, borderColor) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [600, 8760],
    rows: [new TableRow({
      children: [
        new TableCell({
          width: { size: 600, type: WidthType.DXA },
          shading: { fill: bgColor, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 100, right: 80 },
          borders: {
            top:    { style: BorderStyle.SINGLE, size: 4, color: borderColor },
            bottom: { style: BorderStyle.SINGLE, size: 4, color: borderColor },
            left:   { style: BorderStyle.SINGLE, size: 4, color: borderColor },
            right:  { style: BorderStyle.NONE,   size: 0, color: 'FFFFFF' },
          },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: icon, font: 'Arial', size: 22, bold: true, color: borderColor })]
          })]
        }),
        new TableCell({
          width: { size: 8760, type: WidthType.DXA },
          shading: { fill: bgColor, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 160, right: 120 },
          borders: {
            top:    { style: BorderStyle.SINGLE, size: 4, color: borderColor },
            bottom: { style: BorderStyle.SINGLE, size: 4, color: borderColor },
            left:   { style: BorderStyle.NONE,   size: 0, color: 'FFFFFF' },
            right:  { style: BorderStyle.SINGLE, size: 4, color: borderColor },
          },
          children: [new Paragraph({
            children: [new TextRun({ text, font: 'Arial', size: 19, color: DARK_TEXT })]
          })]
        }),
      ]
    })]
  });
}
```

---

## Section Box (재발방지 / Checklist Items)

Dark colored header + light gray rows. Used for 재발방지 item lists.

```javascript
// bgColor: use NAVY for 재발방지, ORANGE for 용량, BRAND_PURPLE for 환경안내, etc.
// rows: string array — prefix each item with '[ ]' for actionable checklist style
function sectionBox(title, bgColor, rows) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [
      new TableRow({ children: [
        new TableCell({
          width: { size: 9360, type: WidthType.DXA },
          shading: { fill: bgColor, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 160, right: 120 },
          borders: cellBorder(bgColor),
          children: [new Paragraph({ children: [
            new TextRun({ text: title, font: 'Arial', size: 20, bold: true, color: WHITE })
          ]})]
        })
      ]}),
      ...rows.map(row => new TableRow({ children: [
        new TableCell({
          width: { size: 9360, type: WidthType.DXA },
          shading: { fill: LIGHT_GRAY, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 160, right: 120 },
          borders: cellBorder('DDDDDD'),
          children: [new Paragraph({
            spacing: { before: 40, after: 40 },
            children: [new TextRun({ text: row, font: 'Arial', size: 19, color: DARK_TEXT })]
          })]
        })
      ]}))
    ]
  });
}
```

---

## Issue Layer Overview Table

4-row table showing the issue structure layers with left-side color accent border.

```javascript
// layers: array of { label, color, bgColor, description }
// Example colors: RED/'FFE8E8', ORANGE/'FFF3E0', BRAND_PURPLE/'F3E5F5', NAVY/'E8EAF6'
function issueLayerTable(layers) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: layers.map(({ label, color, bgColor, description }) => new TableRow({
      children: [new TableCell({
        width: { size: 9360, type: WidthType.DXA },
        shading: { fill: bgColor, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 160, right: 120 },
        borders: {
          top:    { style: BorderStyle.NONE },
          bottom: { style: BorderStyle.SINGLE, size: 1, color: 'DDDDDD' },
          left:   { style: BorderStyle.SINGLE, size: 6, color },
          right:  { style: BorderStyle.NONE },
        },
        children: [
          new Paragraph({ spacing: { before: 0, after: 30 }, children: [
            new TextRun({ text: label, font: 'Arial', size: 20, bold: true, color })
          ]}),
          new Paragraph({ spacing: { before: 0, after: 0 }, children: [
            new TextRun({ text: description, font: 'Arial', size: 19, color: DARK_TEXT })
          ]}),
        ]
      })]
    }))
  });
}
```

---

## Stat Badge Row (Title Page Metrics)

Colored boxes displaying key numeric metrics on the title page.

```javascript
// badges: array of { label, count, color }
// Standard colors: ORANGE, RED, BRAND_PURPLE, NAVY
// Count goes large (size 40), label below (size 17), both WHITE
function statBadgeRow(badges) {
  const width = Math.floor(9360 / badges.length);
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: badges.map(() => width),
    rows: [new TableRow({
      children: badges.map(({ label, count, color }) => new TableCell({
        width: { size: width, type: WidthType.DXA },
        shading: { fill: color, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 120, right: 120 },
        borders: {
          top:    { style: BorderStyle.NONE },
          bottom: { style: BorderStyle.NONE },
          left:   { style: BorderStyle.SINGLE, size: 2, color: WHITE },
          right:  { style: BorderStyle.SINGLE, size: 2, color: WHITE },
        },
        children: [
          new Paragraph({ alignment: AlignmentType.CENTER, children: [
            new TextRun({ text: count, font: 'Arial', size: 40, bold: true, color: WHITE })
          ]}),
          new Paragraph({ alignment: AlignmentType.CENTER, children: [
            new TextRun({ text: label, font: 'Arial', size: 17, color: WHITE })
          ]}),
        ]
      }))
    })]
  });
}
```

---

## Three-Column Data Table

General purpose data table with Navy header and alternating rows.

```javascript
// widths must sum to 9360
function threeColTable(headers, rows, widths = [3120, 3120, 3120]) {
  const headerRow = new TableRow({ children: headers.map((h, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    borders: cellBorder(NAVY),
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: h, font: 'Arial', size: 19, bold: true, color: WHITE })
    ]})]
  }))});

  const dataRows = rows.map((row, ri) => new TableRow({ children: row.map((cell, ci) => new TableCell({
    width: { size: widths[ci], type: WidthType.DXA },
    shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    borders: cellBorder('DDDDDD'),
    children: [new Paragraph({ children: [
      new TextRun({ text: cell, font: 'Arial', size: 18, color: DARK_TEXT })
    ]})]
  }))}));

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...dataRows]
  });
}
```

---

## Checklist Table (Phase A/B/C)

4-column table: #, 항목, 담당, ☐  
Use for Section 3 phase-by-phase checklists.

```javascript
// headerColor: use NAVY for A, ORANGE for B, BRAND_PURPLE for C
// rows: array of [num, item, owner, '☐']
function checklistTable(headerColor, rows) {
  const widths = [600, 6560, 1200, 1000];
  const headers = ['#', '체크 항목', '담당', '완료'];

  const headerRow = new TableRow({ children: headers.map((h, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: { fill: headerColor, type: ShadingType.CLEAR },
    borders: cellBorder(headerColor),
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: i === 0 || i >= 2 ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: [new TextRun({ text: h, font: 'Arial', size: 18, bold: true, color: WHITE })]
    })]
  }))});

  const dataRows = rows.map(([num, item, owner, check], ri) => new TableRow({
    children: [
      new TableCell({
        width: { size: widths[0], type: WidthType.DXA },
        shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR },
        borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 80, right: 80 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: num, font: 'Arial', size: 18, bold: true, color: headerColor })
        ]})]
      }),
      new TableCell({
        width: { size: widths[1], type: WidthType.DXA },
        shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR },
        borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [
          new TextRun({ text: item, font: 'Arial', size: 18, color: DARK_TEXT })
        ]})]
      }),
      new TableCell({
        width: { size: widths[2], type: WidthType.DXA },
        shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR },
        borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 80, right: 80 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: owner, font: 'Arial', size: 17, color: '555555' })
        ]})]
      }),
      new TableCell({
        width: { size: widths[3], type: WidthType.DXA },
        shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR },
        borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 80, right: 80 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: check, font: 'Arial', size: 22 })
        ]})]
      }),
    ]
  }));

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...dataRows]
  });
}
```

---

## Priority Summary Table

```javascript
// rows: array of [priority_label, task, impact, effort]
// priority_label examples: '🔴 P0', '🟠 P1', '🟡 P2', '🟢 P3'
function priorityTable(rows) {
  const widths = [1200, 5160, 1400, 1600];
  const headers = ['우선순위', '과제', '임팩트', '예상 공수'];

  const headerRow = new TableRow({ children: headers.map((h, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    borders: cellBorder(NAVY),
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: h, font: 'Arial', size: 18, bold: true, color: WHITE })
    ]})]
  }))});

  const dataRows = rows.map(([pri, task, impact, effort], ri) => new TableRow({
    children: [
      new TableCell({ width: { size: widths[0], type: WidthType.DXA }, shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR }, borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 80, right: 80 }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: pri, font: 'Arial', size: 18, bold: true })] })] }),
      new TableCell({ width: { size: widths[1], type: WidthType.DXA }, shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR }, borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: task, font: 'Arial', size: 18, color: DARK_TEXT })] })] }),
      new TableCell({ width: { size: widths[2], type: WidthType.DXA }, shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR }, borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 80, right: 80 }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: impact, font: 'Arial', size: 17, color: '555555' })] })] }),
      new TableCell({ width: { size: widths[3], type: WidthType.DXA }, shading: { fill: ri % 2 === 0 ? WHITE : LIGHT_GRAY, type: ShadingType.CLEAR }, borders: cellBorder('DDDDDD'), margins: { top: 80, bottom: 80, left: 80, right: 80 }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: effort, font: 'Arial', size: 17, color: DARK_TEXT })] })] }),
    ]
  }));

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...dataRows]
  });
}
```

---

## Title Page Pattern

```javascript
// Standard title page block — insert at top of children array
function titlePage(mainTitle, subtitle, dataSourceNote, badges) {
  return [
    space(2),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 60 },
      children: [new TextRun({ text: mainTitle, font: 'Arial', size: 52, bold: true, color: NAVY })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 120 },
      children: [new TextRun({ text: subtitle, font: 'Arial', size: 40, color: BRAND_PURPLE })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND_PURPLE, space: 6 } },
      spacing: { before: 0, after: 200 },
      children: [new TextRun({ text: '', font: 'Arial', size: 20 })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 40 },
      children: [new TextRun({ text: dataSourceNote, font: 'Arial', size: 20, color: '777777' })]
    }),
    space(2),
    statBadgeRow(badges),
    space(2),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}
```

---

## Footer Note

```javascript
// Always add at the very end of children array
function footerNote(sourceDesc) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: 'CCCCCC', space: 8 } },
    spacing: { before: 200, after: 0 },
    children: [new TextRun({
      text: `본 문서는 ${sourceDesc} 분석하여 작성되었습니다. | 인공지능팩토리`,
      font: 'Arial', size: 16, color: '999999'
    })]
  });
}
```
