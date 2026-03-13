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

속성: `caption`, `width` (기본 80%), `theme` (기본 1), `pad` (기본 20).

#### D2 다이어그램 디자인 원칙

**미니멀 색상**: 2~3색만 사용. 무채색 기반 + 강조색 1개.

```
# 권장 색상 팔레트 (모노톤 + 블루 악센트)
메인 배경:   "#F5F5F5"  (연한 회색)     stroke: "#9E9E9E"
강조 배경:   "#E3F2FD"  (연한 파란)     stroke: "#64B5F6"
헤더/타이틀: "#424242"  (진한 회색)     stroke: "#616161"
외부/연동:   "#FAFAFA"  (거의 흰색)     stroke: "#BDBDBD"
```

**폰트 크기**: 최소 14pt. 타이틀급은 18~20pt.

```d2
style.font-size: 14   # 일반 블록 최소
style.font-size: 18   # 컨테이너/그룹 제목
style.font-size: 20   # 최상위 타이틀
```

**간격 축소**: `--pad 20` 사용. 블록 라벨을 짧게 유지하여 화살표 길이 최소화.

**균형 잡힌 구조**:
- `direction: down` 사용 시 같은 레벨 노드 수를 3~5개로 제한
- 컨테이너로 관련 노드를 그룹핑하여 자연스러운 배치
- 화살표 라벨은 2~3글자 이내 (길면 생략)
- `classes` 블록으로 스타일 일괄 정의 (인라인 스타일 최소화)

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
  box: {
    style.fill: "#F5F5F5"
    style.stroke: "#9E9E9E"
    style.border-radius: 8
    style.font-size: 16
  }
  group: {
    style.fill: "#FAFAFA"
    style.stroke: "#BDBDBD"
    style.font-size: 18
  }
}
system: "시스템" { class: group
  a: "모듈 A" { class: box }
  b: "모듈 B" { class: box }
}
system.a -> system.b
```

| 항목 | 설명 |
|------|------|
| A    | 내용 |

\newpage

## 2. 상세 설계

...
```
