---
name: assidocs-md-note
description: "Pandoc 기반 마크다운 기술문서 작성 및 DOCX 변환. 인라인 D2 다이어그램, YAML frontmatter, 한국어 폰트 지원. 사용자가 '문서 만들어', 'md에서 docx', '마크다운 문서', 'note 작성', '보고서 작성', 'assidocs-md-note', 'md note', '기술문서 작성', '마크다운 노트', 'docx 변환'을 요청할 때 사용."
---

# AssiDocs MD Note

Pandoc 표준 마크다운으로 기술문서를 작성하고 DOCX로 변환.
인라인 D2 다이어그램을 마크다운에 직접 삽입하여 문서 하나로 완결.

## Dependencies

- **pandoc** v3.0+ (`brew install pandoc`)
- **d2** (`brew install d2`)
- **python3**

## Workflow

### 1. 마크다운 작성

프로젝트 디렉토리에 `.md` 파일 생성. Pandoc 표준 문법만 사용.

### 2. 초기 설정 (프로젝트당 1회)

```bash
# reference.docx 생성 및 한국어 스타일 적용
pandoc --print-default-data-file reference.docx > reference.docx
python3 SKILL_DIR/scripts/setup_reference_docx.py reference.docx reference.docx

# Lua 필터 복사
cp SKILL_DIR/scripts/pagebreak.lua SKILL_DIR/scripts/d2-filter.lua SKILL_DIR/scripts/full-width-tables.lua .
```

`SKILL_DIR` = 이 스킬의 절대 경로.

### 3. DOCX 변환

```bash
pandoc document.md \
  --from=markdown+smart --to=docx \
  --output=document.docx \
  --reference-doc=reference.docx \
  --lua-filter=pagebreak.lua \
  --lua-filter=d2-filter.lua \
  --lua-filter=full-width-tables.lua \
  --standalone --dpi=300

python3 SKILL_DIR/scripts/center_images.py document.docx
```

## 마크다운 문법 요약

### YAML Frontmatter

```yaml
---
title: "문서 제목"
subtitle: "부제목"
author: "작성자"
date: "2026-03-13"
lang: ko
---
```

### 제목

```markdown
## 1. 대제목
### 1.1 중제목
#### 소제목
```

`#`은 문서 최상위 제목에만 사용. 본문 섹션은 `##`부터.

### 페이지 나누기

```markdown
\newpage
```

### 이미지 (외부 파일)

```markdown
![캡션](path/to/image.png){width=80%}
```

### 인라인 D2 다이어그램

````markdown
```{.d2 caption="구성도" width=80%}
direction: down
classes: {
  box: {
    style.fill: "#F5F5F5"
    style.stroke: "#9E9E9E"
    style.border-radius: 8
    style.font-size: 16
  }
}
a: "모듈 A" { class: box }
b: "모듈 B" { class: box }
a -> b
```
````

속성: `caption`, `width` (기본 80%), `theme` (기본 1), `pad` (기본 10), `layout` (기본 elk).

#### D2 다이어그램 디자인 원칙 (필수)

DOCX 삽입 시 다이어그램이 꽉 차고 균형 잡혀 보여야 합니다.

**레이아웃 엔진**: ELK 사용 (dagre 대비 화살표 간격 ~20% 짧음). d2-filter.lua가 자동 적용.

**미니멀 색상**: 무채색 기반 + 강조색 1개. 최대 3색.

```
메인 블록:    fill="#F5F5F5" stroke="#9E9E9E"   (연한 회색)
강조 블록:    fill="#E3F2FD" stroke="#90CAF9"    (연한 파란)
타이틀 블록:  fill="#424242" font-color="#FFFFFF" (진한 회색 반전)
그룹/컨테이너: fill="#FAFAFA" stroke="#E0E0E0"   (거의 흰색)
결과 블록:    fill="#E8F5E9" stroke="#A5D6A7"    (연한 초록)
점선 노트:    fill="#FAFAFA" stroke="#BDBDBD" stroke-dash=3 (보조 설명)
```

**블록 크기**: `width`와 `height`를 명시하여 블록이 충분히 크게. 화살표 대비 블록 비율이 커야 균형.

```d2
# 블록 크기 기준 (classes에 정의)
일반 블록:  width=200~300, height=42~50
넓은 블록:  width=350~400, height=50~55
타이틀:     width=350~400, height=50
```

**폰트 크기**: 최소 16pt. DOCX에서 축소되므로 넉넉하게.

```d2
style.font-size: 16   # 일반 블록
style.font-size: 18   # 컨테이너/그룹 제목
style.font-size: 20~22 # 최상위 타이틀
```

**간격 축소 핵심 전략**:
- `grid-columns: N` 으로 수평 블록 배치 (화살표 없이 그룹핑)
- 화살표 라벨은 2~3글자 이내 (길면 생략)
- 블록 라벨에 `\n` 줄바꿈으로 2줄 구성 → 블록이 커져 비율 개선
- `classes` 블록으로 스타일 일괄 정의 (인라인 반복 금지)

