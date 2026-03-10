# AssiDocs Proposal Skill

R&D 제안서, 기획서, 연구계획서를 체계적으로 작성하는 범용 스킬.
특정 기술이나 솔루션에 국한되지 않으며, 다양한 분야의 제안서에 적용 가능합니다.
docx-js로 문서를 생성하고, D2 다이어그램으로 구성도/흐름도를 삽입합니다.

## Trigger

Use when the user asks to:
- 제안서, 기획서, 연구계획서 작성/생성
- R&D proposal, research plan, project plan
- 사업계획서, 과제제안서, 연구개발계획서
- "제안서 만들어", "기획서 작성", "proposal 작성"
- "assidocs-proposal", "assidocs proposal"

## Workflow

### 1. 요구사항 분석
- RFP(공고문) 또는 사용자 요구사항 분석
- 제안서 유형 결정 (정부 R&D / 민간 / 내부 기획)
- 페이지 제한, 필수 항목, 평가 기준 파악

### 2. 구조 설계
- 제안서 유형에 맞는 목차 템플릿 선택 (아래 참조)
- 각 섹션별 분량 배분
- D2 다이어그램 배치 계획

### 3. 콘텐츠 작성
- **MANDATORY**: Read [`docx-template.js`](../assidocs-lecture/docx-template.js) for docx-js helper functions.
- 프로젝트 디렉토리에 `create_proposal.js` 생성
- 아래 제안서 전용 스타일과 구성요소 활용

### 4. D2 다이어그램 생성
- `/assidocs-diagram` 스킬 활용
- 시스템 구성도, 연구 추진체계, 일정표, 기술 흐름도 등

### 5. 검증 및 출력
```bash
node create_proposal.js
soffice --headless --convert-to pdf output.docx
```

---

## 제안서 목차 템플릿

### A. 정부 R&D 제안서 (표준형)

```
1. 연구개발과제의 필요성
   가. 문제/배경 분석
   나. 기술 동향
   다. 기존 연구 성과와 한계
   라. 본 연구의 필요성

2. 연구개발과제의 목표 및 내용
   가. 최종 목표
   나. 세부 연구내용
   다. 추진전략 및 방법
   라. 추진체계

3. 연구개발 일정 및 기대성과
   가. 연차별 추진 일정
   나. 정량적 성과 목표
   다. 정성적 기대효과

4. 연구개발비 사용 계획
   가. 총 연구비 편성
   나. 항목별 산출 근거

5. 연구개발 성과 활용방안
   가. 기술 이전/사업화 계획
   나. 후속 연구 연계
   다. 사회적 파급효과
```

### B. 민간/스타트업 사업계획서

```
1. 사업 개요
   가. 비전 및 미션
   나. 문제 정의
   다. 솔루션 개요

2. 시장 분석
   가. 시장 규모 (TAM/SAM/SOM)
   나. 경쟁 분석
   다. 차별화 전략

3. 제품/서비스 상세
   가. 핵심 기능
   나. 기술 아키텍처
   다. 개발 로드맵

4. 사업화 전략
   가. 비즈니스 모델
   나. 마케팅/고객 획득 전략
   다. 핵심 파트너십

5. 팀 구성 및 역량

6. 재무 계획
   가. 매출/비용 전망
   나. 투자 활용 계획
   다. 손익분기점 분석
```

### C. 내부 기획서 (범용)

```
1. 배경 및 목적
2. 현황 분석
3. 추진 방안
4. 기대 효과
5. 소요 자원 및 일정
6. 리스크 관리
```

---

## 색상 체계

```javascript
// 제안서용 색상 (assidocs-lecture와 호환)
const PRIMARY = "1B4F72";     // 진한 파란색 (대제목)
const ACCENT = "2E86C1";      // 밝은 파란색 (중제목)
const LIGHT_BG = "EBF5FB";    // 연한 파란 배경
const HEADER_BG = "2E86C1";   // 테이블 헤더
const CODE_BG = "F4F4F4";     // 코드 배경
const HIGHLIGHT = "FFF9C4";   // 강조 배경 (노란색)
const GRAY = "555555";        // 부가 설명
```

---

## 제안서 전용 구성요소

### 핵심 요약 박스
```javascript
function summaryBox(title, items) {
  // 연한 파란 배경에 핵심 내용을 불릿으로 정리
  return [
    new Paragraph({
      spacing: { before: 120, after: 0 },
      shading: { fill: "E3F2FD", type: ShadingType.CLEAR },
      indent: { left: 360, right: 360 },
      children: [new TextRun({ text: title, size: 22, font: "Arial", bold: true, color: "1565C0" })]
    }),
    ...items.map(item => new Paragraph({
      spacing: { before: 40, after: 40 },
      shading: { fill: "E3F2FD", type: ShadingType.CLEAR },
      indent: { left: 720, right: 360 },
      children: [new TextRun({ text: "• " + item, size: 20, font: "Arial", color: "1565C0" })]
    })),
    new Paragraph({ spacing: { before: 0, after: 120 }, shading: { fill: "E3F2FD", type: ShadingType.CLEAR }, indent: { left: 360, right: 360 }, children: [] })
  ];
}
```

