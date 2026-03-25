---
name: assidocs-hwp
description: "HWP 5.0 및 HWPX 한글 문서 읽기, 텍스트 추출, 라운드트립 쓰기, 콘텐츠 치환. 사용자가 'hwp 읽어', 'hwpx 읽어', 'hwp 만들어', '한글 파일', '설문 추출', 'hwp 변환', 'hwpx 변환', 'hwp 라운드트립', 'hwp 텍스트 치환' 등을 요청할 때 사용합니다."
---

# assidocs-hwp: HWP 5.0 / HWPX 문서 처리 스킬

## 개요

HWP 5.0(OLE Compound File) 및 HWPX(ZIP/XML 기반) 형식의 한글 문서를 **읽기 → 파싱 → 수정 → 재조립 → 저장**하는 완전한 라운드트립을 지원합니다.

## 스크립트

- `scripts/hwp_utils.py` — HWP 5.0 바이너리 레코드 파싱, OLE 패치, 텍스트 인코딩/디코딩
- `scripts/hwp_roundtrip.py` — 라운드트립 엔진 (읽기 → 치환 → 저장 → 검증)
- `scripts/hwpx_utils.py` — HWPX(ZIP/XML) 읽기, 텍스트 추출/치환, 테이블 셀 채우기, 양식 작성

## 핵심 API

### 라운드트립 (읽기 → 저장)

```python
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/assidocs-hwp/scripts'))
from hwp_roundtrip import roundtrip_hwp, verify_roundtrip

# 단순 라운드트립 (원본 그대로 복사)
result = roundtrip_hwp("input.hwp", "output.hwp")
# result = {'success': True, 'sections': 2, 'replaced': 0, 'error': None}

# 텍스트 치환 포함
result = roundtrip_hwp("input.hwp", "output.hwp", {
    "김철수": "김태영",
    "(주)ABC": "(주)인공지능팩토리"
})

# 검증
vr = verify_roundtrip("input.hwp", "output.hwp", replacements)
# vr = {'match': True, 'diffs': [], 'error': None}
```

### 안전한 문서 수정 패턴 (권장)

HWP 수정 시 **가장 안전한 방식**은 아래 두 가지를 조합하는 것입니다:

1. **빈 셀 채우기** (`fill_empty_cell`) — 빈 테이블 셀에 새 텍스트 삽입
2. **바이트 레벨 치환** (`safe_replace`) — 기존 텍스트를 다른 텍스트로 교체

```python
import struct, zlib
from hwp_utils import (read_hwp, parse_records, records_to_bytes, encode_para_text,
                        decode_para_text, ole_binary_patch, HwpRecord, _has_extended_ctrl,
                        TAG_PARA_TEXT, TAG_PARA_HEADER)

doc = read_hwp("input.hwp")
records = list(parse_records(doc.sections[0]))

# --- 1. 빈 셀 채우기 (bit 31 보존) ---
def fill_empty_cell(records, para_hdr_idx, text):
    text_data = encode_para_text(text)
    n_chars = len(text) + 1
    hdr = bytearray(records[para_hdr_idx].data)
    orig_nc = struct.unpack('<I', hdr[0:4])[0]
    flag = orig_nc & 0x80000000
    struct.pack_into('<I', hdr, 0, n_chars | flag)
    records[para_hdr_idx] = HwpRecord(records[para_hdr_idx].tag_id,
                                       records[para_hdr_idx].level, bytes(hdr))
    new_rec = HwpRecord(TAG_PARA_TEXT, records[para_hdr_idx].level + 1, text_data)
    records.insert(para_hdr_idx + 1, new_rec)
    return 1  # 삽입된 레코드 수

# --- 2. 바이트 레벨 치환 (확장 제어문자 스킵) ---
def safe_replace(records, idx, old_str, new_str):
    rec = records[idx]
    if rec.tag_id != TAG_PARA_TEXT:
        return False
    if _has_extended_ctrl(rec.data):
        return False
    old_b = old_str.encode('utf-16-le')
    new_b = new_str.encode('utf-16-le')
    if old_b not in rec.data:
        return False
    new_data = rec.data.replace(old_b, new_b, 1)
    char_diff = (len(new_data) - len(rec.data)) // 2
    records[idx] = HwpRecord(rec.tag_id, rec.level, new_data)
    if char_diff != 0:
        for k in range(idx - 1, -1, -1):
            if records[k].tag_id == TAG_PARA_HEADER:
                hdr = bytearray(records[k].data)
                old_nc = struct.unpack('<I', hdr[0:4])[0]
                flag = old_nc & 0x80000000
                count = (old_nc & 0x7FFFFFFF) + char_diff
                if count < 1: count = 1
                struct.pack_into('<I', hdr, 0, count | flag)
                records[k] = HwpRecord(records[k].tag_id, records[k].level, bytes(hdr))
                break
    return True

# --- 실행 순서 ---
# ① 빈 셀 채우기: 반드시 뒤에서부터 (인덱스 시프트 방지)
fills = {292: '김태영', 108: '김태영', 58: '(주)인공지능팩토리'}
for idx in sorted(fills.keys(), reverse=True):
    fill_empty_cell(records, idx, fills[idx])

# ② 빈 셀 삽입 후 인덱스가 변경되므로 시프트 계산
inserted = sorted(fills.keys())
def shifted(orig_idx):
    return orig_idx + sum(1 for k in inserted if k < orig_idx)

# ③ 바이트 치환 (시프트된 인덱스 사용)
safe_replace(records, shifted(460), 'o', 'o 내용 입력')

# --- 저장 ---
rebuilt = records_to_bytes(records)
if doc.compressed:
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    stream_data = comp.compress(rebuilt) + comp.flush()
else:
    stream_data = rebuilt
ole_binary_patch("input.hwp", "output.hwp", "Section0", stream_data)
```

