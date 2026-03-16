# AssIDocs Checklist — Annotated Example Structure

This file documents the structure of the "추론 자동화 안정화 이슈분석 체크리스트" report
as a reference for content organization and naming conventions.

---

## Title Page

- **mainTitle**: `추론 자동화 안정화`  (large, NAVY)
- **subtitle**: `이슈 분석 및 체크리스트`  (BRAND_PURPLE)
- **dataSourceNote**: `슬랙 로그 + 참가자 Q&A (총 368건) 통합 분석`
- **badges** (4 colored stat boxes):
  ```
  { label: '채점 지연/대기', count: '158건', color: ORANGE }
  { label: '추론 오류/실패', count: '70+건', color: RED }
  { label: '환경·패키지 문제', count: '68건', color: BRAND_PURPLE }
  { label: 'HuggingFace 외부접근', count: '24건', color: NAVY }
  ```

---

## Section 1: 이슈 구조 개요

**heading1**: `1. 이슈 구조 개요`

**body**: 분석 대상 및 분류 기준 1~2문장

**issueLayerTable** (4 rows):
```
{ label: '인프라 레이어',        color: RED,          bgColor: 'FFE8E8', description: '...' }
{ label: '처리 용량 레이어',     color: ORANGE,       bgColor: 'FFF3E0', description: '...' }
{ label: '참가자 제출 레이어',   color: BRAND_PURPLE, bgColor: 'F3E5F5', description: '...' }
{ label: '운영·CS 레이어',      color: NAVY,         bgColor: 'E8EAF6', description: '...' }
```

*Naming convention*: "[도메인] 레이어" — always 4 layers mapping to the 4 issue types

---

## Section 2: 이슈별 상세 분석

**heading1**: `2. 이슈별 상세 분석`

### Per-issue block structure:

```
heading2(이슈 제목, severity_color)
  heading3('원인')
    calloutBox('!', root_cause_summary, bgColor, borderColor)
    [optional] threeColTable(항목/내용/비고 detail)
  
  heading3('대응 과정')
    bullet() × N  OR  threeColTable()
  
  heading3('Q&A에서 확인된 참가자 경험')   [optional — if Q&A data available]
    calloutBox('"', participant_quote, PURPLE_BG, BRAND_PURPLE)
  
  heading3('재발 방지 제안')
    sectionBox('체크리스트 | [이슈명]', issue_color, ['[ ] 항목1', '[ ] 항목2', ...])
  
  space(2)
```

### Issue severity → color mapping:
```
Critical infra issue    → heading2(title, RED)         + calloutBox('!', ..., 'FFE8E8', RED)
Capacity/queue issue    → heading2(title, ORANGE)       + calloutBox('!', ..., 'FFF3E0', AMBER)
Environment/env issue   → heading2(title, BRAND_PURPLE) + calloutBox('!', ..., 'F3E5F5', BRAND_PURPLE)
Process/ops issue       → heading2(title, '555555')     + calloutBox(...)
```

### sectionBox title convention:
`'체크리스트 | [카테고리명]'`
Examples:
- `'체크리스트 | GCP 클러스터 설정'`
- `'체크리스트 | 처리 용량 관리'`
- `'체크리스트 | 네트워크 제한 환경 안내'`
- `'체크리스트 | 시스템 패치 정책'`
- `'체크리스트 | 오류 로그 및 디버깅 UX'`

---

## Section 3: 체크리스트

**heading1**: `3. [문맥에 맞는 제목] 체크리스트`
Example: `3. 대회 오픈 전 통합 체크리스트`

**body**: 단계별 점검 안내 1문장

### Phase structure:
```
heading2('A. [Phase Name] (오픈 N주 전)')
  checklistTable(NAVY, [
    ['A-1', '항목 설명...', '개발팀', '☐'],
    ['A-2', '항목 설명...', '개발팀', '☐'],
    ...
  ])
  space(1)

heading2('B. [Phase Name] (오픈 N일 전)')
  checklistTable(ORANGE, [...])
  space(1)

heading2('C. [Phase Name] (오픈 당일)')
  checklistTable(BRAND_PURPLE, [...])
  space(2)
```

*Naming convention for phases*:
- A = Infrastructure / 인프라 설정 (2 weeks before)
- B = Capacity & performance / 용량·성능 검증 (1 week before)
- C = Participant comms / 참가자 안내 (launch day)

*Header color by phase*: A=NAVY, B=ORANGE, C=BRAND_PURPLE
*Row number format*: `'A-1'`, `'B-3'` etc. colored in phase color

---

## Section 4: 우선순위 요약

**heading1**: `4. 우선순위별 개선 과제 요약`

**body**: 기준 설명 (임팩트 대비 공수)

**priorityTable** rows format:
```
['🔴 P0', '과제 설명', '매우 높음', '0.5일 ~ 2일']
['🟠 P1', '과제 설명', '높음',     '2~5일']
['🟡 P2', '과제 설명', '중간',     '0.5일 (문서화)']
['🟢 P3', '과제 설명', '중간',     '3~5일']
```

*Standard impact labels*: `매우 높음` / `높음` / `중간` / `낮음`
*Standard effort labels*: `0.5일` / `1일` / `2~3일` / `3~5일` / `1~2주`

---

## Page Break Placement

- After title page (before Section 1)
- Before Section 2 (after long Section 1 table)
- Between long issue blocks (use judgment — add if block > ~30 lines)
- Before Section 4

---

## Footer

Always at end of children:
```javascript
footerNote('슬랙 로그(3,589줄) + Q&A 데이터(368건)를')
```
Adapt the source description to match actual data used.
