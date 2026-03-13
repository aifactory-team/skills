#!/usr/bin/env python3
"""DOCX 내 이미지 포함 단락과 Caption 단락을 중앙정렬로 변경"""
import zipfile, os, sys, shutil
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

for p, u in [
    ('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'),
    ('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'),
    ('mc', 'http://schemas.openxmlformats.org/markup-compatibility/2006'),
    ('a', 'http://schemas.openxmlformats.org/drawingml/2006/main'),
    ('wp', 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'),
    ('w14', 'http://schemas.microsoft.com/office/word/2010/wordml'),
    ('w15', 'http://schemas.microsoft.com/office/word/2012/wordml'),
    ('m', 'http://schemas.openxmlformats.org/officeDocument/2006/math'),
    ('v', 'urn:schemas-microsoft-com:vml'),
    ('o', 'urn:schemas-microsoft-com:office:office'),
    ('wps', 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape'),
    ('wpc', 'http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas'),
    ('wpg', 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup'),
    ('wpi', 'http://schemas.microsoft.com/office/word/2010/wordprocessingInk'),
    ('wne', 'http://schemas.microsoft.com/office/word/2006/wordml'),
    ('sl', 'http://schemas.openxmlformats.org/schemaLibrary/2006/main'),
    ('pic', 'http://schemas.openxmlformats.org/drawingml/2006/picture'),
    ('r14', 'http://schemas.microsoft.com/office/powerpoint/2010/main'),
]:
    ET.register_namespace(p, u)

def center_paragraph(para):
    """Set paragraph alignment to center."""
    ppr = para.find(f'{W}pPr')
    if ppr is None:
        ppr = ET.SubElement(para, f'{W}pPr')
        # Insert pPr as first child
        para.remove(ppr)
        para.insert(0, ppr)
    jc = ppr.find(f'{W}jc')
    if jc is None:
        jc = ET.SubElement(ppr, f'{W}jc')
    jc.set(f'{W}val', 'center')

def process(doc_xml_path):
    tree = ET.parse(doc_xml_path)
    root = tree.getroot()
    img_count = 0
    cap_count = 0

    body = root.find(f'{W}body')
    paragraphs = list(body.iter(f'{W}p'))

    for i, para in enumerate(paragraphs):
        # Check if paragraph contains a drawing (image)
        has_drawing = para.find(f'.//{W}drawing') is not None
        if has_drawing:
            center_paragraph(para)
            img_count += 1

            # Also center the next paragraph if it looks like a caption
            # (Pandoc puts Figure N: caption as next paragraph with Caption style)
            if i + 1 < len(paragraphs):
                next_p = paragraphs[i + 1]
                ppr = next_p.find(f'{W}pPr')
                if ppr is not None:
                    pstyle = ppr.find(f'{W}pStyle')
                    if pstyle is not None and 'Caption' in pstyle.get(f'{W}val', ''):
                        center_paragraph(next_p)
                        cap_count += 1
                        continue
                # Even without Caption style, check if it starts with "Figure" or contains caption text
                text_content = ''.join(t.text or '' for t in next_p.iter(f'{W}t'))
                if text_content.strip().startswith(('Figure', '그림', 'Fig')):
                    center_paragraph(next_p)
                    cap_count += 1

        # Also center any paragraph with Caption/ImageCaption style
        ppr = para.find(f'{W}pPr')
        if ppr is not None:
            pstyle = ppr.find(f'{W}pStyle')
            if pstyle is not None and 'Caption' in pstyle.get(f'{W}val', ''):
                center_paragraph(para)
                cap_count += 1

    tree.write(doc_xml_path, xml_declaration=True, encoding='UTF-8')
    return img_count, cap_count

def main():
    docx_path = sys.argv[1]
    tmp_dir = '/tmp/docx_center_img'
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    with zipfile.ZipFile(docx_path, 'r') as z:
        z.extractall(tmp_dir)

    doc_xml = os.path.join(tmp_dir, 'word', 'document.xml')
    img_count, cap_count = process(doc_xml)
    print(f'Centered {img_count} image paragraphs, {cap_count} caption paragraphs')

    with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for r, dirs, files in os.walk(tmp_dir):
            for f in files:
                fp = os.path.join(r, f)
                zout.write(fp, os.path.relpath(fp, tmp_dir))

    shutil.rmtree(tmp_dir)
    print(f'Saved: {docx_path}')

if __name__ == '__main__':
    main()
