"""
HWPX 파일 읽기/쓰기 유틸리티
- HWPX = ZIP 기반 한글 문서 (OOXML 유사)
- Contents/section0.xml 에 본문 포함
- 텍스트 추출, 치환, 테이블 셀 채우기 지원
"""

import zipfile
import re
import shutil
import copy
from xml.etree import ElementTree as ET
from typing import Dict, List, Optional, Tuple

# HWPX XML 네임스페이스
NS = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
    'ha': 'http://www.hancom.co.kr/hwpml/2011/app',
}

# 네임스페이스 등록 (출력 시 ns0: 방지)
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)
# 추가 네임스페이스도 등록
_EXTRA_NS = {
    'hp10': 'http://www.hancom.co.kr/hwpml/2016/paragraph',
    'hhs': 'http://www.hancom.co.kr/hwpml/2011/history',
    'hm': 'http://www.hancom.co.kr/hwpml/2011/master-page',
    'hpf': 'http://www.hancom.co.kr/schema/2011/hpf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'opf': 'http://www.idpf.org/2007/opf/',
    'ooxmlchart': 'http://www.hancom.co.kr/hwpml/2016/ooxmlchart',
    'hwpunitchar': 'http://www.hancom.co.kr/hwpml/2016/HwpUnitChar',
    'epub': 'http://www.idpf.org/2007/ops',
    'config': 'urn:oasis:names:tc:opendocument:xmlns:config:1.0',
}
for prefix, uri in _EXTRA_NS.items():
    ET.register_namespace(prefix, uri)


