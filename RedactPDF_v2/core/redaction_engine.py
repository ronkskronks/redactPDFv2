# core/redaction_engine.py

from typing import List, Tuple
import fitz  # PyMuPDF
from business.selection_manager import Selection

BBox = Tuple[float, float, float, float]

class RedactionEngine:
    """Aplica censuras permanentes em regiões especificadas de um documento PDF."""

    @staticmethod
    def apply_redactions(
        doc: fitz.Document,
        redactions: List[Tuple[int, BBox]],
        color: Tuple[int, int, int] = (0, 0, 0)
    ) -> fitz.Document:
        for page_index, bbox in redactions:
            if page_index >= len(doc):
                continue
            page = doc[page_index]
            page.add_redact_annot(bbox, fill=color)

        for page in doc:
            page.apply_redactions()

        return doc

    @staticmethod
    def apply_to_selections(input_path: str, selections: List[Selection], output_path: str):
        doc = fitz.open(input_path)
        redactions = [(s.page, s.bbox) for s in selections]
        RedactionEngine.apply_redactions(doc, redactions)
        doc.save(output_path)
        doc.close()

    @staticmethod
    def apply_to_selections_and_occurrences(input_path: str, selections: List[Selection], output_path: str):
        doc = fitz.open(input_path)
        targets = set(s.text for s in selections if s.text.strip())

        for page_index in range(len(doc)):
            page = doc[page_index]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip() in targets:
                            bbox = tuple(span["bbox"])
                            page.add_redact_annot(bbox, fill=(0, 0, 0))

        for page in doc:
            page.apply_redactions()

        doc.save(output_path)
        doc.close()

