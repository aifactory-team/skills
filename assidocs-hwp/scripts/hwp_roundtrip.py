#!/usr/bin/env python3
"""
HWP 라운드트립 엔진: 읽기 → 콘텐츠 치환 → 저장
assidocs-hwp 스킬의 핵심 처리 모듈
"""
import sys, os, zlib, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hwp_utils import (read_hwp, parse_records, records_to_bytes, decode_para_text,
                        encode_para_text, ole_binary_patch, HwpRecord,
                        update_line_seg,
                        TAG_PARA_TEXT, TAG_PARA_HEADER)


def roundtrip_hwp(src_path: str, out_path: str, replacements: dict = None):
    """HWP 파일을 읽고, 텍스트 치환 후 저장.

    Args:
        src_path: 원본 HWP 파일 경로
        out_path: 출력 HWP 파일 경로
        replacements: {old_text: new_text} 딕셔너리. None이면 단순 라운드트립.

    Returns:
        dict: {'success': bool, 'sections': int, 'replaced': int, 'error': str}
    """
    replacements = replacements or {}
    total_replaced = 0

    try:
        doc = read_hwp(src_path)

        # 암호화 체크
        props = struct.unpack('<I', doc.file_header[36:40])[0]
        if props & 0x02:
            return {'success': False, 'sections': 0, 'replaced': 0,
                    'error': '암호화된 파일은 지원하지 않습니다'}

        for si in range(len(doc.sections)):
            records = list(parse_records(doc.sections[si]))

            # 텍스트 치환
            if replacements:
                for ri, rec in enumerate(records):
                    if rec.tag_id != TAG_PARA_TEXT:
                        continue
                    data = rec.data
                    changed = False
                    for old_str, new_str in replacements.items():
                        old_b = old_str.encode('utf-16-le')
                        new_b = new_str.encode('utf-16-le')
                        if old_b in data:
                            data = data.replace(old_b, new_b)
                            changed = True
                            total_replaced += 1
                    if changed:
                        char_diff = (len(data) - len(rec.data)) // 2
                        records[ri] = HwpRecord(rec.tag_id, rec.level, data)
                        # nchars 업데이트
                        if char_diff != 0:
                            for k in range(ri - 1, -1, -1):
                                if records[k].tag_id == TAG_PARA_HEADER:
                                    hdr = bytearray(records[k].data)
                                    old_nc = struct.unpack('<I', hdr[0:4])[0]
                                    flag = old_nc & 0x80000000
                                    count = (old_nc & 0x7FFFFFFF) + char_diff
                                    struct.pack_into('<I', hdr, 0, count | flag)
                                    records[k] = HwpRecord(records[k].tag_id, records[k].level, bytes(hdr))
                                    break
                        # LINE_SEG 업데이트 (글자 겹침 방지)
                        update_line_seg(records, ri, len(data) // 2)

            # 재조립
            rebuilt = records_to_bytes(records)

            # 압축 (원본이 압축 파일일 때만)
            if doc.compressed:
                compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
                stream_data = compressor.compress(rebuilt) + compressor.flush()
            else:
                stream_data = rebuilt

            stream_name = f"Section{si}"
            src = src_path if si == 0 else out_path
            ole_binary_patch(src, out_path, stream_name, stream_data)

        return {'success': True, 'sections': len(doc.sections),
                'replaced': total_replaced, 'error': None}

    except Exception as e:
        return {'success': False, 'sections': 0, 'replaced': 0, 'error': str(e)}


def verify_roundtrip(src_path: str, out_path: str, replacements: dict = None):
    """라운드트립 검증: 원본과 출력의 텍스트 비교.

    Args:
        src_path: 원본 HWP 파일 경로
        out_path: 출력 HWP 파일 경로
        replacements: 적용된 치환 딕셔너리

    Returns:
        dict: {'match': bool, 'diffs': list, 'error': str}
    """
    replacements = replacements or {}

    try:
        doc_orig = read_hwp(src_path)
        doc_new = read_hwp(out_path)

        if len(doc_orig.sections) != len(doc_new.sections):
            return {'match': False,
                    'diffs': [f"섹션 수 불일치: {len(doc_orig.sections)} → {len(doc_new.sections)}"],
                    'error': None}

        all_diffs = []
        for si in range(len(doc_orig.sections)):
            orig_text = doc_orig.extract_all_text(si)
            new_text = doc_new.extract_all_text(si)

            # 치환이 적용된 경우, 원본 텍스트에도 같은 치환을 적용해서 비교
            expected = orig_text
            for old_str, new_str in replacements.items():
                expected = expected.replace(old_str, new_str)

            if expected != new_text:
                orig_lines = expected.split('\n')
                new_lines = new_text.split('\n')
                for li, (a, b) in enumerate(zip(orig_lines, new_lines)):
                    if a != b:
                        all_diffs.append(f"Section{si} L{li}: '{a[:60]}' → '{b[:60]}'")
                if len(orig_lines) != len(new_lines):
                    all_diffs.append(f"Section{si}: 줄 수 {len(orig_lines)} → {len(new_lines)}")

        return {'match': len(all_diffs) == 0, 'diffs': all_diffs[:20], 'error': None}

    except Exception as e:
        return {'match': False, 'diffs': [], 'error': str(e)}


def build_replacements_from_content(content_dir: str) -> dict:
    """content/ 폴더의 md 파일에서 치환 딕셔너리를 구성.
    현재는 개인정보 기반 치환만 지원.
    """
    # 기본 치환 맵 (content/김태영.md, content/aifactory.md에서 파생)
    return {}  # 기본은 빈 딕셔너리 (순수 라운드트립)


if __name__ == '__main__':
    import argparse, glob, json

    parser = argparse.ArgumentParser(description='HWP 라운드트립 처리')
    parser.add_argument('src_dir', help='원본 HWP 디렉토리')
    parser.add_argument('out_dir', help='출력 디렉토리')
    parser.add_argument('--replace', type=str, default=None,
                        help='치환 JSON 파일 경로')
    parser.add_argument('--verify', action='store_true', help='검증 실행')
    args = parser.parse_args()

    replacements = {}
    if args.replace:
        with open(args.replace) as f:
            replacements = json.load(f)

    os.makedirs(args.out_dir, exist_ok=True)
    hwp_files = sorted(glob.glob(os.path.join(args.src_dir, '*.hwp')))

    results = {'pass': 0, 'fail': 0, 'skip': 0, 'errors': []}

    for fpath in hwp_files:
        fname = os.path.basename(fpath)
        out_path = os.path.join(args.out_dir, fname)

        result = roundtrip_hwp(fpath, out_path, replacements)

        if not result['success']:
            results['fail'] += 1
            results['errors'].append({'file': fname, 'error': result['error']})
            continue

        if args.verify:
            vr = verify_roundtrip(fpath, out_path, replacements)
            if vr['match']:
                results['pass'] += 1
            else:
                results['fail'] += 1
                results['errors'].append({'file': fname, 'diffs': vr['diffs']})
        else:
            results['pass'] += 1

    total = results['pass'] + results['fail'] + results['skip']
    print(f"\nPASS: {results['pass']}/{total}  FAIL: {results['fail']}  SKIP: {results['skip']}")
    if results['errors']:
        for e in results['errors'][:10]:
            print(f"  FAIL: {e['file']}: {e.get('error', '')}{', '.join(e.get('diffs', []))[:100]}")
