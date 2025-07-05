# gui/pdf_viewer_widget.py

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QImage, QMouseEvent
from PyQt6.QtCore import Qt, QRectF, QPoint

import fitz  # PyMuPDF
from core.text_extractor import TextExtractor
from business.selection_manager import SelectionManager


class PDFViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Scroll + Label com imagem da página
        self.scroll_area = QScrollArea()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        # Armazena dados para interação
        self.current_page = None
        self.zoom = 1.0
        self.selections = SelectionManager()
        self.bboxes = []  # Lista de (bbox, texto)
        self.image = None

        # Habilita clique
        self.label.mousePressEvent = self.handle_mouse_click

    def render_page(self, page: fitz.Page, zoom: float = 1.0):
        self.current_page = page
        self.zoom = zoom
        self.bboxes = TextExtractor.extract_bboxes(page)

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self.image = QPixmap.fromImage(image)

        # Cria uma cópia para desenhar
        pixmap = QPixmap(self.image)
        painter = QPainter(pixmap)

        for bbox, text in self.bboxes:
            x0, y0, x1, y1 = [coord * zoom for coord in bbox]
            rect = QRectF(x0, y0, x1 - x0, y1 - y0)

            # Verifica se bbox está selecionada
            if self.selections_has(bbox):
                pen = QPen(QColor("blue"))
            else:
                pen = QPen(QColor("red"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(rect)

        painter.end()
        self.label.setPixmap(pixmap)

    def handle_mouse_click(self, event: QMouseEvent):
        if not self.current_page or self.image is None:
            return

        # Corrige coordenada do clique para considerar margem do QLabel
        label_pos = self.label.mapToGlobal(QPoint(0, 0))
        scroll_pos = self.scroll_area.viewport().mapToGlobal(QPoint(0, 0))
        offset_x = max((self.label.width() - self.image.width()) // 2, 0)
        offset_y = max((self.label.height() - self.image.height()) // 2, 0)

        click_pos = event.position().toPoint()
        click_x = (click_pos.x() - offset_x) / self.zoom
        click_y = (click_pos.y() - offset_y) / self.zoom

        for bbox, text in self.bboxes:
            x0, y0, x1, y1 = bbox
            if x0 <= click_x <= x1 and y0 <= click_y <= y1:
                page_index = self.current_page.number

                if self.selections_has(bbox):
                    self.selections.remove_selection(page_index, bbox)
                else:
                    self.selections.add_selection(page_index, bbox, text)

                self.render_page(self.current_page, self.zoom)
                break

    def selections_has(self, bbox):
        page_index = self.current_page.number if self.current_page else -1
        return any(s.page == page_index and s.bbox == bbox for s in self.selections.get_all())

