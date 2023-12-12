import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QDialog, QHBoxLayout, QScrollArea
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, QRunnable, pyqtSignal, QObject, QTimer, QMetaObject, QThreadPool, Q_ARG, pyqtSlot
import fitz
from OCRWork import OCRWorker
from pix2Work import Pix2Work

class NovaJanela(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Equation')

        self.image_path = image_path
        self.img_width = self.img_height = 1  # valores iniciais

        self.label_imagem = QLabel(self)
        self.label_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setWidget(self.label_imagem)

        self.ampliar_img = QPushButton("+", self)
        self.reduzir_img = QPushButton("-", self)
        self.convert_latex = QPushButton("Copy", self)
        self.texandeq = QPushButton("text+eq", self)
        self.ampliar_img.clicked.connect(self.ampliar)
        self.reduzir_img.clicked.connect(self.reduzir)
        self.convert_latex.clicked.connect(self.latex_convert)
        self.texandeq.clicked.connect(self.pix2text_ocr)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.ampliar_img)
        buttons_layout.addWidget(self.reduzir_img)
        buttons_layout.addWidget(self.convert_latex)
        buttons_layout.addWidget(self.texandeq)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)
        layout.addLayout(buttons_layout)

        self.update_image()

    def update_image(self):
        doc = fitz.open(self.image_path)
        page = doc[0]

        matrix = fitz.Matrix(self.img_width, self.img_height)
        pixmap = page.get_pixmap(matrix=matrix)

        img = QImage(pixmap.samples, pixmap.width, pixmap.height, pixmap.stride, QImage.Format.Format_RGB888)
        self.label_imagem.setPixmap(QPixmap(img))

        self.setMinimumSize(self.label_imagem.sizeHint())
        self.adjustSize()  # Ajusta o tamanho da janela

    def pix2text_ocr(self):
        pixworker = Pix2Work(self.image_path, self.result_latex, self)
        QThreadPool.globalInstance().start(pixworker)

    def latex_convert(self):
        worker = OCRWorker(self.image_path, self.result_latex, self)
        QThreadPool.globalInstance().start(worker)

    @pyqtSlot(str)
    def update_clipboard(self, result):
        clipboard = QApplication.clipboard()
        clipboard.setText(result)
        
    def result_latex(self, result):
        print("!")
        print(result)
        
        # Use QMetaObject to invoke the clipboard operation in the main thread
        QMetaObject.invokeMethod(self, "update_clipboard", Qt.QueuedConnection, Q_ARG(str, result))

    def reduzir(self):
        self.img_height -= 0.2
        self.img_width -= 0.2
        self.update_image()
    

    def ampliar(self):
        self.img_height += 0.2
        self.img_width += 0.2
        self.update_image()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = NovaJanela(r'img_teste\trash\screenshot.png')  # Substitua pelo caminho da sua imagem
    viewer.show()
    sys.exit(app.exec())
