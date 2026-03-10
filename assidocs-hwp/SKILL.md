---
name: hwp
description: "HWP 5.0 한글 문서 읽기, 텍스트 추출, 새 HWP 파일 생성. 사용자가 'hwp 읽어', 'hwp 만들어', '한글 파일', '설문 추출', 'hwp 변환', '한글 문서 생성' 등을 요청할 때 사용합니다."
---

# HWP 5.0 한글 문서 처리 스킬

## 개요

HWP 5.0 형식의 한글 문서를 읽고, 텍스트를 추출하고, 테이블 셀을 수정하고, 새 HWP 파일을 생성하는 스킬입니다.

## HWP 파일 구조

HWP 5.0은 OLE Compound File (MS-CFB) 기반의 바이너리 포맷입니다.

### 주요 스트림
- `FileHeader` (256 bytes): 시그니처("HWP Document File"), 버전, 속성(압축/암호화 등)
- `DocInfo`: 문서 메타데이터 (폰트, 스타일, 문단모양, 글자모양 등)
- `BodyText/Section0..N`: 본문 텍스트 및 컨트롤 (zlib 압축)
- `PrvText`: 미리보기 텍스트 (UTF-16LE)
- `PrvImage`: 미리보기 이미지
- `\x05HwpSummaryInformation`: 문서 요약 정보
- `Scripts/`: JScript
- `DocOptions/`: 연결 문서 등

### 레코드 구조
각 스트림(DocInfo, BodyText)은 연속된 레코드로 구성됩니다:
```
Header (4 bytes): tag_id(10bit) | level(10bit) | size(12bit)
  - size == 0xFFF이면 다음 4바이트가 실제 크기 (확장 크기)
Data (size bytes)
```

### 주요 Tag ID
- DocInfo 영역 (HWPTAG_BEGIN=16 기준):
  - 19: FACE_NAME (폰트)
  - 20: BORDER_FILL
  - 21: CHAR_SHAPE (글자모양)
  - 25: PARA_SHAPE (문단모양)
  - 26: STYLE

- BodyText 영역 (HWPTAG_BEGIN+50=66 기준):
  - 66: PARA_HEADER (문단 헤더, 24 bytes)
  - 67: PARA_TEXT (문단 텍스트, UTF-16LE + 제어문자)
  - 68: PARA_CHAR_SHAPE
  - 69: PARA_LINE_SEG
  - 71: CTRL_HEADER (섹션정의/표/그림 등)
  - 72: LIST_HEADER
  - 73: PAGE_DEF
  - 77: TABLE

### PARA_TEXT 제어문자
- 0x0001~0x0003, 0x000B, 0x000C, 0x000E~0x0012, 0x0015~0x0017: 확장 제어문자 (16바이트)
- 0x0004: 필드 시작 (16바이트)
- 0x0009: 탭
- 0x000A: 줄바꿈
- 0x000D: 문단 끝
- 0x0018: 하이픈
- 0x001E: 비분리공백

### PARA_HEADER nchars 필드 (중요!)
PARA_HEADER의 첫 4바이트는 `nchars` 필드이며 이중 용도입니다:
```
비트 0~30: 실제 글자 수
비트 31:   테이블 셀/텍스트박스 내 마지막 문단 플래그 (0x80000000)
```
**테이블 셀 수정 시 반드시 bit 31을 보존해야 합니다!** 이 플래그가 누락되면 한글이 후속 레코드를 잘못 해석하여 파일이 손상됩니다.

## 사용 방법

### 필수 라이브러리
```bash
pip install olefile
```

### hwp_utils.py 위치
`~/.claude/skills/hwp/scripts/hwp_utils.py`에 HWP 읽기/쓰기 라이브러리가 있습니다.

### HWP 읽기 (텍스트 추출)
```python
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/hwp/scripts'))
from hwp_utils import read_hwp

doc = read_hwp("input.hwp")

# 전체 텍스트
text = doc.extract_all_text()

# 구조화된 텍스트 (레코드 레벨 정보 포함)
items = doc.extract_text()
for item in items:
    print(f"[L{item['level']}] {item['text']}")
```

### HWP 쓰기 (새 문서 생성)
```python
from hwp_utils import read_hwp, create_survey_hwp

# 방법 1: 원본에서 설문 내용만 추출하여 새 파일 생성
create_survey_hwp("original.hwp", "output.hwp")

# 방법 2: 원본 템플릿 + 사용자 지정 텍스트
create_survey_hwp("original.hwp", "output.hwp", content_lines=[
    "설문 제목",
    "1. 첫 번째 질문",
    "① 보기 1",
    "② 보기 2",
])

# 방법 3: 직접 조작
doc = read_hwp("template.hwp")
doc.replace_body_text(["문단1", "문단2", "문단3"])
doc.save("output.hwp")
```

### 테이블 셀 수정 (핵심 기능)

