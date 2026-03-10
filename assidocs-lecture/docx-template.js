// AssiDocs Lecture - docx-js 보일러플레이트 템플릿
// 사용법: 이 파일을 참고하여 create_docx.js를 작성하세요.

const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
        WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak, ImageRun } = require('docx');

// ==================== 색상 체계 ====================
const PRIMARY = "1B4F72";
const ACCENT = "2E86C1";
const LIGHT_BG = "EBF5FB";
const HEADER_BG = "2E86C1";
const CODE_BG = "F4F4F4";
const WHITE = "FFFFFF";
const BLACK = "000000";
const GRAY = "555555";
const LIGHT_GRAY = "EEEEEE";

// ==================== 테이블 유틸 ====================
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

function headerCell(text, width) {
  return new TableCell({
    borders: cellBorders, width: { size: width, type: WidthType.DXA },
    shading: { fill: HEADER_BG, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 },
      children: [new TextRun({ text, bold: true, color: WHITE, size: 20, font: "Arial" })] })]
  });
}

function dataCell(text, width, opts = {}) {
  const runs = typeof text === 'string'
    ? [new TextRun({ text, size: 20, font: "Arial", color: opts.color || BLACK, bold: opts.bold || false })]
    : text;
  return new TableCell({
    borders: cellBorders, width: { size: width, type: WidthType.DXA },
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ spacing: { before: 40, after: 40 }, alignment: opts.align || AlignmentType.LEFT, children: runs })]
  });
}

function makeTable(headers, rows, colWidths) {
  return new Table({
    columnWidths: colWidths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => headerCell(h, colWidths[i])) }),
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, ci) => dataCell(cell, colWidths[ci], { shading: ri % 2 === 1 ? LIGHT_GRAY : undefined }))
      }))
    ]
  });
}

// ==================== 제목 ====================
function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: "Arial" })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, font: "Arial" })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, font: "Arial" })] });
}

// ==================== 본문 ====================
function p(text, opts = {}) {
  return new Paragraph({ spacing: { before: 80, after: 80 }, alignment: opts.align,
    children: [new TextRun({ text, size: 20, font: "Arial", color: opts.color || BLACK, bold: opts.bold, italics: opts.italics })] });
}
function richP(runs) {
  return new Paragraph({ spacing: { before: 80, after: 80 }, children: runs });
}
function boldP(label, text) {
  return new Paragraph({ spacing: { before: 80, after: 80 },
    children: [
      new TextRun({ text: label, size: 20, font: "Arial", bold: true }),
      new TextRun({ text, size: 20, font: "Arial" })
    ] });
}

// ==================== 코드 블록 ====================
function codeBlock(lines) {
  return lines.map(line => new Paragraph({
    spacing: { before: 0, after: 0 },
    shading: { fill: CODE_BG, type: ShadingType.CLEAR },
    indent: { left: 360 },
    children: [new TextRun({ text: line || " ", font: "Courier New", size: 18, color: "333333" })]
  }));
}

// ==================== 교육 박스 ====================
function tipBox(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    shading: { fill: "FFF3CD", type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [
      new TextRun({ text: "[TIP] ", size: 20, font: "Arial", bold: true, color: "856404" }),
      new TextRun({ text, size: 20, font: "Arial", color: "856404" })
    ]
  });
}

function warningBox(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    shading: { fill: "F8D7DA", type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [
      new TextRun({ text: "[WARNING] ", size: 20, font: "Arial", bold: true, color: "721C24" }),
      new TextRun({ text, size: 20, font: "Arial", color: "721C24" })
    ]
  });
}

function labBox(title, text) {
  return [
    new Paragraph({
      spacing: { before: 120, after: 0 },
      shading: { fill: "D4EDDA", type: ShadingType.CLEAR },
      indent: { left: 360, right: 360 },
      children: [new TextRun({ text: "[HANDS-ON] " + title, size: 20, font: "Arial", bold: true, color: "155724" })]
    }),
    new Paragraph({
      spacing: { before: 0, after: 120 },
      shading: { fill: "D4EDDA", type: ShadingType.CLEAR },
      indent: { left: 360, right: 360 },
      children: [new TextRun({ text, size: 20, font: "Arial", color: "155724" })]
    })
  ];
}

