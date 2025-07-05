# tests/test_core.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pdf_processor import PDFProcessor

def test_pdf_processor():

    # Caminho absoluto para o teste.pdf dentro da pasta tests/
    current_dir = os.path.dirname(__file__)
    pdf_path = os.path.join(current_dir, "teste.pdf")

    processor = PDFProcessor(pdf_path)
    processor.open()
    page_count = processor.get_page_count()

    print(f"Número de páginas: {page_count}")
    assert page_count > 0, "O PDF deve conter pelo menos uma página."

    # Testar carregamento da primeira página
    page = processor.load_page(0)
    assert page is not None, "A página não foi carregada corretamente."

    processor.close()
    print("Teste concluído com sucesso.")

if __name__ == '__main__':
    test_pdf_processor()