class HwpxDocument:
    """HWPX 문서 객체"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.sections: Dict[str, str] = {}  # section name -> XML string
        self.other_files: Dict[str, bytes] = {}  # other ZIP entries
        self._read()

    def _read(self):
        """ZIP에서 모든 파일 읽기"""
        with zipfile.ZipFile(self.filepath) as z:
            for name in z.namelist():
                if name.startswith('Contents/section') and name.endswith('.xml'):
                    self.sections[name] = z.read(name).decode('utf-8')
                else:
                    self.other_files[name] = z.read(name)

    def extract_all_text(self) -> str:
        """모든 섹션에서 텍스트 추출"""
        texts = []
        for name in sorted(self.sections.keys()):
            xml_str = self.sections[name]
            # regex 기반 추출 (네임스페이스 문제 회피)
            for m in re.finditer(r'<hp:t>(.*?)</hp:t>', xml_str, re.DOTALL):
                t = m.group(1)
                t = t.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                if t.strip():
                    texts.append(t)
        return '\n'.join(texts)

    def extract_text_elements(self, section: str = 'Contents/section0.xml') -> List[Dict]:
        """텍스트 요소와 위치 정보 추출"""
        xml_str = self.sections.get(section, '')
        elements = []
        for m in re.finditer(r'<hp:t>(.*?)</hp:t>', xml_str, re.DOTALL):
            t = m.group(1)
            t_decoded = t.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            elements.append({
                'text': t_decoded,
                'raw': t,
                'start': m.start(),
                'end': m.end(),
            })
        return elements

    def replace_text(self, old: str, new: str, section: str = 'Contents/section0.xml') -> int:
        """단순 텍스트 치환 (XML 안전하게)"""
        xml_str = self.sections.get(section, '')
        old_escaped = old.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        new_escaped = new.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        count = xml_str.count(old_escaped)
        if count > 0:
            self.sections[section] = xml_str.replace(old_escaped, new_escaped)
        return count

    def replace_cell_content(self, section_xml: str, cell_marker: str,
                             new_lines: List[str],
                             para_pr_id: str = "34",
                             char_pr_id: str = "7") -> str:
        """
        테이블 셀의 내용을 교체.
        cell_marker: 셀을 식별하는 텍스트 (예: "(중점방향1)")
        new_lines: 새로 넣을 텍스트 줄 리스트

        핵심: linesegarray를 제거하여 한글이 열 때 자동 재계산하도록 함
        """
        # cell_marker가 포함된 헤더 행 찾기
        marker_escaped = re.escape(cell_marker.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        marker_match = re.search(marker_escaped, section_xml)
        if not marker_match:
            # Try without XML escaping
            marker_match = re.search(re.escape(cell_marker), section_xml)
        if not marker_match:
            return section_xml

        search_start = marker_match.end()

        # 다음 <hp:subList ...> 찾기 (내용 셀)
        sublist_match = re.search(r'<hp:subList[^>]*>', section_xml[search_start:])
        if not sublist_match:
            return section_xml

        sublist_tag_end = search_start + sublist_match.end()
        sublist_close = section_xml.index('</hp:subList>', sublist_tag_end)

        # colPr 컨트롤 보존
        old_inner = section_xml[sublist_tag_end:sublist_close]
        colpr_match = re.search(
            r'<hp:run charPrIDRef="\d+"><hp:ctrl><hp:colPr[^/]*/></hp:ctrl></hp:run>',
            old_inner
        )
        colpr = colpr_match.group(0) if colpr_match else ''

        # 새 문단 생성 (linesegarray 없이!)
        paras = []
        for i, line in enumerate(new_lines):
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if i == 0:
                # 첫 문단: colPr 포함
                para = (f'<hp:p id="2147483648" paraPrIDRef="32" styleIDRef="0" '
                        f'pageBreak="0" columnBreak="0" merged="0">'
                        f'{colpr}'
                        f'<hp:run charPrIDRef="{char_pr_id}">'
                        f'<hp:t>{escaped}</hp:t></hp:run></hp:p>')
            else:
                para = (f'<hp:p id="2147483648" paraPrIDRef="{para_pr_id}" styleIDRef="0" '
                        f'pageBreak="0" columnBreak="0" merged="0">'
                        f'<hp:run charPrIDRef="{char_pr_id}">'
                        f'<hp:t>{escaped}</hp:t></hp:run></hp:p>')
            paras.append(para)

        new_inner = ''.join(paras)
        return section_xml[:sublist_tag_end] + new_inner + section_xml[sublist_close:]

    def save(self, output_path: str):
        """수정된 HWPX를 새 파일로 저장"""
        with zipfile.ZipFile(self.filepath) as zin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for name in zin.namelist():
                    if name in self.sections:
                        zout.writestr(name, self.sections[name].encode('utf-8'))
                    else:
                        zout.writestr(name, zin.read(name))


def read_hwpx(filepath: str) -> HwpxDocument:
    """HWPX 파일 읽기"""
    return HwpxDocument(filepath)


def hwpx_replace_text(src: str, out: str, replacements: Dict[str, str]) -> Dict:
    """
    HWPX 파일에서 텍스트 치환 후 저장

    Args:
        src: 원본 HWPX 파일 경로
        out: 출력 HWPX 파일 경로
        replacements: {원본텍스트: 새텍스트} 딕셔너리

    Returns:
        {'success': bool, 'replaced': int, 'error': str or None}
    """
    try:
        doc = read_hwpx(src)
        total = 0
        for old, new in replacements.items():
            for section_name in doc.sections:
                total += doc.replace_text(old, new, section_name)
        doc.save(out)
        return {'success': True, 'replaced': total, 'error': None}
    except Exception as e:
        return {'success': False, 'replaced': 0, 'error': str(e)}


def hwpx_fill_evaluation_form(src: str, out: str,
                               evaluator_org: str,
                               evaluator_name: str,
                               evaluator_title: str,
                               sections_content: Dict[str, List[str]]) -> Dict:
    """
    평가의견서 등 양식 HWPX 파일에 내용 채우기

    Args:
        src: 원본 HWPX 양식 파일
        out: 출력 파일 경로
        evaluator_org: 기관명
        evaluator_name: 평가자명
        evaluator_title: 직급/직책
        sections_content: {섹션식별텍스트: [줄1, 줄2, ...]} 딕셔너리

    Returns:
        {'success': bool, 'error': str or None}
    """
    try:
        doc = read_hwpx(src)

        # 평가자 정보 치환
        doc.replace_text('기관명 평가자명', f'{evaluator_org} {evaluator_name}')
        doc.replace_text('(직급 또는 직책)', f'({evaluator_title})')

        # 각 섹션 내용 채우기
        section_key = 'Contents/section0.xml'
        xml = doc.sections[section_key]

        for marker, lines in sections_content.items():
            xml = doc.replace_cell_content(xml, marker, lines)

        doc.sections[section_key] = xml
        doc.save(out)

        # 검증
        verify_doc = read_hwpx(out)
        verify_text = verify_doc.extract_all_text()

        return {'success': True, 'error': None, 'preview': verify_text[:500]}
    except Exception as e:
        return {'success': False, 'error': str(e), 'preview': ''}
