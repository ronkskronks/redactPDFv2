# gui/main_window.py

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from business.selection_manager import Selection


from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QVBoxLayout, QWidget,
    QPushButton, QLabel, QHBoxLayout, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QRadioButton, QTabWidget, QTextEdit,
    QSplitter, QComboBox, QToolBox
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QRectF
from core.pdf_processor import PDFProcessor
from gui.pdf_viewer_widget import PDFViewerWidget
from core.redaction_engine import RedactionEngine
import pdfplumber
from collections import defaultdict, Counter
from pathlib import Path
import re


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Redact PDF v2.0")
        self.setMinimumSize(1000, 800)

        self.processor = None
        self.current_page = 0
        self.zoom = 1.0
        self.zoom_step = 0.25

        self.viewer = PDFViewerWidget()

        self.selection_list = QListWidget()
        self.selection_list.setMaximumHeight(200)
        self.selection_list.setMinimumHeight(100)
        self.selection_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.nav_label = QLabel("Página: - / -")
        self.prev_button = QPushButton("◀ Anterior")
        self.next_button = QPushButton("Próxima ▶")
        self.zoom_in_btn = QPushButton("🔍 + Zoom")
        self.zoom_out_btn = QPushButton("🔎 - Zoom")
        self.censor_button = QPushButton("Aplicar Censura...")

        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.censor_button.clicked.connect(self._on_censor_button_clicked)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.zoom_in_btn)
        nav_layout.addWidget(self.zoom_out_btn)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.nav_label)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.censor_button)

        nav_container = QWidget()
        nav_container.setLayout(nav_layout)

        # Tab 1: PDF Viewer
        viewer_layout = QVBoxLayout()
        viewer_layout.addWidget(self.viewer)
        viewer_layout.addWidget(nav_container)
        viewer_layout.addWidget(QLabel("Seleções ativas:"))
        viewer_layout.addWidget(self.selection_list)
        viewer_tab = QWidget()
        viewer_tab.setLayout(viewer_layout)

        # Tab 2: Investigação (visor geral)
        investigation_tab = QWidget()
        investigation_layout = QVBoxLayout()
        self.stdout_area = QTextEdit()
        self.stdout_area.setReadOnly(True)
        self.stdout_area.setPlaceholderText("Visor geral da investigação. Resultados combinados aparecerão aqui futuramente...")
        investigation_layout.addWidget(self.stdout_area)
        investigation_tab.setLayout(investigation_layout)

        # Tab 3: Ferramentas (Toolbox com múltiplas ferramentas)
        tools_tab = QWidget()
        tools_layout = QVBoxLayout()
        self.toolbox = QTabWidget()

        # Ferramenta 1 - Fontes e Tamanhos
        font_widget = QWidget()
        font_layout = QVBoxLayout()
        self.analysis_button = QPushButton("📐 Analisar Fontes e Tamanhos")
        self.analysis_button.clicked.connect(self.analyze_fonts_and_sizes)
        self.hardplumb_output = QTextEdit()
        self.hardplumb_output.setReadOnly(True)
        self.hardplumb_output.setPlaceholderText("Relatório de fontes por página...")
        font_layout.addWidget(self.analysis_button)
        font_layout.addWidget(self.hardplumb_output)
        font_widget.setLayout(font_layout)

        # Ferramenta 2 - Metadados
        meta_widget = QWidget()
        meta_layout = QVBoxLayout()
        self.meta_button = QPushButton("📦 Extrair Metadados")
        self.meta_button.clicked.connect(self.extract_metadata)
        self.meta_output = QTextEdit()
        self.meta_output.setReadOnly(True)
        self.meta_output.setPlaceholderText("Metadados extraídos do PDF...")
        meta_layout.addWidget(self.meta_button)
        meta_layout.addWidget(self.meta_output)
        meta_widget.setLayout(meta_layout)

        # Ferramenta 3 - Repetições
        repeat_widget = QWidget()
        repeat_layout = QVBoxLayout()
        self.repeats_button = QPushButton("🔁 Detectar Repetições")
        self.repeats_button.clicked.connect(self.detect_repetitions)
        self.repeats_output = QTextEdit()
        self.repeats_output.setReadOnly(True)
        self.repeats_output.setPlaceholderText("Linhas de texto repetidas...")
        repeat_layout.addWidget(self.repeats_button)
        repeat_layout.addWidget(self.repeats_output)
        repeat_widget.setLayout(repeat_layout)

        # Ferramenta 4 - Mapa de Estrutura
        structure_widget = QWidget()
        structure_layout = QVBoxLayout()
        self.structure_button = QPushButton("🧭 Gerar Mapa de Estrutura")
        self.structure_button.clicked.connect(self.generate_structure_map)
        self.structure_output = QTextEdit()
        self.structure_output.setReadOnly(True)
        self.structure_output.setPlaceholderText("Títulos e seções estruturais detectados...")
        structure_layout.addWidget(self.structure_button)
        structure_layout.addWidget(self.structure_output)
        structure_widget.setLayout(structure_layout)

        # Ferramenta 5 - Estatísticas de Estrutura
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        self.stats_button = QPushButton("📊 Gerar Estatísticas de Estrutura")
        self.stats_button.clicked.connect(self.generate_structure_stats)
        self.stats_output = QTextEdit()
        self.stats_output.setReadOnly(True)
        self.stats_output.setPlaceholderText("Resumo técnico da composição estrutural por página...")
        stats_layout.addWidget(self.stats_button)
        stats_layout.addWidget(self.stats_output)
        stats_widget.setLayout(stats_layout)

        # Ferramenta 6 - Campos Sensíveis na Página 1 ← AQUI
        sensitive_widget = QWidget()
        sensitive_layout = QVBoxLayout()
        self.sensitive_button = QPushButton("🧪 Marcar Campos Sensíveis (Página 1)")
        self.sensitive_button.clicked.connect(self.mark_sensitive_fields_page1)
        self.sensitive_output = QTextEdit()
        self.sensitive_output.setReadOnly(True)
        self.sensitive_output.setPlaceholderText("Campos identificados para censura na página 1...")
        sensitive_layout.addWidget(self.sensitive_button)
        sensitive_layout.addWidget(self.sensitive_output)
        sensitive_widget.setLayout(sensitive_layout)

        # 📜 Plano de Ensaios
        plan_widget = QWidget()
        plan_layout = QVBoxLayout()
        self.plan_button = QPushButton("📜 Extrair Plano de Ensaios")
        self.plan_button.clicked.connect(self.extract_test_plan)
        self.plan_output = QTextEdit()
        self.plan_output.setReadOnly(True)
        self.plan_output.setPlaceholderText("Mapeamento de ensaios por categoria após ANEXO 1...")
        plan_layout.addWidget(self.plan_button)
        plan_layout.addWidget(self.plan_output)
        plan_widget.setLayout(plan_layout)


        # Adiciona ferramentas como abas internas
        self.toolbox.addTab(font_widget, "📐 Fontes")
        self.toolbox.addTab(meta_widget, "📦 Metadados")
        self.toolbox.addTab(repeat_widget, "🔁 Repetições")
        self.toolbox.addTab(structure_widget, "🧭 Estrutura")
        self.toolbox.addTab(stats_widget, "📊 Estatísticas")
        self.toolbox.addTab(sensitive_widget, "🛡️ Sensível")
        self.toolbox.addTab(plan_widget, "📜 Plano de Ensaios")

        tools_layout.addWidget(self.toolbox)
        tools_tab.setLayout(tools_layout)

        # Tab Container Principal
        self.tabs = QTabWidget()
        self.tabs.addTab(viewer_tab, "📄 PDF Viewer")
        self.tabs.addTab(investigation_tab, "🧠 Investigação")
        self.tabs.addTab(tools_tab, "🛠️ Ferramentas")

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self._create_menu()

    def extract_test_plan(self):
        if not self.processor:
            self.plan_output.setPlainText("Nenhum PDF carregado.")
            return

        try:
            in_annex = False
            current_type = None
            plan = defaultdict(list)

            with pdfplumber.open(self.processor.file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue

                    lines = text.split("\n")
                    for line in lines:
                        l = line.strip()
                        if not in_annex and "ANEXO 1" in l.upper():
                            in_annex = True
                            continue
                        if not in_annex:
                            continue

                        if re.match(r"^Ensaios de", l):
                            current_type = l
                            continue
                        if current_type and "Descrição dos ensaios" in l:
                            continue  # ignora linha de cabeçalho
                        if current_type and len(l) > 10:
                            plan[current_type].append(l)

            if not plan:
                self.plan_output.setPlainText("Nenhum plano de ensaios detectado.")
            else:
                resultado = []
                for k, v in plan.items():
                    resultado.append(f"{k}:")
                    for item in v:
                        resultado.append(f"  - {item}")
                    resultado.append("")
                self.plan_output.setPlainText("\n".join(resultado))

        except Exception as e:
            self.plan_output.setPlainText(f"Erro ao extrair plano de ensaios: {e}")

    def mark_sensitive_fields_page1(self):  # ← AQUI
        if not self.processor:
            self.sensitive_output.setPlainText("Nenhum PDF carregado.")
            return

        fields = [
            "N.° da proposta", "Resp.", "Motivo da revisão",
            "Requisitante", "Contato", "OCD", "OCP",
            "E-mail do requisitante", "E-mail do OCD", "Fone",
            "N.° processo", "Modelo"
        ]

        marked = []
        try:
            with pdfplumber.open(self.processor.file_path) as pdf:
                page = pdf.pages[0]
                words = page.extract_words()

                for f in fields:
                    matches = [w for w in words if f.lower() in w['text'].lower()]
                    for m in matches:
                        nearby = [w for w in words if abs(w['top'] - m['top']) < 5 and w['x0'] > m['x1']]
                        if nearby:
                            x0 = m['x1'] + 2
                            x1 = max(w['x1'] for w in nearby)
                            top = min(w['top'] for w in nearby)
                            bottom = max(w['bottom'] for w in nearby)
                            rect = QRectF(x0, top, x1 - x0, bottom - top)
                            sel = Selection(text="[Detectado]", bbox=rect, page=0)
                            bbox = (rect.left(), rect.top(), rect.right(), rect.bottom())
                            self.viewer.selections.add_selection(0, bbox, "[Detectado]")
                           #self.viewer.selections.add_selection(sel.bbox, sel.text, sel.page)
                           #self.viewer.selections.add_selection(rect, "[Detectado]", str(0))
                            marked.append(f"'{f}' em linha: {m['text']} → censura marcada")

            if marked:
                self.sensitive_output.setPlainText("\n".join(marked))
                self.load_current_page()
            else:
                self.sensitive_output.setPlainText("Nenhum campo sensível encontrado.")

        except Exception as e:
            self.sensitive_output.setPlainText(f"Erro: {e}")


    def generate_structure_stats(self):
        if not self.processor:
            self.stats_output.setPlainText("Nenhum PDF carregado.")
            return

        try:
            result = []
            with pdfplumber.open(self.processor.file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    words = page.extract_words()
                    text = page.extract_text()
                    lines = text.split("\n") if text else []
                    num_words = len(words)
                    num_lines = len(lines)
                    avg_words_per_line = round(num_words / num_lines, 2) if num_lines > 0 else 0
                    density = round((num_words / (page.width * page.height)) * 100000, 2)

                    result.append(f"Página {i + 1}:")
                    result.append(f"  - Palavras: {num_words}")
                    result.append(f"  - Linhas: {num_lines}")
                    result.append(f"  - Palavras por linha: {avg_words_per_line}")
                    result.append(f"  - Densidade estimada: {density} (texto/pixel² x100k)")
                    result.append("")

            self.stats_output.setPlainText("\n".join(result))

        except Exception as e:
            self.stats_output.setPlainText(f"Erro ao gerar estatísticas: {e}")

    def generate_structure_map(self):
        if not self.processor:
            self.structure_output.setPlainText("Nenhum PDF carregado.")
            return

        try:
            headings = []
            with pdfplumber.open(self.processor.file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    lines = text.split("\n")
                    for line in lines:
                        clean = line.strip()
                        if len(clean) > 200:
                            continue
                        if re.match(r"^\d+(\.\d+)*\s+", clean) or clean.isupper():
                            headings.append(f"Página {i + 1}: {clean}")

            if not headings:
                self.structure_output.setPlainText("Nenhum título estrutural detectado.")
            else:
                self.structure_output.setPlainText("\n".join(headings))

        except Exception as e:
            self.structure_output.setPlainText(f"Erro ao gerar mapa de estrutura: {e}")


    def _create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Arquivo")

        open_action = QAction("Abrir PDF", self)
        open_action.triggered.connect(self.open_pdf_dialog)

        file_menu.addAction(open_action)

    def open_pdf_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        try:
            self.processor = PDFProcessor(file_path)
            self.processor.open()

            self.current_page = 0
            self.total_pages = self.processor.get_page_count()

            self.load_current_page()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir o PDF:\n{e}")

    def analyze_fonts_and_sizes(self):
        if not self.processor:
            self.hardplumb_output.setPlainText("Nenhum PDF carregado.")
            return

        font_data = defaultdict(lambda: defaultdict(int))

        try:
            with pdfplumber.open(self.processor.file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    for char in page.chars:
                        font = char.get("fontname", "?")
                        size = round(float(char.get("size", 0)), 2)
                        font_data[i + 1][(font, size)] += 1

            result = []
            for page_num, entries in font_data.items():
                result.append(f"Página {page_num}:")
                for (font, size), count in sorted(entries.items(), key=lambda x: -x[1]):
                    result.append(f"  - Fonte: {font}, Tamanho: {size} ({count}x)")
                result.append("")

            self.hardplumb_output.setPlainText("\n".join(result))

        except Exception as e:
            self.hardplumb_output.setPlainText(f"Erro na análise: {e}")

    def extract_metadata(self):
        if not self.processor:
            self.meta_output.setPlainText("Nenhum PDF carregado.")
            return

        try:
            with pdfplumber.open(self.processor.file_path) as pdf:
                meta = pdf.metadata or {}
                result = ["📦 Metadados do PDF:\n"]
                for key, value in meta.items():
                    result.append(f"- {key}: {value}")

            self.meta_output.setPlainText("\n".join(result))

        except Exception as e:
            self.meta_output.setPlainText(f"Erro na extração de metadados: {e}")

    def detect_repetitions(self):
        if not self.processor:
            self.repeats_output.setPlainText("Nenhum PDF carregado.")
            return

        line_counter = Counter()

        try:
            with pdfplumber.open(self.processor.file_path) as pdf:
                for page in pdf.pages:
                    lines = page.extract_text().split("\n") if page.extract_text() else []
                    for line in lines:
                        norm = re.sub(r"\s+", " ", line.strip().lower())
                        if norm:
                            line_counter[norm] += 1

            result = ["🔁 Linhas repetidas:"]
            for text, count in line_counter.most_common():
                if count > 1:
                    result.append(f"- '{text}' → {count}x")

            if len(result) == 1:
                result.append("Nenhuma repetição encontrada.")

            self.repeats_output.setPlainText("\n".join(result))

        except Exception as e:
            self.repeats_output.setPlainText(f"Erro na detecção de repetições: {e}")

    def load_current_page(self):
        if not self.processor:
            return

        page = self.processor.load_page(self.current_page)
        self.viewer.render_page(page, zoom=self.zoom)
        self.nav_label.setText(f"Página: {self.current_page + 1} / {self.total_pages}")
        self._update_buttons()
        self._update_selection_list()

    def _update_selection_list(self):
        self.selection_list.clear()
        for s in self.viewer.selections.get_all():
            text = s.text.replace("\n", " ").strip()
            item = QListWidgetItem(f"Página {s.page + 1} | {text}")
            self.selection_list.addItem(item)

    def go_to_previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_current_page()

    def go_to_next_page(self):
        if self.processor and self.current_page < self.processor.get_page_count() - 1:
            self.current_page += 1
            self.load_current_page()

    def zoom_in(self):
        self.zoom += self.zoom_step
        self.load_current_page()

    def zoom_out(self):
        if self.zoom > self.zoom_step:
            self.zoom -= self.zoom_step
            self.load_current_page()

    def _update_buttons(self):
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)

    def _on_censor_button_clicked(self):
        selections = self.viewer.selections.get_all()
        if not selections:
            QMessageBox.information(self, "Aviso", "Nenhuma seleção para censurar.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Aplicar Censura")
        layout = QVBoxLayout(dialog)

        radio1 = QRadioButton("Aplicar Censura em todas as seleções")
        radio2 = QRadioButton("Aplicar Censura em todas as seleções e ocorrências delas no arquivo")
        radio1.setChecked(True)

        layout.addWidget(radio1)
        layout.addWidget(radio2)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec():
            mode = "selections" if radio1.isChecked() else "occurrences"
            self._apply_censorship(mode, selections)

    def _apply_censorship(self, mode: str, selections: list):
        input_path = self.processor.file_path
        base = Path(input_path).stem
        default_suffix = "_censurado.pdf" if mode == "selections" else "_censurado_ocorrencias.pdf"
        suggested_name = base + default_suffix

        save_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF censurado", suggested_name, "PDF Files (*.pdf)")
        if not save_path:
            return

        try:
            if mode == "selections":
                RedactionEngine.apply_to_selections(input_path, selections, save_path)
            else:
                RedactionEngine.apply_to_selections_and_occurrences(input_path, selections, save_path)
            QMessageBox.information(self, "Sucesso", f"Arquivo salvo com sucesso:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao aplicar censura:\n{e}")