**점선 노트 박스**: 여백을 설명으로 활용. `--` (양방향 연결)로 메인 블록에 연결.

```d2
note1: "보조 설명 텍스트" {
  style.stroke-dash: 3
  style.fill: "#FAFAFA"
  style.stroke: "#BDBDBD"
  style.font-size: 14
  style.font-color: "#616161"
}
main_block -- note1: { style.stroke-dash: 3; style.stroke: "#BDBDBD" }
```

**D2 예약어 주의**: 노드 이름으로 `top`, `bottom`, `left`, `right`, `center`, `classes`, `label`, `style`, `shape`, `icon`, `tooltip`, `link`, `near`, `width`, `height`, `grid-rows`, `grid-columns`, `grid-gap` 사용 금지. `top` 대신 `header`, `platform` 등 사용.

**D2 다이어그램 기본 템플릿**:

````d2
direction: down
classes: {
  title: {
    style.border-radius: 10
    style.font-size: 22
    style.bold: true
    style.fill: "#424242"
    style.font-color: "#FFFFFF"
    width: 360
    height: 50
  }
  box: {
    style.border-radius: 8
    style.font-size: 16
    style.bold: true
    width: 200
    height: 42
  }
  accent: {
    style.border-radius: 8
    style.font-size: 16
    style.bold: true
    style.fill: "#E3F2FD"
    style.stroke: "#90CAF9"
    width: 200
    height: 42
  }
  group: {
    style.fill: "#FAFAFA"
    style.stroke: "#E0E0E0"
    style.border-radius: 10
    style.font-size: 15
    style.bold: true
  }
  note: {
    style.border-radius: 6
    style.fill: "#FAFAFA"
    style.stroke: "#BDBDBD"
    style.stroke-dash: 3
    style.font-size: 14
    style.font-color: "#616161"
  }
}
````

### 테이블

```markdown
| 항목 | 설명 |
|------|------|
| A    | 내용 |
```

전체 너비 자동 적용. 테두리 검정색.

### 서식 규칙

- **굵게**: `**텍스트**`
- 기울임체 사용 안함
- 중앙정렬: 이미지/캡션만 후처리로 적용, 본문은 좌측정렬

### 불릿 목록

```markdown
- 항목
- **라벨:** 설명
```

### 인용

```markdown
> 강조 텍스트
```

## 스크립트

| 파일 | 역할 |
|------|------|
| `pagebreak.lua` | `\newpage` → DOCX 페이지 브레이크 (pandoc-ext 공식) |
| `d2-filter.lua` | `.d2` 코드블록 → PNG 렌더링 후 이미지 삽입 |
| `full-width-tables.lua` | 테이블 페이지 전체 너비 |
| `center_images.py` | DOCX 내 이미지/캡션 중앙정렬 후처리 |
| `setup_reference_docx.py` | reference.docx 한국어 폰트/색상/테두리 설정 |

## reference.docx 스타일

- **폰트**: Arial + Apple SD Gothic Neo (macOS) / Malgun Gothic (Windows)
- **Heading 1**: #1B4F72, 16pt, Bold
- **Heading 2**: #2E86C1, 13pt, Bold
- **Heading 3**: #34495E, 11pt, Bold
- **본문**: 10pt
- **테이블 테두리**: #000000
- 기울임체 없음, Title/Subtitle 중앙정렬 없음

## 문서 구조 예시

```markdown
---
title: "기술 설계서"
subtitle: "v1.0"
author: "조직명"
date: "2026-03-13"
lang: ko
---

# 기술 설계서

(세부 추진계획) v1.0

\newpage

## 1. 개요

본 과제는 ...

```{.d2 caption="시스템 구성도" width=80%}
direction: down
classes: {
  title: { style.border-radius: 10; style.font-size: 22; style.bold: true; style.fill: "#424242"; style.font-color: "#FFFFFF"; width: 360; height: 50 }
  box: { style.border-radius: 8; style.font-size: 16; style.bold: true; width: 200; height: 42 }
  accent: { style.border-radius: 8; style.font-size: 16; style.bold: true; style.fill: "#E3F2FD"; style.stroke: "#90CAF9"; width: 200; height: 42 }
  group: { style.fill: "#FAFAFA"; style.stroke: "#E0E0E0"; style.border-radius: 10; style.font-size: 15; style.bold: true }
}
header: "시스템명" { class: title }
layer1: "처리 계층" {
  class: group
  grid-columns: 3
  a: "모듈 A" { class: box }
  b: "모듈 B" { class: accent }
  c: "모듈 C" { class: box }
}
header -> layer1: { style.stroke-width: 2 }
```

| 항목 | 설명 |
|------|------|
| A    | 내용 |

\newpage

## 2. 상세 설계

...
```