### 저수준 API (hwp_utils)

```python
from hwp_utils import (read_hwp, parse_records, records_to_bytes,
                        decode_para_text, encode_para_text,
                        ole_binary_patch, fill_table_cells,
                        _has_extended_ctrl,
                        HwpRecord, TAG_PARA_TEXT, TAG_PARA_HEADER)

doc = read_hwp("input.hwp")
text = doc.extract_all_text()
records = list(parse_records(doc.sections[0]))
```

### 테이블 빈 셀 채우기 (간편 API)

```python
from hwp_utils import fill_table_cells

fill_table_cells("template.hwp", "output.hwp", {
    120: "김태영",
    124: "(주)인공지능팩토리",
    128: "대표이사",
})
```

### CLI 사용

```bash
# 단순 라운드트립 + 검증
python3 ~/.claude/skills/assidocs-hwp/scripts/hwp_roundtrip.py hwp_files/ gen_hwp/ --verify

# 텍스트 치환 + 검증
python3 ~/.claude/skills/assidocs-hwp/scripts/hwp_roundtrip.py hwp_files/ gen_hwp/ \
  --replace replacements.json --verify
```

## 수정 작업 안전 등급

| 작업 | 안전도 | 방법 |
|------|--------|------|
| 빈 셀에 짧은 텍스트 삽입 | ★★★ 안전 | `fill_empty_cell()` (역순 처리) |
| 동일 길이 바이트 치환 (□→■) | ★★★ 안전 | `safe_replace()` |
| 짧은 텍스트→짧은 텍스트 치환 | ★★☆ 보통 | `safe_replace()` + nchars 업데이트 |
| 긴 텍스트 전체 교체 | ★☆☆ 위험 | LINE_SEG 불일치 → 글자 겹침/파일 손상 가능 |
| 확장 제어문자 포함 레코드 수정 | ☆☆☆ 금지 | 구조 손상 → 파일 열리지 않음 |

## HWPX 지원 (hwpx_utils)

### 읽기 및 텍스트 추출

```python
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/assidocs-hwp/scripts'))
from hwpx_utils import read_hwpx

doc = read_hwpx("input.hwpx")
text = doc.extract_all_text()
elements = doc.extract_text_elements()  # 위치 정보 포함
```

### 텍스트 치환

```python
from hwpx_utils import hwpx_replace_text

result = hwpx_replace_text("input.hwpx", "output.hwpx", {
    "김철수": "김태영",
    "(주)ABC": "(주)인공지능팩토리"
})
```

### 양식 채우기 (평가의견서 등)

```python
from hwpx_utils import hwpx_fill_evaluation_form

result = hwpx_fill_evaluation_form(
    src="template.hwpx",
    out="filled.hwpx",
    evaluator_org="AIFactory",
    evaluator_name="김태영",
    evaluator_title="대표이사",
    sections_content={
        "(중점방향1) 활용 분야별 혁신 지원": [
            " ㅇ 첫 번째 의견",
            " ㅇ 두 번째 의견",
        ],
        "(중점방향2) 초고성능컴퓨팅 자원 접근성 강화": [
            " ㅇ 의견 내용",
        ],
    }
)
```

### HWPX 수정 시 주의사항 (필독)

#### linesegarray 문제 (글자 겹침 원인)
- HWPX의 `<hp:linesegarray>`는 HWP의 LINE_SEG와 동일한 역할 — 텍스트 렌더링 레이아웃 정보
- **텍스트를 변경하면서 기존 linesegarray를 유지하면 글자가 겹치거나 깨짐** (실제 검증 완료)
- **해결법**: 새로 넣거나 대폭 변경하는 문단에서 `<hp:linesegarray>...</hp:linesegarray>`를 **제거**하면 한글이 열 때 자동 재계산함
- `replace_cell_content()` 메서드가 자동으로 linesegarray를 제거하므로 안전함
- 단순 텍스트 치환(`replace_text`)은 `<hp:t>` 내용만 바꾸므로 linesegarray에 영향 없이 안전

#### HWPX 수정 안전 등급

