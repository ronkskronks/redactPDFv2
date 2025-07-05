# core/pdf_processor.py

import fitz  # PyMuPDF

class PDFProcessor:
    """Responsável pela manipulação básica de documentos PDF."""

    def __init__(self, file_path: str):
        """
        Inicializa o processador, abrindo o documento PDF especificado.

        Args:
            file_path (str): Caminho completo para o arquivo PDF a ser aberto.
        """
        self.file_path = file_path
        self.doc = None

    def open(self):
        """Abre o arquivo PDF usando PyMuPDF e armazena o documento aberto."""
        try:
            self.doc = fitz.open(self.file_path)
        except Exception as e:
            raise FileNotFoundError(f"Erro ao abrir o PDF: {e}")

    def get_page_count(self) -> int:
        """Retorna a quantidade de páginas no PDF aberto."""
        if self.doc is None:
            raise ValueError("Nenhum PDF aberto. Chame o método open() primeiro.")
        return self.doc.page_count

    def load_page(self, page_number: int) -> fitz.Page:
        """
        Carrega uma página específica do documento.

        Args:
            page_number (int): Número da página a ser carregada (0-indexado).

        Returns:
            fitz.Page: Objeto da página especificada.
        """
        if self.doc is None:
            raise ValueError("Nenhum PDF aberto. Chame o método open() primeiro.")
        if page_number < 0 or page_number >= self.doc.page_count:
            raise IndexError("Número da página fora dos limites.")
        return self.doc.load_page(page_number)

    def close(self):
        """Fecha o documento PDF e libera recursos."""
        if self.doc is not None:
            self.doc.close()
            self.doc = None