원본 HWP의 레이아웃/서식을 그대로 유지하면서 특정 셀의 텍스트만 수정하는 방법입니다.

#### 1단계: 레코드 구조 분석
```python
import struct
from hwp_utils import read_hwp, parse_records, decode_para_text, TAG_PARA_TEXT, TAG_PARA_HEADER

doc = read_hwp("input.hwp")
records = parse_records(doc.sections[0])

# 모든 레코드 덤프
for i, rec in enumerate(records):
    tag_name = {66:'PARA_HDR',67:'PARA_TXT',68:'CHAR_SHP',69:'LINE_SEG',
                71:'CTRL_HDR',72:'LIST_HDR',77:'TABLE'}.get(rec.tag_id, f'TAG{rec.tag_id}')
    txt = ''
    if rec.tag_id == TAG_PARA_TEXT:
        txt = repr(decode_para_text(rec.data).strip()[:60])
    print(f"{i:4d} L{rec.level} {tag_name:10s} sz={rec.size:5d} {txt}")
```

#### 2단계: 빈 셀 찾기
테이블에서 빈 셀은 `LIST_HDR → PARA_HDR → CHAR_SHP → LINE_SEG` 순서로 PARA_TEXT가 없는 패턴입니다.
```python
# 빈 셀 = PARA_HDR 바로 다음이 CHAR_SHP (PARA_TEXT 없음)
empty_cells = []
for i in range(len(records) - 1):
    if (records[i].tag_id == 66 and     # PARA_HDR
        records[i+1].tag_id == 68):      # CHAR_SHP (no PARA_TXT)
        empty_cells.append(i)
```

#### 3단계: 빈 셀에 텍스트 삽입
```python
import struct
from hwp_utils import encode_para_text, HwpRecord, TAG_PARA_TEXT, TAG_PARA_HEADER

def fill_empty_cell(records, para_hdr_idx, text):
    """빈 테이블 셀에 텍스트 삽입. bit 31 보존 필수!"""
    text_data = encode_para_text(text)
    n_chars = len(text) + 1  # +1 for paragraph end (\r)

    # CRITICAL: bit 31 (마지막 문단 플래그) 보존
    orig_nchars = struct.unpack('<I', records[para_hdr_idx].data[0:4])[0]
    n_chars_with_flag = n_chars | (orig_nchars & 0x80000000)

    para_hdr_data = bytearray(records[para_hdr_idx].data)
    struct.pack_into('<I', para_hdr_data, 0, n_chars_with_flag)
    records[para_hdr_idx] = HwpRecord(
        records[para_hdr_idx].tag_id,
        records[para_hdr_idx].level,
        bytes(para_hdr_data)
    )

    new_text_rec = HwpRecord(TAG_PARA_TEXT, records[para_hdr_idx].level + 1, text_data)
    records.insert(para_hdr_idx + 1, new_text_rec)
    return 1  # 삽입된 레코드 수 (인덱스 시프트용)
```

#### 4단계: 기존 텍스트 수정 (체크박스, 마킹)
```python
def replace_in_para_text(records, rec_idx, old_str, new_str):
    """PARA_TEXT 내 텍스트 치환. 같은 바이트 길이일 때 가장 안전."""
    data = records[rec_idx].data
    old_b = old_str.encode('utf-16-le')
    new_b = new_str.encode('utf-16-le')
    if old_b in data:
        new_data = data.replace(old_b, new_b, 1)
        records[rec_idx] = HwpRecord(records[rec_idx].tag_id, records[rec_idx].level, new_data)
        # 바이트 길이가 달라지면 PARA_HDR nchars도 업데이트
        char_diff = (len(new_data) - len(data)) // 2
        if char_diff != 0:
            for k in range(rec_idx - 1, -1, -1):
                if records[k].tag_id == TAG_PARA_HEADER:
                    hdr = bytearray(records[k].data)
                    old_nc = struct.unpack('<I', hdr[0:4])[0]
                    flag = old_nc & 0x80000000
                    count = (old_nc & 0x7FFFFFFF) + char_diff
                    struct.pack_into('<I', hdr, 0, count | flag)
                    records[k] = HwpRecord(records[k].tag_id, records[k].level, bytes(hdr))
                    break
        return True
    return False

def mark_answer(records, rec_idx, marker="✔"):
    """선택된 답변 앞에 마커 추가"""
    rec = records[rec_idx]
    marker_bytes = marker.encode('utf-16-le')
    new_data = marker_bytes + rec.data
    records[rec_idx] = HwpRecord(rec.tag_id, rec.level, new_data)

    # PARA_HDR nchars 업데이트
    for k in range(rec_idx - 1, -1, -1):
        if records[k].tag_id == TAG_PARA_HEADER:
            hdr = bytearray(records[k].data)
            old_nc = struct.unpack('<I', hdr[0:4])[0]
            flag = old_nc & 0x80000000
            count = (old_nc & 0x7FFFFFFF) + len(marker)
            struct.pack_into('<I', hdr, 0, count | flag)
            records[k] = HwpRecord(records[k].tag_id, records[k].level, bytes(hdr))
            break
```

