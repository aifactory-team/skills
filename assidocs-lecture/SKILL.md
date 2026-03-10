# AssiDocs Lecture Skill

강의 교안(lecture handout)을 docx-js + D2 다이어그램으로 생성하는 스킬.
파트 기반 구조, 다양한 교육용 박스, D2 삽화, 팩트체크 워크플로우를 포함합니다.

## Trigger

Use when the user asks to:
- 강의 교안, 강의안, 강의자료 만들기/생성
- lecture handout, lecture material, course material
- 교안 docx, 수업자료, 워크숍 교재
- "교안 만들어", "강의안 작성", "lecture 만들어"
- 기존 교안 수정/업데이트/버전업

## Workflow

### 1. 주제 분석 및 구조 설계
- 대상 청중 파악 (초보자/중급/전문가)
- 파트(Part) 구조 설계 (보통 5~10개 파트)
- 각 파트별 학습 목표 정의

### 2. create_docx.js 스크립트 작성
- **MANDATORY**: Read [`docx-template.js`](docx-template.js) for the complete boilerplate code with all helper functions.
- 프로젝트 디렉토리에 `create_docx.js` 생성
- 아래 헬퍼 함수와 색상 체계를 사용

### 3. D2 다이어그램 생성
- `/assidocs-diagram` 스킬을 활용하여 개념도/구성도 생성
- `diagrams/` 디렉토리에 .d2 파일 작성 후 PNG 렌더링
- **반드시** `sips -g pixelWidth -g pixelHeight` 로 실제 크기 확인 후 종횡비 유지하여 삽입

### 4. 팩트체크 (선택)
- 커뮤니티 사례나 기술 설명을 웹 검색으로 교차검증
- 출처가 불명확한 내용 제거
- 확인된 출처 URL 병기

### 5. DOCX 생성 및 검증
```bash
node create_docx.js
soffice --headless --convert-to pdf output.docx
pdftoppm -jpeg -r 150 output.pdf verify_page
```
- 렌더링된 이미지를 확인하여 레이아웃/종횡비 검증

## 문서 구조

```
[표지]
  - 제목 (72pt, 진한 파란색)
  - 부제목 (48pt, 파란색)
  - 설명 문구
  - 메타 테이블 (대상, 준비물, 목표, 작성일)

[목차]
  - 파트별 내용 및 난이도 표시

[파트 1~N]
  - h1: 파트 제목
  - h2: 섹션 제목
  - h3: 하위 섹션
  - 본문, 표, 코드블록, 교육 박스, D2 다이어그램

[부록]
  - 치트시트, 용어 사전 등
```

## 색상 체계

```javascript
const PRIMARY = "1B4F72";    // 진한 파란색 (h1)
const ACCENT = "2E86C1";     // 밝은 파란색 (h2, 강조)
const LIGHT_BG = "EBF5FB";   // 연한 파란 배경
const HEADER_BG = "2E86C1";  // 테이블 헤더
const CODE_BG = "F4F4F4";    // 코드 배경
const GRAY = "555555";       // 부가 설명
```

## 교육 박스 유형

| 박스 | 배경색 | 용도 | 접두사 |
|------|--------|------|--------|
| `tipBox(text)` | #FFF3CD (노란색) | 유용한 팁 | [TIP] |
| `warningBox(text)` | #F8D7DA (빨간색) | 주의/경고 | [WARNING] |
| `labBox(title, text)` | #D4EDDA (초록색) | 실습 과제 | [HANDS-ON] |
| `faqBox(q, a)` | #E8DAEF (보라색) | 자주 묻는 질문 | Q: / A: |
| `analogyBox(text)` | #D6EAF8 (파란색) | 비유로 설명 | [쉽게 이해하기] |
| `vocabBox(term, def)` | #FDEBD0 (주황색) | 용어 설명 | 용어: 정의 |

## 헬퍼 함수 요약

```javascript
// 제목
h1(text), h2(text), h3(text)

// 본문
p(text, opts), richP(runs), boldP(label, text)

// 목록
bullet(text), boldBullet(label, text), numItem(ref, text)

// 테이블
makeTable(headers, rows, colWidths)
headerCell(text, width), dataCell(text, width, opts)

// 코드
codeBlock(lines)  // 회색 배경 코드 블록

// 교육 박스
tipBox(text), warningBox(text), labBox(title, text)
faqBox(question, answer), analogyBox(text), vocabBox(term, definition)
```

## D2 다이어그램 삽입 규칙

1. `diagrams/` 디렉토리에 번호 접두사로 파일 생성: `01_name.d2`, `02_name.d2`
2. `d2 --theme 1 --pad 40 input.d2 output.png` 로 렌더링
3. 실제 픽셀 크기 확인:
   ```bash
   sips -g pixelWidth -g pixelHeight diagrams/*.png
   ```
4. 최대 너비 560px 기준으로 종횡비 유지 계산:
   ```
   ratio = originalWidth / originalHeight
   if ratio >= 1:  width = 560, height = 560 / ratio
   if ratio < 1:   height = 530, width = 530 * ratio  (세로 이미지)
   ```
5. ImageRun으로 삽입:
   ```javascript
   new Paragraph({
     alignment: AlignmentType.CENTER,
     spacing: { before: 200, after: 200 },
     children: [new ImageRun({
       type: "png",
       data: fs.readFileSync("diagrams/01_name.png"),
       transformation: { width: CALC_W, height: CALC_H },
       altText: { title: "제목", description: "설명", name: "id" }
     })]
   })
   ```

## 파트 작성 패턴

각 파트는 아래 구조를 따릅니다:

```javascript
// ==================== PART N ====================
children.push(h1("N부: 파트 제목"));

// 도입: 비유로 쉽게 설명
children.push(analogyBox("이 개념은 ... 과 비슷합니다."));

// 핵심 내용
children.push(h2("N.1 섹션 제목"));
children.push(p("설명 텍스트"));

// 표로 정리
children.push(makeTable(["헤더1", "헤더2"], [["데이터1", "데이터2"]], [4680, 4680]));

// D2 다이어그램 삽입
children.push(p("구성도:", { bold: true }));
children.push(/* ImageRun */);

// 코드 예시
children.push(...codeBlock(["명령어1", "명령어2"]));

// 팁/주의
children.push(tipBox("유용한 정보"));
children.push(warningBox("주의사항"));

// FAQ
children.push(...faqBox("질문?", "답변"));

// 실습
children.push(...labBox("실습 제목", "실습 내용"));

// 페이지 구분
children.push(new Paragraph({ children: [new PageBreak()] }));
```

## 검증 체크리스트

- [ ] 모든 D2 다이어그램 종횡비 정확한가?
- [ ] 사례/출처가 교차검증되었는가?
- [ ] 코드 블록이 정상 표시되는가?
- [ ] 페이지 구분이 적절한가?
- [ ] 용어가 일관되게 사용되는가?
- [ ] PDF 변환 후 레이아웃이 정상인가?

## Dependencies

- **Node.js**: v22+
- **docx**: `npm install docx` (docx-js library)
- **d2**: `brew install d2` (D2 diagramming)
- **LibreOffice**: `soffice` (PDF 변환용)
- **Poppler**: `pdftoppm` (PDF → 이미지 검증용)
