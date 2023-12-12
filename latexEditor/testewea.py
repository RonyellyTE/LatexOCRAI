import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QScrollArea, QLabel, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import fitz  # PyMuPDF
from PIL.ImageQt import ImageQt

class PDFViewer(QMainWindow):
    def __init__(self, pdf_path):
        super().__init__()

        self.pdf_path = pdf_path
        self.pdf_document = fitz.open(self.pdf_path)
        self.total_pages = self.pdf_document.page_count

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PDF Viewer')
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.scroll_area = QScrollArea(self.central_widget)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_content)

        self.page_layout = QVBoxLayout(self.scroll_content)

        for page_num in range(self.total_pages):
            label = QLabel(self.scroll_content)
            page = self.pdf_document[page_num]
            image = page.get_pixmap()

            # Convertendo a imagem Pixmap para QImage
            qimage = QImage(image.samples, image.width, image.height, image.stride, QImage.Format_RGB888)

            # Convertendo a imagem QImage para QPixmap
            pixmap = QPixmap.fromImage(qimage)

            label.setPixmap(pixmap)
            self.page_layout.addWidget(label)

        self.layout.addWidget(self.scroll_area)

    def closeEvent(self, event):
        self.pdf_document.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pdf_path = 'J._E._Thompson_Algebra_for_the_Practical_Man.pdf'  # Substitua pelo caminho do seu PDF
    window = PDFViewer(pdf_path)
    window.show()
    sys.exit(app.exec_())