function faqBox(question, answer) {
  return [
    new Paragraph({
      spacing: { before: 120, after: 0 },
      shading: { fill: "E8DAEF", type: ShadingType.CLEAR },
      indent: { left: 360, right: 360 },
      children: [
        new TextRun({ text: "Q: ", size: 20, font: "Arial", bold: true, color: "6C3483" }),
        new TextRun({ text: question, size: 20, font: "Arial", bold: true, color: "6C3483" })
      ]
    }),
    new Paragraph({
      spacing: { before: 0, after: 120 },
      shading: { fill: "E8DAEF", type: ShadingType.CLEAR },
      indent: { left: 360, right: 360 },
      children: [
        new TextRun({ text: "A: ", size: 20, font: "Arial", bold: true, color: "4A235A" }),
        new TextRun({ text: answer, size: 20, font: "Arial", color: "4A235A" })
      ]
    })
  ];
}

function analogyBox(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    shading: { fill: "D6EAF8", type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [
      new TextRun({ text: "[쉽게 이해하기] ", size: 20, font: "Arial", bold: true, color: "1A5276" }),
      new TextRun({ text, size: 20, font: "Arial", color: "1A5276" })
    ]
  });
}

function vocabBox(term, definition) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    shading: { fill: "FDEBD0", type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [
      new TextRun({ text: term + ": ", size: 20, font: "Arial", bold: true, color: "784212" }),
      new TextRun({ text: definition, size: 20, font: "Arial", color: "784212" })
    ]
  });
}

// ==================== 목록 ====================
const numbering = {
  config: [
    { reference: "bullet-list", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num-list", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    // 필요시 추가 넘버링 참조를 여기에 등록
  ]
};

function bullet(text) {
  return new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 20, font: "Arial" })] });
}
function boldBullet(label, text) {
  return new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { before: 40, after: 40 },
    children: [
      new TextRun({ text: label, size: 20, font: "Arial", bold: true }),
      new TextRun({ text, size: 20, font: "Arial" })
    ] });
}
function numItem(ref, text) {
  return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 20, font: "Arial" })] });
}

// ==================== D2 다이어그램 삽입 ====================
function diagramImage(filePath, width, height, title, description) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(filePath),
      transformation: { width, height },
      altText: { title, description, name: title }
    })]
  });
}

// ==================== 문서 스타일 ====================
function createDocument(children, title = "강의 교안") {
  return new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 20 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 32, bold: true, color: PRIMARY, font: "Arial" },
          paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 26, bold: true, color: ACCENT, font: "Arial" },
          paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 22, bold: true, color: "34495E", font: "Arial" },
          paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
      ]
    },
    numbering,
    sections: [{
      properties: {
        page: {
          margin: { top: 1200, right: 1200, bottom: 1200, left: 1200 },
          pageNumbers: { start: 1 }
        }
      },
      headers: {
        default: new Header({ children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: title, size: 16, color: GRAY, font: "Arial", italics: true })]
        })] })
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "- ", size: 16, color: GRAY, font: "Arial" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GRAY, font: "Arial" }),
            new TextRun({ text: " -", size: 16, color: GRAY, font: "Arial" })]
        })] })
      },
      children
    }]
  });
}

// ==================== 내보내기 ====================
async function saveDocument(doc, outputPath) {
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`DOCX created: ${outputPath}`);
}

module.exports = {
  // Colors
  PRIMARY, ACCENT, LIGHT_BG, HEADER_BG, CODE_BG, WHITE, BLACK, GRAY, LIGHT_GRAY,
  // Table
  headerCell, dataCell, makeTable,
  // Headings
  h1, h2, h3,
  // Text
  p, richP, boldP,
  // Code
  codeBlock,
  // Educational boxes
  tipBox, warningBox, labBox, faqBox, analogyBox, vocabBox,
  // Lists
  bullet, boldBullet, numItem, numbering,
  // Diagram
  diagramImage,
  // Document
  createDocument, saveDocument,
  // Re-exports from docx
  Paragraph, TextRun, Table, TableRow, TableCell, PageBreak, ImageRun,
  AlignmentType, ShadingType, WidthType, VerticalAlign, BorderStyle
};