| 작업 | 안전도 | 방법 |
|------|--------|------|
| 짧은 텍스트 치환 (동일 길이) | ★★★ 안전 | `replace_text()` |
| 테이블 셀 전체 교체 | ★★★ 안전 | `replace_cell_content()` (linesegarray 자동 제거) |
| 평가의견서 등 양식 채우기 | ★★★ 안전 | `hwpx_fill_evaluation_form()` |
| 길이 변경 치환 + linesegarray 유지 | ☆☆☆ 금지 | 글자 겹침 발생 → 반드시 linesegarray 제거 필요 |

#### HWPX 포맷 요약

| 항목 | 설명 |
|------|------|
| 형식 | ZIP 아카이브 (PK 시그니처) |
| 본문 | `Contents/section0.xml` ~ `sectionN.xml` |
| 텍스트 | `<hp:t>텍스트</hp:t>` (UTF-8, XML 이스케이프) |
| 문단 | `<hp:p>` — paraPrIDRef로 스타일 참조 |
| 글자 속성 | `<hp:run charPrIDRef="N">` — 글자 모양 참조 |
| 레이아웃 | `<hp:linesegarray>` — 줄별 렌더링 위치 (수정 시 제거 권장) |
| 테이블 | `<hp:tbl>` → `<hp:tr>` → `<hp:tc>` → `<hp:subList>` → `<hp:p>` |
| 컬럼 설정 | `<hp:ctrl><hp:colPr>` — 첫 문단에 포함, 수정 시 보존 필수 |

## 제한사항

- **암호화된 HWP/HWPX**는 지원하지 않음
- **손상된 zlib 데이터**가 있는 파일은 읽기 불가
- 이미지/OLE 객체는 텍스트 추출 시 무시됨
- **비압축(uncompressed) HWP**도 정상 처리 (자동 감지)

## 저장 방식

**반드시 `ole_binary_patch()`를 사용**하여 저장합니다:
- 원본 OLE 구조를 바이너리 레벨에서 직접 패치
- DIFAT 체인 지원 (대용량 파일 7MB+)
- 미니스트림/정규 스트림 자동 판별
- `src == out` 인플레이스 패치 지원 (다중 섹션)

**사용 금지 API:**
- `doc.save()` — orig_compressed 캐시 버그로 수정 내용 유실
- `olefile.write_stream` — 원본 크기 초과 시 무시됨
- `_ole_build()` — OLE 구조 불완전 → 한글이 빈 페이지 표시

## HWP 포맷 요약

| 항목 | 설명 |
|------|------|
| 형식 | OLE Compound File (MS-CFB) |
| 본문 | `BodyText/Section0..N`, zlib 압축 (wbits=-15) |
| 레코드 | 4byte 헤더: tag(10) \| level(10) \| size(12) |
| PARA_TEXT | UTF-16LE + 확장 제어문자 (16바이트) |
| PARA_HEADER nchars | bit 0~30: 글자 수, **bit 31: 셀 마지막 문단 플래그** |
| PARA_CHAR_SHAPE | (position, charShapeId) 쌍의 배열. 스타일 범위 지정 |
| PARA_LINE_SEG | 36byte/줄. 한글이 렌더링 시 사용하는 레이아웃 정보 |

## 텍스트 수정 시 주의사항 (필독)

### 1. 확장 제어문자 금지
PARA_TEXT에 0x0001~0x0017 범위의 확장 제어문자(16바이트)가 있으면 **절대 치환 금지**.
`_has_extended_ctrl(rec.data)`로 반드시 확인. 치환 시 구조 손상 → 파일이 열리지 않음.

### 2. LINE_SEG 주의
- LINE_SEG(tag 69)는 36바이트/줄 구조로 한글의 텍스트 렌더링 레이아웃을 담당
- 텍스트 길이를 **대폭 변경**하면(예: 3자 → 100자) LINE_SEG와 불일치 → 글자 겹침 또는 파일 손상
- **안전한 접근**: 텍스트 길이 변경을 최소화하는 바이트 치환(`safe_replace`) 사용
- **위험한 접근**: `replace_para_text()`로 전체 텍스트 교체 시 `update_line_seg()`가 호출되나, 실제 한글 렌더링과 100% 일치하지 않아 파일 손상 가능성 있음

### 3. nchars bit 31 보존
테이블 셀의 마지막 문단 플래그(0x80000000) 필수 보존. 누락 시 한글이 후속 레코드를 잘못 파싱 → 파일 손상.

### 4. 빈 셀 삽입 순서
빈 셀에 레코드를 삽입하면 이후 인덱스가 밀림. **반드시 뒤에서부터(역순)** 처리.
이미 삽입한 후 바이트 치환할 때는 `shifted()` 함수로 인덱스 보정 필요.

### 5. 검증 필수
수정 후 반드시 `read_hwp()`로 다시 읽어 `extract_all_text()`로 내용 확인.
주요 키워드가 포함되어 있는지 assert로 체크.
