#!/usr/bin/env python3
"""
reference.docx 스타일 커스터마이즈 (한국어 제안서용)
- 한국어 폰트 설정 (맑은 고딕 / Apple SD Gothic Neo)
- 제목 색상 설정 (PRIMARY: 1B4F72, ACCENT: 2E86C1)
- 헤더/푸터 (페이지 번호)
"""
import zipfile, os, shutil, re, sys
from xml.etree import ElementTree as ET

NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
}
for prefix, uri in NSMAP.items():
    ET.register_namespace(prefix, uri)

# Also register other common namespaces to avoid ns0, ns1 pollution
for prefix, uri in [
    ('a', 'http://schemas.openxmlformats.org/drawingml/2006/main'),
    ('wp', 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'),
    ('v', 'urn:schemas-microsoft-com:vml'),
    ('o', 'urn:schemas-microsoft-com:office:office'),
    ('m', 'http://schemas.openxmlformats.org/officeDocument/2006/math'),
    ('wps', 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape'),
    ('wpc', 'http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas'),
    ('ct', 'http://schemas.openxmlformats.org/package/2006/content-types'),
    ('rel', 'http://schemas.openxmlformats.org/package/2006/relationships'),
    ('w14', 'http://schemas.microsoft.com/office/word/2010/wordml'),
    ('w15', 'http://schemas.microsoft.com/office/word/2012/wordml'),
    ('wne', 'http://schemas.microsoft.com/office/word/2006/wordml'),
    ('sl', 'http://schemas.openxmlformats.org/schemaLibrary/2006/main'),
]:
    ET.register_namespace(prefix, uri)

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# Platform-aware Korean font
import platform
if platform.system() == 'Darwin':
    KO_FONT = 'Apple SD Gothic Neo'
else:
    KO_FONT = 'Malgun Gothic'

LATIN_FONT = 'Arial'

# Color scheme
PRIMARY = '1B4F72'
ACCENT = '2E86C1'
H3_COLOR = '34495E'

def modify_styles(styles_xml):
    """Modify word/styles.xml for Korean fonts and heading colors."""
    tree = ET.parse(styles_xml)
    root = tree.getroot()

    for style_el in root.findall(f'{W}style'):
        style_id = style_el.get(f'{W}styleId', '')

        # Find or create rPr (run properties)
        rpr = style_el.find(f'{W}rPr')
        if rpr is None:
            rpr = ET.SubElement(style_el, f'{W}rPr')

        # Set fonts for all styles
        rfonts = rpr.find(f'{W}rFonts')
        if rfonts is None:
            rfonts = ET.SubElement(rpr, f'{W}rFonts')
        rfonts.set(f'{W}ascii', LATIN_FONT)
        rfonts.set(f'{W}hAnsi', LATIN_FONT)
        rfonts.set(f'{W}eastAsia', KO_FONT)
        rfonts.set(f'{W}cs', LATIN_FONT)

        # Set heading colors
        if style_id == 'Heading1':
            color = rpr.find(f'{W}color')
            if color is None:
                color = ET.SubElement(rpr, f'{W}color')
            color.set(f'{W}val', PRIMARY)
            # Bold
            bold = rpr.find(f'{W}b')
            if bold is None:
                ET.SubElement(rpr, f'{W}b')
            # Size 32 (16pt)
            sz = rpr.find(f'{W}sz')
            if sz is None:
                sz = ET.SubElement(rpr, f'{W}sz')
            sz.set(f'{W}val', '32')

        elif style_id == 'Heading2':
            color = rpr.find(f'{W}color')
            if color is None:
                color = ET.SubElement(rpr, f'{W}color')
            color.set(f'{W}val', ACCENT)
            bold = rpr.find(f'{W}b')
            if bold is None:
                ET.SubElement(rpr, f'{W}b')
            sz = rpr.find(f'{W}sz')
            if sz is None:
                sz = ET.SubElement(rpr, f'{W}sz')
            sz.set(f'{W}val', '26')

        elif style_id == 'Heading3':
            color = rpr.find(f'{W}color')
            if color is None:
                color = ET.SubElement(rpr, f'{W}color')
            color.set(f'{W}val', H3_COLOR)
            bold = rpr.find(f'{W}b')
            if bold is None:
                ET.SubElement(rpr, f'{W}b')
            sz = rpr.find(f'{W}sz')
            if sz is None:
                sz = ET.SubElement(rpr, f'{W}sz')
            sz.set(f'{W}val', '22')

        # Normal / Body Text - size 10pt (20 half-points)
        elif style_id in ('Normal', 'BodyText'):
            sz = rpr.find(f'{W}sz')
            if sz is None:
                sz = ET.SubElement(rpr, f'{W}sz')
            sz.set(f'{W}val', '20')

    tree.write(styles_xml, xml_declaration=True, encoding='UTF-8')


def add_footer_page_numbers(footer_xml):
    """Add page numbers to footer."""
    # Create a simple footer with centered page number
    content = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:p>
    <w:pPr>
      <w:jc w:val="center"/>
      <w:rPr>
        <w:rFonts w:ascii="{LATIN_FONT}" w:hAnsi="{LATIN_FONT}" w:eastAsia="{KO_FONT}"/>
        <w:sz w:val="16"/>
        <w:color w:val="888888"/>
      </w:rPr>
    </w:pPr>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="{LATIN_FONT}" w:hAnsi="{LATIN_FONT}" w:eastAsia="{KO_FONT}"/>
        <w:sz w:val="16"/>
        <w:color w:val="888888"/>
      </w:rPr>
      <w:t xml:space="preserve">- </w:t>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="{LATIN_FONT}" w:hAnsi="{LATIN_FONT}" w:eastAsia="{KO_FONT}"/>
        <w:sz w:val="16"/>
        <w:color w:val="888888"/>
      </w:rPr>
      <w:fldChar w:fldCharType="begin"/>
    </w:r>
    <w:r>
      <w:instrText> PAGE </w:instrText>
    </w:r>
    <w:r>
      <w:fldChar w:fldCharType="end"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="{LATIN_FONT}" w:hAnsi="{LATIN_FONT}" w:eastAsia="{KO_FONT}"/>
        <w:sz w:val="16"/>
        <w:color w:val="888888"/>
      </w:rPr>
      <w:t xml:space="preserve"> -</w:t>
    </w:r>
  </w:p>
</w:ftr>'''
    with open(footer_xml, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    ref_in = sys.argv[1] if len(sys.argv) > 1 else 'reference.docx'
    ref_out = sys.argv[2] if len(sys.argv) > 2 else ref_in

    tmp_dir = '/tmp/ref_docx_edit'
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    # Unzip
    with zipfile.ZipFile(ref_in, 'r') as z:
        z.extractall(tmp_dir)

    # Modify styles
    styles_path = os.path.join(tmp_dir, 'word', 'styles.xml')
    if os.path.exists(styles_path):
        modify_styles(styles_path)
        print(f'Modified styles: fonts={LATIN_FONT}/{KO_FONT}, colors=H1:{PRIMARY} H2:{ACCENT} H3:{H3_COLOR}')

    # Modify footer (add page numbers)
    footer_files = [f for f in os.listdir(os.path.join(tmp_dir, 'word')) if f.startswith('footer')]
    if footer_files:
        for ff in footer_files:
            footer_path = os.path.join(tmp_dir, 'word', ff)
            add_footer_page_numbers(footer_path)
            print(f'Updated footer: {ff}')
    else:
        print('No footer files found in reference doc')

    # Rezip
    with zipfile.ZipFile(ref_out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, tmp_dir)
                zout.write(file_path, arcname)

    shutil.rmtree(tmp_dir)
    print(f'Saved: {ref_out}')


if __name__ == '__main__':
    main()
