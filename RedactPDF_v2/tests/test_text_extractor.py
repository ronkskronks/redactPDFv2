# tests/test_text_extractor.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pdf_processor import PDFProcessor
from core.text_extractor import TextExtractor

def test_text_extractor():
    current_dir = os.path.dirname(__file__)
    pdf_path = os.path.join(current_dir, "teste.pdf")

    processor = PDFProcessor(pdf_path)
    processor.open()
    page = processor.load_page(0)

    bboxes = TextExtractor.extract_bboxes(page)

    print(f"Total de caixas de texto na página 0: {len(bboxes)}")

    for bbox, text in bboxes[:5]:  # Mostrar só os primeiros
        print(f"{text} @ {bbox}")

    assert len(bboxes) > 0, "Deve haver caixas de texto na página 0."

    processor.close()

if __name__ == '__main__':
    test_text_extractor()

