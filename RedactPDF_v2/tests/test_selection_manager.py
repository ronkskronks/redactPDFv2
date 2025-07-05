# tests/test_selection_manager.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from business.selection_manager import SelectionManager

def test_selection_manager():
    manager = SelectionManager()

    # Simula 3 seleções em páginas diferentes
    manager.add_selection(0, (10, 10, 50, 50), "Nome Exemplo")
    manager.add_selection(1, (20, 30, 60, 80), "CPF 123")
    manager.add_selection(0, (100, 100, 120, 120), "Outro Nome")

    selections = manager.get_all()
    assert len(selections) == 3

    # Remove uma delas
    manager.remove_selection(1, (20, 30, 60, 80))
    assert len(manager.get_all()) == 2

    # Testa exportação
    current_dir = os.path.dirname(__file__)
    output_path = os.path.join(current_dir, "selecoes.json")
    manager.export_to_json(output_path)
    assert os.path.exists(output_path)

    print("Seleções exportadas com sucesso:", output_path)

if __name__ == '__main__':
    test_selection_manager()

