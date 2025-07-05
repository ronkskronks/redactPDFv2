import fitz
from PyQt6.QtWidgets import QApplication, QLabel

# Teste básico PyMuPDF
pdf = fitz.open()  # Criar PDF em branco na memória
pdf.new_page()
pdf.close()

# Teste básico PyQt6
app = QApplication([])
label = QLabel("Instalação Ok!")
label.show()
app.exec()