#### 5단계: 저장 (바이너리 패치 방식 - 권장)

**중요**: `olefile.write_stream`은 원본 크기 이하만 쓸 수 있고, `_ole_build`는 OLE 구조가 불완전합니다.
**반드시 `ole_binary_patch()` 또는 `fill_table_cells()`를 사용하세요.**

```python
import zlib
from hwp_utils import records_to_bytes, ole_binary_patch

# 레코드 재조립 및 압축
new_section = records_to_bytes(records)
compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
new_compressed = compressor.compress(new_section) + compressor.flush()

# 바이너리 패치로 저장 (크기 증가해도 안전)
ole_binary_patch("original.hwp", "output.hwp", "Section0", new_compressed)
```

## 테이블 빈 셀 채우기 (간편 API)

```python
from hwp_utils import fill_table_cells

# {PARA_HDR 인덱스: 채울 텍스트} - 자동 역순 처리
fill_table_cells("template.hwp", "output.hwp", {
    120: "김태영",
    124: "(주)인공지능팩토리",
    128: "대표이사",
    132: "790730-1670812",
    136: "1002-229-065829 (우리은행)",
    140: "대전광역시 유성구 용성로20 102동 2301호",
    144: "김태영",
})
```

## 설문조사 HWP 작성 전체 예시

```python
import struct, zlib
from hwp_utils import (read_hwp, parse_records, records_to_bytes, encode_para_text,
                        decode_para_text, HwpRecord, TAG_PARA_TEXT, TAG_PARA_HEADER,
                        ole_binary_patch)

doc = read_hwp("survey_template.hwp")
records = list(parse_records(doc.sections[0]))

# 1. 체크박스: □ → ■ (동일 바이트 길이, 안전)
for i, rec in enumerate(records):
    if rec.tag_id == TAG_PARA_TEXT:
        data = rec.data
        for old, new in [("□ 10~50인", "■ 10~50인"), ("□ 국방 SW", "■ 국방 SW")]:
            old_b, new_b = old.encode('utf-16-le'), new.encode('utf-16-le')
            if old_b in data:
                data = data.replace(old_b, new_b, 1)
        if data != rec.data:
            records[i] = HwpRecord(rec.tag_id, rec.level, data)

# 2. 답변 마킹: ✔ 프리픽스 (nchars +1 필요)
for idx in [233, 313, 382]:
    mark_answer(records, idx, "✔")

# 3. 빈 셀 채우기 (뒤에서부터 처리하여 인덱스 보존)
for para_hdr_idx, text in [(117, "2020"), (108, "주소"), (99, "회사명")]:
    fill_empty_cell(records, para_hdr_idx, text)

# 4. 저장 (바이너리 패치 - 크기 증가해도 안전)
new_section = records_to_bytes(records)
compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
new_compressed = compressor.compress(new_section) + compressor.flush()
ole_binary_patch("survey_template.hwp", "output.hwp", "Section0", new_compressed)
```

## 작업 흐름

1. HWP 파일을 `read_hwp()`로 읽기
2. `extract_text()` 또는 `extract_all_text()`로 내용 확인
3. `parse_records()`로 레코드 구조 분석
4. 수정 작업:
   - 빈 셀 채우기: `fill_empty_cell()` (bit 31 보존)
   - 체크박스 변경: `replace_in_para_text()` (□ → ■)
   - 답변 마킹: `mark_answer()` (✔ 프리픽스)
   - 본문 교체: `replace_body_text()` (전체 교체)
5. 템플릿 복사 방식으로 저장 (OLE 구조 보존)

## 주의사항

- **반드시 `ole_binary_patch()` 또는 `fill_table_cells()`로 저장**: `doc.save()`와 `olefile.write_stream`은 크기 증가 시 실패하며, `_ole_build`는 OLE 구조가 불완전하여 한글이 빈 페이지를 표시함
- **bit 31 필수 보존**: PARA_HEADER nchars의 bit 31은 테이블 셀 마지막 문단 플래그. 누락 시 파일 손상
- **빈 셀 삽입은 뒤에서부터**: 레코드 삽입 시 인덱스가 밀리므로 반드시 역순 처리 (`fill_table_cells`는 자동 역순)
- **체크박스 치환은 동일 길이**: □(U+25A1)→■(U+25A0)는 바이트 길이 동일하여 안전
- **마커 추가 시 nchars 업데이트**: 텍스트 앞에 문자 추가 시 PARA_HDR nchars도 +N
- 암호화된 HWP 파일은 지원하지 않습니다
- 이미지/OLE 객체는 텍스트 추출 시 무시됩니다
- 생성된 HWP 파일은 원본의 DocInfo(폰트/스타일)를 그대로 사용합니다
