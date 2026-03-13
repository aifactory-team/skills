# AI Factory Skills

Claude Code에서 사용할 수 있는 문서 생성 스킬 모음입니다.

## 설치

```bash
claude skill add --global /path/to/skill-name
```

또는 특정 스킬만 개별 설치:

```bash
git clone https://github.com/aifactory-team/skills.git
claude skill add --global skills/assidocs-md-note
```

## 스킬 목록

### assidocs-md-note

Pandoc 기반 마크다운 기술문서 작성 및 DOCX 변환 스킬.

- **용도**: 마크다운(.md)으로 기술문서를 작성하고 고품질 DOCX로 변환
- **주요 기능**: 인라인 D2 다이어그램, YAML frontmatter, 한국어 폰트, 전체 너비 테이블, 이미지/캡션 중앙정렬
- **의존성**: pandoc v3.0+, d2, python3
- **번들 스크립트**: `pagebreak.lua`, `d2-filter.lua`, `full-width-tables.lua`, `center_images.py`, `setup_reference_docx.py`

### assidocs-proposal

R&D 제안서, 기획서, 연구계획서 작성 스킬.

- **용도**: 정부 R&D, 민간 사업계획서, 내부 기획서 등 체계적 제안서 작성
- **주요 기능**: 제안서 목차 템플릿(정부 R&D/민간/내부), 성과 지표 테이블, 연구비 테이블, D2 다이어그램 패턴
- **의존성**: Node.js v22+, docx (npm), d2, LibreOffice

### assidocs-lecture

강의 교안(lecture handout) 생성 스킬.

- **용도**: docx-js + D2 다이어그램으로 교육용 강의 자료 생성
- **주요 기능**: 파트 기반 구조, 교육용 박스(개념/실습/퀴즈), D2 삽화, 팩트체크 워크플로우
- **의존성**: Node.js v22+, docx (npm), d2, LibreOffice

### assidocs-diagram

D2 다이어그램 전문 생성 스킬.

- **용도**: 아키텍처 다이어그램, 플로우차트, ERD, 시퀀스 다이어그램 등 전문 다이어그램 생성
- **주요 기능**: D2 언어 기반, 다양한 테마/스타일, PNG/SVG 출력, DOCX 삽입 지원
- **의존성**: d2

### assidocs-hwp

HWP 5.0 한글 문서 처리 스킬.

- **용도**: HWP 파일 읽기, 텍스트 추출, 테이블 셀 수정, 새 HWP 파일 생성
- **주요 기능**: OLE 바이너리 파싱, 레코드 단위 편집, 체크박스 치환, 빈 셀 채우기, 바이너리 패치 저장
- **의존성**: python3, olefile (pip)
- **번들 스크립트**: `hwp_utils.py`

## 라이선스

MIT
