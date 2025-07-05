# tests/test_redaction_engine.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pdf_processor import PDFProcessor
from core.text_extractor import TextExtractor
from core.redaction_engine import RedactionEngine

def test_redaction_engine():
    current_dir = os.path.dirname(__file__)
    pdf_path = os.path.join(current_dir, "teste.pdf")
    output_path = os.path.join(current_dir, "teste_censurado.pdf")

    # Abre o documento
    processor = PDFProcessor(pdf_path)
    processor.open()

    # Carrega a primeira página e extrai as bboxes
    page = processor.load_page(0)
    bboxes = TextExtractor.extract_bboxes(page)

    # Aplica redaction nos 3 primeiros bboxes como teste
    areas = [(0, bbox) for bbox, _ in bboxes[:3]]
    print(f"Aplicando censura em {len(areas)} trechos...")

    # Aplica censura
    RedactionEngine.apply_redactions(processor.doc, areas)

    # Salva o documento modificado
    processor.doc.save(output_path)
    processor.close()

    print(f"Documento censurado salvo como: {output_path}")

if __name__ == '__main__':
    test_redaction_engine()