### 성과 지표 테이블
```javascript
function kpiTable(kpis) {
  // kpis: [{name, unit, year1, year2, year3, total}]
  return makeTable(
    ["성과 지표", "단위", "1차연도", "2차연도", "3차연도", "합계"],
    kpis.map(k => [k.name, k.unit, k.year1, k.year2, k.year3, k.total]),
    [2400, 1200, 1440, 1440, 1440, 1440]
  );
}
```

### 연구비 테이블
```javascript
function budgetTable(items) {
  // items: [{category, detail, amount, note}]
  return makeTable(
    ["비목", "세목", "금액(천원)", "산출 근거"],
    items.map(i => [i.category, i.detail, i.amount, i.note]),
    [1800, 2000, 1800, 3760]
  );
}
```

### 일정표 (간트 스타일 텍스트)
```javascript
function scheduleTable(tasks) {
  // tasks: [{name, m1, m2, m3, ..., m12}]  ("●" or "")
  const months = Array.from({length: 12}, (_, i) => `${i+1}월`);
  return makeTable(
    ["연구내용", ...months],
    tasks.map(t => [t.name, ...months.map((_, i) => t[`m${i+1}`] || "")]),
    [2400, ...Array(12).fill(640)]
  );
}
```

---

## D2 다이어그램 패턴 (제안서용)

### 추진체계도
```d2
direction: down
classes: {
  org: { style.fill: "#E3F2FD"; style.stroke: "#1565C0"; style.border-radius: 8; style.bold: true }
  role: { style.fill: "#FFF3E0"; style.stroke: "#F57C00"; style.border-radius: 6; style.font-size: 13 }
  ext: { style.fill: "#E8F5E9"; style.stroke: "#2E7D32"; style.border-radius: 6; style.font-size: 13 }
}
pm: "총괄 책임자\n(PM)" { class: org }
team1: "세부과제 1\n핵심기술 개발" { class: role }
team2: "세부과제 2\n실증 및 검증" { class: role }
advisor: "자문위원회" { class: ext }
pm -> team1
pm -> team2
pm -> advisor: "자문" { style.stroke-dash: 3 }
```

### 기술 로드맵
```d2
direction: right
classes: {
  phase: { style.fill: "#E8F4FD"; style.stroke: "#1565C0"; style.border-radius: 8; style.bold: true }
  task: { style.fill: "#FFF8E1"; style.stroke: "#F9A825"; style.border-radius: 4; style.font-size: 12 }
}
y1: "1차연도\n기반 구축" { class: phase }
y2: "2차연도\n핵심 개발" { class: phase }
y3: "3차연도\n실증/사업화" { class: phase }
y1 -> y2 -> y3
```

### 시스템 구성도
```d2
direction: down
classes: {
  main: { style.fill: "#E8F4FD"; style.stroke: "#1565C0"; style.border-radius: 8; style.bold: true }
  sub: { style.fill: "#FFF3E0"; style.stroke: "#F57C00"; style.border-radius: 6 }
  ext: { style.fill: "#E8F5E9"; style.stroke: "#388E3C"; style.border-radius: 6 }
}
system: "제안 시스템" {
  class: main
  module1: "모듈 A" { class: sub }
  module2: "모듈 B" { class: sub }
}
external: "외부 시스템/데이터" { class: ext }
system.module1 -> external: "연동"
```

---

## 작성 원칙

### 문체
- 경어체 사용 (합니다/입니다)
- 구체적 수치와 근거 제시 (모호한 표현 회피)
- "최초", "세계 최고" 등 과장 표현 지양
- 약어는 첫 등장 시 풀어쓰기: "자연어 처리(NLP, Natural Language Processing)"

### 수치/KPI 규칙
- 모든 KPI에 **정의(분모/기간)** 명시
- 가정치는 `v0 가정치`로 표기하고 검증 계획 병기
- 출처가 있는 수치는 각주 또는 괄호 안에 출처 표기

### 표절/중복 방지
- 타 과제 제안서 문구 직접 인용 금지
- 공개 데이터/논문 인용 시 출처 명기
- 기존 유사 과제와의 차별점 명확히 기술

### 페이지 관리
- 공고문 페이지 제한 준수 (보통 15~30페이지)
- 다이어그램은 1~2개/섹션으로 제한
- 표는 가로폭 초과하지 않도록 열 수 조정

---

## 검증 체크리스트

- [ ] 공고문(RFP) 필수 항목 모두 포함되었는가?
- [ ] 모든 KPI에 정의(단위/기간/분모)가 명시되었는가?
- [ ] 연구비 산출 근거가 구체적인가?
- [ ] D2 다이어그램 종횡비가 정확한가?
- [ ] 과장 표현/플레이스홀더가 남아있지 않은가?
- [ ] 페이지 제한을 초과하지 않는가?
- [ ] 참여 연구원 정보가 정확한가?
- [ ] PDF 변환 후 레이아웃이 정상인가?

---

## Dependencies

- **Node.js**: v22+
- **docx**: `npm install docx` (docx-js library)
- **d2**: `brew install d2` (D2 diagramming)
- **LibreOffice**: `soffice` (PDF 변환용)
- **pandoc**: `brew install pandoc` (선택: md→docx 변환 시)
