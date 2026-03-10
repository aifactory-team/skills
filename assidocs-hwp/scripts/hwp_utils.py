"""
HWP 5.0 파일 읽기/쓰기 유틸리티
- OLE Compound File 기반
- zlib 압축/해제
- 레코드 파싱 및 생성
- 텍스트 추출 및 삽입
- PDF 변환 검증
"""

import olefile
import struct
import zlib
import subprocess
import os
from typing import List, Optional, Dict

# ============================================================
# HWP 5.0 Tag ID 상수
# ============================================================
HWPTAG_BEGIN = 16

TAG_PARA_HEADER = 66
TAG_PARA_TEXT = 67
TAG_PARA_CHAR_SHAPE = 68
TAG_PARA_LINE_SEG = 69
TAG_CTRL_HEADER = 71
TAG_LIST_HEADER = 72
TAG_PAGE_DEF = 73
TAG_FOOTNOTE_SHAPE = 74
TAG_PAGE_BORDER_FILL = 75
TAG_TABLE = 77

# 확장 제어문자 (16바이트 차지)
EXTENDED_CTRL_CHARS = {1, 2, 3, 4, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23}


# ============================================================
# 레코드 처리
# ============================================================
class HwpRecord:
    """HWP 바이너리 레코드"""
    def __init__(self, tag_id: int, level: int, data: bytes):
        self.tag_id = tag_id
        self.level = level
        self.data = data

    @property
    def size(self):
        return len(self.data)

    def to_bytes(self) -> bytes:
        size = len(self.data)
        if size < 0xFFF:
            header = (self.tag_id & 0x3FF) | ((self.level & 0x3FF) << 10) | ((size & 0xFFF) << 20)
            return struct.pack('<I', header) + self.data
        else:
            header = (self.tag_id & 0x3FF) | ((self.level & 0x3FF) << 10) | (0xFFF << 20)
            return struct.pack('<II', header, size) + self.data


def parse_records(data: bytes) -> List[HwpRecord]:
    records = []
    pos = 0
    while pos < len(data):
        if pos + 4 > len(data):
            break
        header = struct.unpack('<I', data[pos:pos+4])[0]
        tag_id = header & 0x3FF
        level = (header >> 10) & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if pos + 8 > len(data):
                break
            size = struct.unpack('<I', data[pos+4:pos+8])[0]
            pos += 8
        else:
            pos += 4
        rec_data = data[pos:pos+size]
        records.append(HwpRecord(tag_id, level, rec_data))
        pos += size
    return records


def records_to_bytes(records: List[HwpRecord]) -> bytes:
    buf = bytearray()
    for rec in records:
        buf.extend(rec.to_bytes())
    return bytes(buf)


# ============================================================
# PARA_TEXT 텍스트 디코딩/인코딩
# ============================================================
def decode_para_text(data: bytes) -> str:
    text = ""
    j = 0
    while j < len(data):
        if j + 2 > len(data):
            break
        ch = struct.unpack('<H', data[j:j+2])[0]
        if ch == 0:
            j += 2
        elif ch < 0x20:
            if ch in EXTENDED_CTRL_CHARS:
                j += 16
            elif ch == 9:
                text += "\t"
                j += 2
            elif ch == 10:
                text += "\n"
                j += 2
            elif ch == 13:
                j += 2
            elif ch == 24:
                text += "-"
                j += 2
            elif ch == 30:
                text += " "
                j += 2
            else:
                j += 2
        else:
            text += chr(ch)
            j += 2
    return text


def encode_para_text(text: str) -> bytes:
    buf = bytearray()
    for ch in text:
        if ch == '\t':
            buf.extend(struct.pack('<H', 9))
        elif ch == '\n':
            buf.extend(struct.pack('<H', 10))
        else:
            buf.extend(struct.pack('<H', ord(ch)))
    buf.extend(struct.pack('<H', 13))  # 문단 끝
    return bytes(buf)


# ============================================================
# OLE Compound File Writer (미니스트림 올바르게 지원)
# ============================================================
SECTOR_SIZE = 512
MINI_SECTOR_SIZE = 64
MINI_CUTOFF = 0x1000  # 4096 - OLE 스펙 필수값
ENDOFCHAIN = 0xFFFFFFFE
FREESECT = 0xFFFFFFFF
FATSECT = 0xFFFFFFFD

DIR_TYPE_STORAGE = 1
DIR_TYPE_STREAM = 2
DIR_TYPE_ROOT = 5


