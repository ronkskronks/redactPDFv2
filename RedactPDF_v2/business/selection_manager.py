# business/selection_manager.py

from dataclasses import dataclass, asdict
from typing import List, Tuple
import json

BBox = Tuple[float, float, float, float]

@dataclass
class Selection:
    page: int
    bbox: BBox
    text: str

class SelectionManager:
    """Gerencia as áreas selecionadas para censura."""

    def __init__(self):
        self.selections: List[Selection] = []

    def add_selection(self, page: int, bbox: BBox, text: str):
        """Adiciona uma nova seleção."""
        sel = Selection(page, bbox, text)
        if sel not in self.selections:
            self.selections.append(sel)

    def remove_selection(self, page: int, bbox: BBox):
        """Remove uma seleção com base na página e bbox."""
        self.selections = [
            s for s in self.selections if not (s.page == page and s.bbox == bbox)
        ]

    def clear(self):
        """Remove todas as seleções."""
        self.selections.clear()

    def get_all(self) -> List[Selection]:
        """Retorna todas as seleções atuais."""
        return self.selections.copy()

    def export_to_json(self, path: str):
        """Salva as seleções atuais em um arquivo JSON."""
        data = [asdict(s) for s in self.selections]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

