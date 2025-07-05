# core/text_extractor.py

from typing import List, Tuple
import fitz  # PyMuPDF

BBox = Tuple[float, float, float, float]
BBoxText = Tuple[BBox, str]

class TextExtractor:
    """Extrai caixas de texto e seus conteúdos de uma página PDF."""

    @staticmethod
    def extract_bboxes(page: fitz.Page) -> List[BBoxText]:
        """
        Extrai todas as caixas de texto (bboxes) de uma página.

        Args:
            page (fitz.Page): Página do PDF.

        Returns:
            List[Tuple[Tuple[float, float, float, float], str]]: Lista de bboxes e textos.
        """
        results = []

        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    bbox = tuple(span["bbox"])  # (x0, y0, x1, y1)
                    results.append((bbox, text))
        
        return results

