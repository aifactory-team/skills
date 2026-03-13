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
a: "모듈 A" { style.fill: "#E3F2FD" }
b: "모듈 B" { style.fill: "#FFF3E0" }
a -> b
```
````

속성: `caption`, `width` (기본 80%), `theme` (기본 4), `pad` (기본 40).

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
system: "시스템" {
  a: "모듈 A"
  b: "모듈 B"
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