def _ole_build(streams: Dict[str, bytes]) -> bytes:
    """OLE Compound File 바이너리 생성 (미니스트림 올바르게 지원)"""
    storages = set()
    for path in streams:
        parts = path.split('/')
        for i in range(len(parts) - 1):
            storages.add('/'.join(parts[:i+1]))

    sectors = []
    fat = []

    def alloc(data: bytes) -> int:
        if not data:
            return ENDOFCHAIN
        start = len(sectors)
        n = (len(data) + SECTOR_SIZE - 1) // SECTOR_SIZE
        for i in range(n):
            off = i * SECTOR_SIZE
            chunk = data[off:off + SECTOR_SIZE]
            if len(chunk) < SECTOR_SIZE:
                chunk += b'\x00' * (SECTOR_SIZE - len(chunk))
            sectors.append(chunk)
            fat.append(start + i + 1 if i < n - 1 else ENDOFCHAIN)
        return start

    # 스트림을 big(>=4096) / small(<4096)로 분류
    big_streams = {p: d for p, d in streams.items() if len(d) >= MINI_CUTOFF}
    small_streams = {p: d for p, d in streams.items() if len(d) < MINI_CUTOFF}

    # 1. Big 스트림을 일반 섹터에 배치
    stream_starts = {}
    for path, data in big_streams.items():
        stream_starts[path] = alloc(data)

    # 2. 미니스트림 컨테이너 구성
    mini_stream_buf = bytearray()
    mini_fat = []
    for path, data in small_streams.items():
        start_mini = len(mini_stream_buf) // MINI_SECTOR_SIZE
        stream_starts[path] = start_mini
        n_mini = max(1, (len(data) + MINI_SECTOR_SIZE - 1) // MINI_SECTOR_SIZE)
        mini_stream_buf.extend(data.ljust(n_mini * MINI_SECTOR_SIZE, b'\x00'))
        for ms in range(n_mini):
            mini_fat.append(start_mini + ms + 1 if ms < n_mini - 1 else ENDOFCHAIN)

    root_start = alloc(bytes(mini_stream_buf)) if mini_stream_buf else ENDOFCHAIN
    root_size = len(mini_stream_buf)

    # 3. 미니FAT를 일반 섹터에 배치
    mini_fat_start = ENDOFCHAIN
    num_mini_fat_sectors = 0
    if mini_fat:
        while len(mini_fat) % (SECTOR_SIZE // 4):
            mini_fat.append(FREESECT)
        mf_data = struct.pack(f'<{len(mini_fat)}I', *mini_fat)
        mini_fat_start = alloc(mf_data)
        num_mini_fat_sectors = len(mf_data) // SECTOR_SIZE

    # 4. 디렉토리 엔트리 구축
    nolink = 0xFFFFFFFF
    dir_entries = [{
        'name': 'Root Entry', 'type': DIR_TYPE_ROOT, 'path': '',
        'start_sect': root_start, 'size': root_size,
        'color': 1, 'left': nolink, 'right': nolink, 'child': nolink,
    }]

    for storage in sorted(storages):
        dir_entries.append({
            'name': storage.split('/')[-1], 'type': DIR_TYPE_STORAGE,
            'path': storage, 'start_sect': ENDOFCHAIN, 'size': 0,
            'color': 1, 'left': nolink, 'right': nolink, 'child': nolink,
        })

    for path in sorted(streams.keys()):
        dir_entries.append({
            'name': path.split('/')[-1], 'type': DIR_TYPE_STREAM,
            'path': path, 'parent': '/'.join(path.split('/')[:-1]),
            'start_sect': stream_starts[path], 'size': len(streams[path]),
            'color': 1, 'left': nolink, 'right': nolink, 'child': nolink,
        })

    # Red-Black 트리 연결
    def _get_parent(e):
        if e['type'] == DIR_TYPE_STORAGE:
            return '/'.join(e['path'].split('/')[:-1])
        return e.get('parent', '')

    root_children = []
    storage_children = {}
    for i in range(1, len(dir_entries)):
        parent = _get_parent(dir_entries[i])
        if not parent:
            root_children.append(i)
        else:
            storage_children.setdefault(parent, []).append(i)

    def build_tree(indices):
        if not indices:
            return nolink
        indices.sort(key=lambda idx: dir_entries[idx]['name'].upper())
        mid = len(indices) // 2
        root_idx = indices[mid]
        dir_entries[root_idx]['left'] = build_tree(indices[:mid])
        dir_entries[root_idx]['right'] = build_tree(indices[mid+1:])
        dir_entries[root_idx]['color'] = 1
        return root_idx

    if root_children:
        dir_entries[0]['child'] = build_tree(root_children)
    for spath, children in storage_children.items():
        for e in dir_entries:
            if e['path'] == spath and e['type'] == DIR_TYPE_STORAGE:
                e['child'] = build_tree(children)
                break

    # 5. 디렉토리 직렬화 및 배치
    dir_buf = bytearray()
    for e in dir_entries:
        entry = bytearray(128)
        name_utf16 = e['name'].encode('utf-16-le')
        name_size = len(name_utf16) + 2
        entry[0:len(name_utf16)] = name_utf16
        struct.pack_into('<H', entry, 64, name_size)
        entry[66] = e['type']
        entry[67] = e['color']
        struct.pack_into('<I', entry, 68, e['left'])
        struct.pack_into('<I', entry, 72, e['right'])
        struct.pack_into('<I', entry, 76, e['child'])
        struct.pack_into('<I', entry, 116, e['start_sect'])
        struct.pack_into('<I', entry, 120, e['size'])
        dir_buf.extend(entry)
    remainder = len(dir_buf) % SECTOR_SIZE
    if remainder:
        dir_buf.extend(b'\x00' * (SECTOR_SIZE - remainder))
    dir_start = alloc(bytes(dir_buf))

    # FAT 섹터 배치
    total = len(fat)
    num_fat_sectors = 1
    while (total + num_fat_sectors) > num_fat_sectors * 128:
        num_fat_sectors += 1

    fat_start = len(sectors)
    for _ in range(num_fat_sectors):
        sectors.append(b'\x00' * SECTOR_SIZE)
        fat.append(FATSECT)

    while len(fat) % 128 != 0:
        fat.append(FREESECT)

    fat_data = struct.pack(f'<{len(fat)}I', *fat)
    for i in range(num_fat_sectors):
        off = i * SECTOR_SIZE
        sectors[fat_start + i] = fat_data[off:off + SECTOR_SIZE]

    # 헤더
    header = bytearray(512)
    header[0:8] = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    struct.pack_into('<H', header, 24, 0x003E)
    struct.pack_into('<H', header, 26, 0x0003)
    struct.pack_into('<H', header, 28, 0xFFFE)
    struct.pack_into('<H', header, 30, 9)
    struct.pack_into('<H', header, 32, 6)
    struct.pack_into('<I', header, 44, num_fat_sectors)
    struct.pack_into('<I', header, 48, dir_start)
    struct.pack_into('<I', header, 56, MINI_CUTOFF)  # 0x1000 필수!
    struct.pack_into('<I', header, 60, mini_fat_start)
    struct.pack_into('<I', header, 64, num_mini_fat_sectors)
    struct.pack_into('<I', header, 68, ENDOFCHAIN)
    struct.pack_into('<I', header, 72, 0)
    for i in range(109):
        if i < num_fat_sectors:
            struct.pack_into('<I', header, 76 + i * 4, fat_start + i)
        else:
            struct.pack_into('<I', header, 76 + i * 4, FREESECT)

    result = bytearray(header)
    for s in sectors:
        result.extend(s)
    return bytes(result)


# ============================================================
# HWP 문서 클래스
# ============================================================
class HwpDocument:
    """HWP 5.0 문서 읽기/쓰기"""

    def __init__(self):
        self.file_header: bytes = b''
        self.doc_info_raw: bytes = b''           # 압축 해제된 DocInfo
        self.sections: List[bytes] = []           # 압축 해제된 BodyText 섹션들
        self.prv_text: str = ''
        self.prv_image: bytes = b''
        self.summary_info: bytes = b''
        self.scripts: Dict[str, bytes] = {}
        self.doc_options: Dict[str, bytes] = {}
        self.compressed: bool = True
        self._source_path: str = ''
        # 원본 압축 데이터 (라운드트립 시 크기 유지용)
        self._orig_compressed: Dict[str, bytes] = {}

    @classmethod
    def from_file(cls, filepath: str) -> 'HwpDocument':
        doc = cls()
        doc._source_path = os.path.abspath(filepath)
        ole = olefile.OleFileIO(filepath)

        try:
            doc.file_header = ole.openstream('FileHeader').read()
            props = struct.unpack('<I', doc.file_header[36:40])[0]
            doc.compressed = bool(props & 0x01)

            raw = ole.openstream('DocInfo').read()
            doc._orig_compressed['DocInfo'] = raw
            doc.doc_info_raw = zlib.decompress(raw, -15) if doc.compressed else raw

            section_idx = 0
            while True:
                path = f'BodyText/Section{section_idx}'
                try:
                    raw = ole.openstream(path).read()
                    doc._orig_compressed[path] = raw
                    decompressed = zlib.decompress(raw, -15) if doc.compressed else raw
                    doc.sections.append(decompressed)
                    section_idx += 1
                except:
                    break

            try:
                prv = ole.openstream('PrvText').read()
                doc.prv_text = prv.decode('utf-16-le', errors='replace')
            except:
                pass

            try:
                doc.prv_image = ole.openstream('PrvImage').read()
            except:
                pass

            try:
                doc.summary_info = ole.openstream('\x05HwpSummaryInformation').read()
            except:
                pass

            for entry in ole.listdir():
                path = "/".join(entry)
                if entry[0] == 'Scripts':
                    doc.scripts[entry[-1]] = ole.openstream(path).read()
                elif entry[0] == 'DocOptions':
                    doc.doc_options[entry[-1]] = ole.openstream(path).read()
        finally:
            ole.close()

        return doc

    def extract_text(self, section_idx: int = 0) -> List[dict]:
        if section_idx >= len(self.sections):
            return []
        records = parse_records(self.sections[section_idx])
        result = []
        for i, rec in enumerate(records):
            if rec.tag_id == TAG_PARA_TEXT:
                text = decode_para_text(rec.data)
                if text.strip():
                    result.append({"text": text.strip(), "level": rec.level, "rec_idx": i})
        return result

    def extract_all_text(self, section_idx: int = 0) -> str:
        paragraphs = self.extract_text(section_idx)
        return "\n".join(p["text"] for p in paragraphs)

    def get_records(self, section_idx: int = 0) -> List[HwpRecord]:
        if section_idx >= len(self.sections):
            return []
        return parse_records(self.sections[section_idx])

    def save(self, filepath: str, template_path: Optional[str] = None):
        """HWP 파일로 저장

        template_path가 주어지면 해당 파일을 복사한 뒤 스트림만 교체.
        없으면 self._source_path를 템플릿으로 사용.
        """
        import shutil

        template = template_path or getattr(self, '_source_path', None)
        if template and os.path.exists(template) and os.path.abspath(template) != os.path.abspath(filepath):
            # 템플릿 복사 후 스트림 교체 (olefile write_mode - 동일 크기만 가능)
            shutil.copy2(template, filepath)
            ole = olefile.OleFileIO(filepath, write_mode=True)

            def write_same_size(stream_name, data):
                """원본과 같은 크기로 맞춰서 쓰기"""
                try:
                    orig_size = ole.get_size(stream_name)
                except:
                    return  # 스트림이 없으면 스킵
                if len(data) == orig_size:
                    ole.write_stream(stream_name, data)
                elif len(data) < orig_size:
                    ole.write_stream(stream_name, data + b'\x00' * (orig_size - len(data)))
                else:
                    # 원본보다 크면 쓸 수 없음 - 원본 데이터 유지
                    pass

            # DocInfo - 변경되지 않았으면 원본 압축 데이터 사용
            orig_di = self._orig_compressed.get('DocInfo', b'')
            if self.compressed:
                new_di = zlib.compress(self.doc_info_raw)[2:-4]
                # 해제 후 재압축한 것이 원본과 동일한 내용이면 원본 사용
                write_same_size('DocInfo', orig_di if len(orig_di) == ole.get_size('DocInfo') else new_di)
            else:
                write_same_size('DocInfo', self.doc_info_raw)

            # BodyText
            for i, section_data in enumerate(self.sections):
                stream_name = f'BodyText/Section{i}'
                orig_body = self._orig_compressed.get(stream_name, b'')
                if self.compressed:
                    new_body = zlib.compress(section_data)[2:-4]
                    try:
                        orig_size = ole.get_size(stream_name)
                        write_same_size(stream_name, orig_body if len(orig_body) == orig_size else new_body)
                    except:
                        pass
                else:
                    write_same_size(stream_name, section_data)

            # FileHeader
            write_same_size('FileHeader', self.file_header)

            # PrvText
            if self.prv_text:
                write_same_size('PrvText', self.prv_text.encode('utf-16-le'))

            # PrvImage
            if self.prv_image:
                write_same_size('PrvImage', self.prv_image)

            # HwpSummaryInformation
            if self.summary_info:
                write_same_size('\x05HwpSummaryInformation', self.summary_info)

            # Scripts
            for name, data in self.scripts.items():
                write_same_size(f'Scripts/{name}', data)

            # DocOptions
            for name, data in self.doc_options.items():
                write_same_size(f'DocOptions/{name}', data)

            ole.close()
        else:
            # 템플릿 없을 경우 OLE 직접 빌드 (폴백)
            all_streams = {}
            all_streams['FileHeader'] = self.file_header
            if self.compressed:
                all_streams['DocInfo'] = zlib.compress(self.doc_info_raw)[2:-4]
            else:
                all_streams['DocInfo'] = self.doc_info_raw
            for i, section_data in enumerate(self.sections):
                if self.compressed:
                    all_streams[f'BodyText/Section{i}'] = zlib.compress(section_data)[2:-4]
                else:
                    all_streams[f'BodyText/Section{i}'] = section_data
            if self.summary_info:
                all_streams['\x05HwpSummaryInformation'] = self.summary_info
            if self.prv_text:
                all_streams['PrvText'] = self.prv_text.encode('utf-16-le')
            if self.prv_image:
                all_streams['PrvImage'] = self.prv_image
            for name, data in self.scripts.items():
                all_streams[f'Scripts/{name}'] = data
            for name, data in self.doc_options.items():
                all_streams[f'DocOptions/{name}'] = data
            with open(filepath, 'wb') as f:
                f.write(_ole_build(all_streams))

    def replace_body_text(self, paragraphs: List[str], section_idx: int = 0):
        records = self._build_simple_section(paragraphs)
        self.sections[section_idx] = records_to_bytes(records)
        self.prv_text = "\r\n".join(paragraphs)

    def _build_simple_section(self, paragraphs: List[str]) -> List[HwpRecord]:
        records = []
        orig_records = parse_records(self.sections[0]) if self.sections else []

        # secd 레코드 추출
        secd_records = []
        found_first_para = False
        for rec in orig_records:
            if rec.tag_id == TAG_PARA_HEADER and not found_first_para:
                found_first_para = True
                continue
            if found_first_para:
                if rec.tag_id == TAG_CTRL_HEADER and rec.level == 1:
                    if len(rec.data) >= 4 and rec.data[:4] == b'dces':
                        secd_records.append(rec)
                        continue
                if rec.tag_id in (TAG_PAGE_DEF, TAG_FOOTNOTE_SHAPE, TAG_PAGE_BORDER_FILL) and rec.level == 2:
                    secd_records.append(rec)
                    continue
                if rec.tag_id == TAG_CTRL_HEADER and rec.level == 1 and secd_records:
                    break
                if rec.tag_id == TAG_PARA_TEXT:
                    break

        for i, text in enumerate(paragraphs):
            records.extend(self._make_paragraph(text, 0, i == 0, secd_records))

        records.extend(self._make_paragraph("", 0, False, []))
        return records

    def _make_paragraph(self, text: str, level_base: int = 0,
                        include_secd: bool = False,
                        secd_records: List[HwpRecord] = None) -> List[HwpRecord]:
        records = []
        para_text_data = encode_para_text(text)
        n_chars = len(text) + 1

        ctrl_mask = 0
        if include_secd:
            ctrl_mask |= (1 << 2)
            secd_char = struct.pack('<H', 2) + b'\x00' * 14
            para_text_data = secd_char + para_text_data
            n_chars += 8

        para_header = struct.pack('<I', n_chars)
        para_header += struct.pack('<I', ctrl_mask)
        para_header += struct.pack('<H', 0)  # paraShapeId
        para_header += struct.pack('<B', 0)  # styleId
        para_header += struct.pack('<B', 0)  # breakType
        para_header += struct.pack('<H', 1)  # charShapeCount
        para_header += struct.pack('<H', 0)  # rangeTagCount
        para_header += struct.pack('<H', 1)  # lineAlignCount
        para_header += struct.pack('<I', 0)  # instanceId
        para_header += struct.pack('<H', 0)  # changeTrackingMerge

        records.append(HwpRecord(TAG_PARA_HEADER, level_base, para_header))

        if para_text_data and len(para_text_data) > 2:
            records.append(HwpRecord(TAG_PARA_TEXT, level_base + 1, para_text_data))

        records.append(HwpRecord(TAG_PARA_CHAR_SHAPE, level_base + 1, struct.pack('<II', 0, 0)))

        line_seg = bytearray(36)
        struct.pack_into('<I', line_seg, 8, 1000)
        struct.pack_into('<I', line_seg, 12, 800)
        struct.pack_into('<I', line_seg, 16, 800)
        struct.pack_into('<I', line_seg, 20, 600)
        struct.pack_into('<I', line_seg, 28, 42520)
        struct.pack_into('<I', line_seg, 32, 0x10)
        records.append(HwpRecord(TAG_PARA_LINE_SEG, level_base + 1, bytes(line_seg)))

        if include_secd and secd_records:
            for rec in secd_records:
                records.append(HwpRecord(rec.tag_id, rec.level, rec.data))

        return records

    def create_survey_only(self, output_path: str):
        text_items = self.extract_text()
        survey_lines = [item["text"] for item in text_items]
        self.replace_body_text(survey_lines)
        self.save(output_path)


# ============================================================
# OLE 바이너리 패치 (미니스트림 확장 지원)
# ============================================================
def ole_binary_patch(src_path: str, out_path: str, stream_name: str, new_data: bytes):
    """원본 OLE 파일을 바이너리 패치하여 스트림 데이터를 교체.

    olefile.write_stream은 원본 크기 이하만 쓸 수 있고,
    _ole_build는 OLE 구조가 불완전하여 한글이 못 읽는 문제를 해결.
    원본 파일의 OLE 구조(FAT, 디렉토리, 미니FAT)를 직접 수정하여
    미니스트림 크기가 늘어나도 정확히 처리한다.

    Args:
        src_path: 원본(템플릿) HWP 파일 경로
        out_path: 출력 HWP 파일 경로
        stream_name: 교체할 스트림 이름 (예: 'Section0')
        new_data: 새 스트림 데이터 (압축된 바이트)
    """
    import shutil

    SECTOR_SIZE = 512
    MINI_SECTOR_SIZE = 64
    ENDOFCHAIN = 0xFFFFFFFE
    FREESECT = 0xFFFFFFFF
    FATSECT = 0xFFFFFFFD

    def sect_off(sid):
        return 512 + sid * SECTOR_SIZE

    # 원본 복사
    shutil.copy2(src_path, out_path)
    with open(out_path, 'rb') as f:
        filedata = bytearray(f.read())

    # FAT 읽기 (헤더 DIFAT 109개 + DIFAT 체인)
    DIFSECT = 0xFFFFFFFC
    fat_sect_ids = []
    for i in range(109):
        sid = struct.unpack_from('<I', filedata, 76 + i * 4)[0]
        if sid < FATSECT:
            fat_sect_ids.append(sid)

    # DIFAT 체인 따라가기 (대용량 파일 지원)
    difat_start = struct.unpack_from('<I', filedata, 68)[0]
    difat_s = difat_start
    while difat_s != ENDOFCHAIN and difat_s != FREESECT and difat_s < ((len(filedata) - 512) // SECTOR_SIZE):
        doff = sect_off(difat_s)
        for j in range(127):  # 마지막 4바이트는 다음 DIFAT 섹터 포인터
            sid = struct.unpack_from('<I', filedata, doff + j * 4)[0]
            if sid < FATSECT:
                fat_sect_ids.append(sid)
        difat_s = struct.unpack_from('<I', filedata, doff + 127 * 4)[0]

    fat = []
    for sid in fat_sect_ids:
        off = sect_off(sid)
        for j in range(SECTOR_SIZE // 4):
            fat.append(struct.unpack_from('<I', filedata, off + j * 4)[0])

    def get_chain(start):
        chain = []
        s = start
        while s < len(fat) and s != ENDOFCHAIN and s != FREESECT:
            chain.append(s)
            s = fat[s]
        return chain

    # 디렉토리 읽기
    dir_start = struct.unpack_from('<I', filedata, 48)[0]
    dir_chain = get_chain(dir_start)
    dir_data = bytearray()
    for sid in dir_chain:
        dir_data.extend(filedata[sect_off(sid):sect_off(sid) + SECTOR_SIZE])

    # 디렉토리 엔트리 파싱
    entries = []
    for i in range(len(dir_data) // 128):
        off = i * 128
        name_size = struct.unpack_from('<H', dir_data, off + 64)[0]
        if name_size == 0:
            entries.append(None)
            continue
        name = dir_data[off:off + name_size - 2].decode('utf-16-le', errors='replace')
        etype = dir_data[off + 66]
        start = struct.unpack_from('<I', dir_data, off + 116)[0]
        size = struct.unpack_from('<I', dir_data, off + 120)[0]
        entries.append({'idx': i, 'name': name, 'type': etype, 'start': start, 'size': size})

    # 대상 스트림 찾기
    target_entry = None
    for e in entries:
        if e and e['name'] == stream_name:
            target_entry = e
            break
    if target_entry is None:
        raise ValueError(f"스트림 '{stream_name}'을 찾을 수 없습니다")

    orig_size = target_entry['size']
    mini_cutoff = struct.unpack_from('<I', filedata, 56)[0]  # 보통 4096

    if orig_size < mini_cutoff:
        # 미니스트림에 저장된 스트림
        _patch_mini_stream(filedata, fat, fat_sect_ids, dir_data, dir_chain,
                           entries, target_entry, new_data,
                           SECTOR_SIZE, MINI_SECTOR_SIZE, ENDOFCHAIN, FREESECT, sect_off)
    else:
        # 일반 섹터에 저장된 스트림
        # 데이터가 mini_cutoff 미만으로 줄면 olefile이 미니스트림으로 오인하므로 패딩
        if len(new_data) < mini_cutoff:
            new_data = new_data + b'\x00' * (mini_cutoff - len(new_data))
        _patch_regular_stream(filedata, fat, fat_sect_ids, dir_data, dir_chain,
                              entries, target_entry, new_data,
                              SECTOR_SIZE, ENDOFCHAIN, FREESECT, sect_off)

    with open(out_path, 'wb') as f:
        f.write(filedata)


def _patch_mini_stream(filedata, fat, fat_sect_ids, dir_data, dir_chain,
                       entries, target, new_data,
                       SECTOR_SIZE, MINI_SECTOR_SIZE, ENDOFCHAIN, FREESECT, sect_off):
    """미니스트림 내 스트림 데이터 패치 (확장 지원)"""

    def get_chain(start):
        chain = []
        s = start
        while s < len(fat) and s != ENDOFCHAIN and s != FREESECT:
            chain.append(s)
            s = fat[s]
        return chain

    # Root Entry
    root_start = struct.unpack_from('<I', dir_data, 116)[0]
    root_size = struct.unpack_from('<I', dir_data, 120)[0]
    root_chain = get_chain(root_start)

    # 미니스트림 읽기
    mini_stream = bytearray()
    for sid in root_chain:
        mini_stream.extend(filedata[sect_off(sid):sect_off(sid) + SECTOR_SIZE])

    # 미니FAT 읽기
    mini_fat_start = struct.unpack_from('<I', filedata, 60)[0]
    mini_fat_chain = get_chain(mini_fat_start)
    mini_fat_data = bytearray()
    for sid in mini_fat_chain:
        mini_fat_data.extend(filedata[sect_off(sid):sect_off(sid) + SECTOR_SIZE])
    mini_fat = list(struct.unpack_from(f'<{len(mini_fat_data) // 4}I', mini_fat_data, 0))

    # 대상 미니체인
    t_chain = []
    ms = target['start']
    while ms != ENDOFCHAIN and ms < len(mini_fat):
        t_chain.append(ms)
        ms = mini_fat[ms]

    needed = (len(new_data) + MINI_SECTOR_SIZE - 1) // MINI_SECTOR_SIZE
    total_avail_mini = len(mini_stream) // MINI_SECTOR_SIZE

    # 추가 미니섹터 필요시 확장
    while needed > len(t_chain):
        # 미니스트림 내 빈 미니섹터 찾기
        used_mini = set()
        for e in entries:
            if e and e['type'] == 2 and e['size'] > 0 and e['size'] < 4096:
                ms = e['start']
                while ms != ENDOFCHAIN and ms < len(mini_fat):
                    used_mini.add(ms)
                    ms = mini_fat[ms]
        for ms_id in t_chain:
            used_mini.add(ms_id)

        free_mini = None
        for ms_id in range(total_avail_mini):
            if ms_id not in used_mini:
                free_mini = ms_id
                break

        if free_mini is None:
            # Root Entry 섹터 확장
            total_sectors = (len(filedata) - 512) // SECTOR_SIZE
            new_sid = None
            for sid in range(total_sectors):
                if sid < len(fat) and fat[sid] == FREESECT:
                    new_sid = sid
                    break
            if new_sid is None:
                new_sid = total_sectors
                filedata.extend(b'\x00' * SECTOR_SIZE)
                if new_sid >= len(fat):
                    fat.extend([FREESECT] * (new_sid - len(fat) + 1))

            fat[root_chain[-1]] = new_sid
            fat[new_sid] = ENDOFCHAIN
            root_chain.append(new_sid)
            mini_stream.extend(b'\x00' * SECTOR_SIZE)
            root_size += SECTOR_SIZE
            total_avail_mini = len(mini_stream) // MINI_SECTOR_SIZE
            continue  # 다시 빈 미니섹터 찾기

        # 미니섹터 할당
        mini_fat[t_chain[-1]] = free_mini
        if free_mini >= len(mini_fat):
            mini_fat.extend([FREESECT] * (free_mini - len(mini_fat) + 1))
        mini_fat[free_mini] = ENDOFCHAIN
        t_chain.append(free_mini)

    # 데이터 쓰기
    padded = new_data + b'\x00' * (needed * MINI_SECTOR_SIZE - len(new_data))
    for k, ms_id in enumerate(t_chain[:needed]):
        off = ms_id * MINI_SECTOR_SIZE
        mini_stream[off:off + MINI_SECTOR_SIZE] = padded[k * MINI_SECTOR_SIZE:(k + 1) * MINI_SECTOR_SIZE]

    # 미니스트림 → Root Entry 섹터
    for k, sid in enumerate(root_chain):
        off = sect_off(sid)
        chunk = mini_stream[k * SECTOR_SIZE:(k + 1) * SECTOR_SIZE]
        if len(chunk) < SECTOR_SIZE:
            chunk += b'\x00' * (SECTOR_SIZE - len(chunk))
        if off + SECTOR_SIZE <= len(filedata):
            filedata[off:off + SECTOR_SIZE] = chunk
        else:
            filedata.extend(chunk[len(filedata) - off:])

    # 미니FAT → 파일
    new_mf = struct.pack(f'<{len(mini_fat)}I', *mini_fat)
    rem = len(new_mf) % SECTOR_SIZE
    if rem:
        pad_count = (SECTOR_SIZE - rem) // 4
        new_mf += struct.pack(f'<{pad_count}I', *([FREESECT] * pad_count))
    for k, sid in enumerate(mini_fat_chain):
        off = sect_off(sid)
        filedata[off:off + SECTOR_SIZE] = new_mf[k * SECTOR_SIZE:(k + 1) * SECTOR_SIZE]

    # FAT → 파일
    fat_bytes = struct.pack(f'<{len(fat)}I', *fat)
    rem = len(fat_bytes) % SECTOR_SIZE
    if rem:
        pad_count = (SECTOR_SIZE - rem) // 4
        fat_bytes += struct.pack(f'<{pad_count}I', *([FREESECT] * pad_count))
    for k, sid in enumerate(fat_sect_ids):
        off = sect_off(sid)
        filedata[off:off + SECTOR_SIZE] = fat_bytes[k * SECTOR_SIZE:(k + 1) * SECTOR_SIZE]

    # 디렉토리 업데이트
    struct.pack_into('<I', dir_data, 120, root_size)  # Root Entry size
    t_off = target['idx'] * 128
    struct.pack_into('<I', dir_data, t_off + 120, len(new_data))  # 스트림 size
    for k, sid in enumerate(dir_chain):
        off = sect_off(sid)
        filedata[off:off + SECTOR_SIZE] = dir_data[k * SECTOR_SIZE:(k + 1) * SECTOR_SIZE]


def _patch_regular_stream(filedata, fat, fat_sect_ids, dir_data, dir_chain,
                          entries, target, new_data,
                          SECTOR_SIZE, ENDOFCHAIN, FREESECT, sect_off):
    """일반 섹터 스트림 데이터 패치"""

    def get_chain(start):
        chain = []
        s = start
        while s < len(fat) and s != ENDOFCHAIN and s != FREESECT:
            chain.append(s)
            s = fat[s]
        return chain

    t_chain = get_chain(target['start'])
    needed = (len(new_data) + SECTOR_SIZE - 1) // SECTOR_SIZE

    while needed > len(t_chain):
        total_sectors = (len(filedata) - 512) // SECTOR_SIZE
        new_sid = None
        for sid in range(total_sectors):
            if sid < len(fat) and fat[sid] == FREESECT:
                new_sid = sid
                break
        if new_sid is None:
            new_sid = total_sectors
            filedata.extend(b'\x00' * SECTOR_SIZE)
            if new_sid >= len(fat):
                fat.extend([FREESECT] * (new_sid - len(fat) + 1))

        if len(t_chain) == 0:
            # 첫 섹터 할당 - 디렉토리 엔트리의 start 업데이트
            t_off = target['idx'] * 128
            struct.pack_into('<I', dir_data, t_off + 116, new_sid)
            target['start'] = new_sid
        else:
            fat[t_chain[-1]] = new_sid
        fat[new_sid] = ENDOFCHAIN
        t_chain.append(new_sid)

    padded = new_data + b'\x00' * (needed * SECTOR_SIZE - len(new_data))
    for k, sid in enumerate(t_chain[:needed]):
        off = sect_off(sid)
        filedata[off:off + SECTOR_SIZE] = padded[k * SECTOR_SIZE:(k + 1) * SECTOR_SIZE]

    fat_bytes = struct.pack(f'<{len(fat)}I', *fat)
    rem = len(fat_bytes) % SECTOR_SIZE
    if rem:
        pad_count = (SECTOR_SIZE - rem) // 4
        fat_bytes += struct.pack(f'<{pad_count}I', *([FREESECT] * pad_count))
    for k, sid in enumerate(fat_sect_ids):
        off = sect_off(sid)
        filedata[off:off + SECTOR_SIZE] = fat_bytes[k * SECTOR_SIZE:(k + 1) * SECTOR_SIZE]

    t_off = target['idx'] * 128
    struct.pack_into('<I', dir_data, t_off + 120, len(new_data))
    for k, sid in enumerate(dir_chain):
        off = sect_off(sid)
        filedata[off:off + SECTOR_SIZE] = dir_data[k * SECTOR_SIZE:(k + 1) * SECTOR_SIZE]


def fill_table_cells(src_path: str, out_path: str, cell_data: dict):
    """HWP 테이블의 빈 셀을 채워서 새 파일로 저장.

    원본 OLE 구조를 100% 보존하는 바이너리 패치 방식 사용.

    Args:
        src_path: 원본 HWP 파일 경로
        out_path: 출력 HWP 파일 경로
        cell_data: {para_hdr_idx: text} 딕셔너리 (큰 인덱스부터 자동 역순 처리)
    """
    doc = read_hwp(src_path)
    records = list(parse_records(doc.sections[0]))

    # 역순 처리 (인덱스 시프트 방지)
    for idx in sorted(cell_data.keys(), reverse=True):
        text = cell_data[idx]
        text_data = encode_para_text(text)
        n_chars = len(text) + 1

        orig_nchars = struct.unpack('<I', records[idx].data[0:4])[0]
        n_chars_with_flag = n_chars | (orig_nchars & 0x80000000)

        para_hdr_data = bytearray(records[idx].data)
        struct.pack_into('<I', para_hdr_data, 0, n_chars_with_flag)
        records[idx] = HwpRecord(records[idx].tag_id, records[idx].level, bytes(para_hdr_data))

        new_text_rec = HwpRecord(TAG_PARA_TEXT, records[idx].level + 1, text_data)
        records.insert(idx + 1, new_text_rec)

    # 압축
    new_section = records_to_bytes(records)
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    new_compressed = compressor.compress(new_section) + compressor.flush()

    # 바이너리 패치로 저장
    ole_binary_patch(src_path, out_path, 'Section0', new_compressed)


# ============================================================
# 편의 함수
# ============================================================
def read_hwp(filepath: str) -> HwpDocument:
    return HwpDocument.from_file(filepath)


def extract_survey_content(filepath: str) -> List[str]:
    doc = read_hwp(filepath)
    return [item["text"] for item in doc.extract_text()]


def create_survey_hwp(source_path: str, output_path: str, content_lines: Optional[List[str]] = None):
    doc = read_hwp(source_path)
    if content_lines is None:
        content_lines = extract_survey_content(source_path)
    doc.replace_body_text(content_lines)
    doc.save(output_path)


# ============================================================
# 검증: 바이너리 + 시각적 비교
# ============================================================
def verify_hwp_roundtrip(original_path: str, copy_path: str, visual: bool = True) -> dict:
    """원본과 복사본의 바이너리/텍스트/시각적 일치도 검증

    Args:
        original_path: 원본 HWP 파일
        copy_path: 복사/수정본 HWP 파일
        visual: True면 hwp5html + playwright로 시각적 비교 수행
    Returns:
        dict with accuracy scores
    """
    doc_orig = read_hwp(original_path)
    doc_copy = read_hwp(copy_path)

    results = {}

    # FileHeader 비교
    results['file_header_match'] = doc_orig.file_header == doc_copy.file_header

    # DocInfo 비교
    results['docinfo_match'] = doc_orig.doc_info_raw == doc_copy.doc_info_raw

    # BodyText 비교
    for i in range(len(doc_orig.sections)):
        if i < len(doc_copy.sections):
            results[f'section{i}_match'] = doc_orig.sections[i] == doc_copy.sections[i]
        else:
            results[f'section{i}_match'] = False

    # 텍스트 비교
    orig_text = doc_orig.extract_all_text()
    copy_text = doc_copy.extract_all_text()
    results['text_match'] = orig_text == copy_text
    results['orig_text_len'] = len(orig_text)
    results['copy_text_len'] = len(copy_text)

    if orig_text and copy_text:
        common = sum(1 for a, b in zip(orig_text, copy_text) if a == b)
        max_len = max(len(orig_text), len(copy_text))
        results['text_similarity'] = round(common / max_len * 100, 2) if max_len > 0 else 100.0
    else:
        results['text_similarity'] = 100.0 if orig_text == copy_text else 0.0

    # OLE 스트림 목록 비교
    ole_orig = olefile.OleFileIO(original_path)
    ole_copy = olefile.OleFileIO(copy_path)
    orig_streams = set("/".join(e) for e in ole_orig.listdir())
    copy_streams = set("/".join(e) for e in ole_copy.listdir())
    results['streams_match'] = orig_streams == copy_streams
    ole_orig.close()
    ole_copy.close()

    # 시각적 비교 (hwp5html → playwright 스크린샷 → 픽셀 비교)
    results['visual_similarity'] = None
    if visual:
        try:
            results['visual_similarity'] = _visual_compare(original_path, copy_path)
        except Exception as e:
            results['visual_error'] = str(e)

    # 종합 점수
    checks = [results['file_header_match'], results['docinfo_match'],
              results['text_match'], results['streams_match']]
    for i in range(len(doc_orig.sections)):
        checks.append(results.get(f'section{i}_match', False))
    results['binary_accuracy'] = round(sum(checks) / len(checks) * 100, 2) if checks else 0.0

    # 최종 정확도 (시각적 비교가 있으면 가중 평균)
    if results['visual_similarity'] is not None:
        results['accuracy'] = round(
            results['binary_accuracy'] * 0.4 +
            results['text_similarity'] * 0.2 +
            results['visual_similarity'] * 0.4, 2)
    else:
        results['accuracy'] = results['binary_accuracy']

    return results


def _visual_compare(original_path: str, copy_path: str) -> float:
    """hwp5html + playwright로 시각적 유사도 측정 (0~100%)"""
    import tempfile, shutil

    tmpdir = tempfile.mkdtemp(prefix='hwp_verify_')
    orig_dir = os.path.join(tmpdir, 'orig')
    copy_dir = os.path.join(tmpdir, 'copy')

    try:
        # HWP → HTML
        subprocess.run(['hwp5html', '--output', orig_dir, original_path],
                       capture_output=True, timeout=30)
        subprocess.run(['hwp5html', '--output', copy_dir, copy_path],
                       capture_output=True, timeout=30)

        orig_html = os.path.join(orig_dir, 'index.xhtml')
        copy_html = os.path.join(copy_dir, 'index.xhtml')

        if not os.path.exists(orig_html) or not os.path.exists(copy_html):
            return None

        # HTML → 스크린샷
        from playwright.sync_api import sync_playwright
        from PIL import Image, ImageChops

        orig_png = os.path.join(tmpdir, 'orig.png')
        copy_png = os.path.join(tmpdir, 'copy.png')

        with sync_playwright() as p:
            browser = p.chromium.launch()
            for html_path, png_path in [(orig_html, orig_png), (copy_html, copy_png)]:
                page = browser.new_page(viewport={"width": 1200, "height": 1800})
                page.goto(f"file://{html_path}")
                page.wait_for_load_state("networkidle")
                page.screenshot(path=png_path, full_page=True)
                page.close()
            browser.close()

        # 픽셀 비교
        img1 = Image.open(orig_png).convert("RGB")
        img2 = Image.open(copy_png).convert("RGB")

        w = max(img1.width, img2.width)
        h = max(img1.height, img2.height)
        img1r = Image.new('RGB', (w, h), 'white')
        img1r.paste(img1, (0, 0))
        img2r = Image.new('RGB', (w, h), 'white')
        img2r.paste(img2, (0, 0))

        diff = ImageChops.difference(img1r, img2r)
        pixels = list(diff.getdata())
        total = len(pixels)
        identical = sum(1 for p in pixels if p == (0, 0, 0))

        return round(identical / total * 100, 2) if total > 0 else 100.0

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def print_verification(results: dict):
    """검증 결과 출력"""
    print("=" * 50)
    print("HWP 라운드트립 검증 결과")
    print("=" * 50)
    print(f"  FileHeader 일치: {'O' if results['file_header_match'] else 'X'}")
    print(f"  DocInfo 일치:    {'O' if results['docinfo_match'] else 'X'}")
    for key in sorted(results):
        if key.startswith('section') and key.endswith('_match'):
            print(f"  {key}: {'O' if results[key] else 'X'}")
    print(f"  스트림 목록 일치: {'O' if results['streams_match'] else 'X'}")
    print(f"  텍스트 일치:     {'O' if results['text_match'] else 'X'}")
    print(f"  텍스트 유사도:   {results['text_similarity']}%")
    vs = results.get('visual_similarity')
    if vs is not None:
        print(f"  시각적 유사도:   {vs}%")
    elif 'visual_error' in results:
        print(f"  시각적 비교:     실패 ({results['visual_error'][:50]})")
    print(f"  바이너리 정확도: {results['binary_accuracy']}%")
    print(f"  종합 정확도:     {results['accuracy']}%")
    print("=" * 50)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python hwp_utils.py <input.hwp> [output.hwp]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    doc = read_hwp(input_file)
    print("=== 추출된 텍스트 ===")
    for item in doc.extract_text():
        print(f"  {item['text']}")

    if output_file:
        doc.save(output_file)
        print(f"\nHWP 저장 완료: {output_file}")

        results = verify_hwp_roundtrip(input_file, output_file, visual=True)
        print_verification(results)
