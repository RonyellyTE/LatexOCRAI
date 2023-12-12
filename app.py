import sys
import os
import re
import shutil
import pytesseract
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, QTextEdit,
    QHBoxLayout, QLineEdit, QComboBox, QFileDialog, QFrame, QRubberBand, QScrollArea
)
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QThreadPool
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QFont
import cv2
import fitz
from PIL import Image, ImageEnhance
from OCRWork import OCRWorker
from chatgpt import APITask
from window import NovaJanela
from style import Styles

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\20211084010035\trab\tesseract\tesseract.exe"

class BorderOnlyRubberBand(QRubberBand):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(Qt.GlobalColor.black)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.rect())


class PDFViewer(QMainWindow):
    def __init__(self, pdf_path=None):
        super().__init__()
        self.text_to_copy = ""
        self.pdf_path = pdf_path
        self.doc = None
        self.current_page = 0
        self.translation_in_progress = False
        self.display_right = True
        self.selection_mode = False
        self.origin = QPoint(-100, -100)
        self.ocr_thread = QThreadPool.globalInstance()
        self.multiplyer_resolution = self.largura = self.altura = 2

        self.init_ui()


        if pdf_path:
            self.load_pdf(pdf_path)


    def init_ui(self):
        self.setWindowTitle('PDF Viewer')
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.setup_layout()
        self.setup_left_panel()
        self.setup_main_layout()

        Styles.set_theme(self)


    def setup_layout(self):
        self.main_layout = QHBoxLayout(self.central_widget)
        self.left_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.page_nav_layout = QHBoxLayout()


    def setup_left_panel(self):
        font = QFont()
        font.setPointSize(32)
        font.setBold(True)

        self.open_file_button = QPushButton('Selecionar PDF', self)
        self.open_file_button.clicked.connect(self.load_pdf)
        self.left_layout.addWidget(self.open_file_button)

        ampliar_reduzir_layout = QHBoxLayout()

        self.ampliar_button = QPushButton("+", self)
        self.ampliar_button.setFont(font)
        # self.icon_ampliar = QIcon("icone-loupe-gris.png")
        # self.ampliar_button.setIcon(self.icon_ampliar)
        self.ampliar_button.setFixedSize(40, 40)
        self.ampliar_button.setIconSize(QSize(35, 35))
        self.ampliar_button.clicked.connect(self.ampliar_pdf)
        ampliar_reduzir_layout.addWidget(self.ampliar_button)

        self.reduzir_button = QPushButton("-",self)
        self.reduzir_button.setFont(font)
        # self.icon_reduzir = QIcon("icone-loupe-gris.png")
        # self.reduzir_button.setIcon(self.icon_reduzir)
        self.reduzir_button.setFixedSize(40, 40)
        self.reduzir_button.setIconSize(QSize(35, 35))
        self.reduzir_button.clicked.connect(self.reduzir_pdf)
        ampliar_reduzir_layout.addWidget(self.reduzir_button)
        self.ampliar_button.setStyleSheet('color: green; border: 2px solid green;')
        self.reduzir_button.setStyleSheet('color: red; border: 2px solid red; ')

        self.left_layout.addLayout(ampliar_reduzir_layout)


        # self.reduzir_button.setGeometry(rect_amp.x() + self.ampliar_button.width(), rect_amp.bottom() + 5, rect_amp.width() // 3, 40)
        self.prompt_input = QLineEdit(self)
        self.prompt_input.setPlaceholderText("Insira sua prompt aqui")
        self.left_layout.addWidget(self.prompt_input)

        self.extract_method_combobox = QComboBox(self)
        self.extract_method_combobox.addItems(["Fitz", "OCR", "OCR Tesseract"])
        self.left_layout.addWidget(self.extract_method_combobox)

        self.setup_buttons()
        self.setup_text_edit()
        self.setup_page_navigation()
        self.setup_page_display()
    

        spacer_frame = QFrame()
        spacer_frame.setFrameShape(QFrame.Shape.StyledPanel)
        spacer_frame.setFrameShadow(QFrame.Shadow.Sunken)
        self.left_layout.addWidget(spacer_frame)


        self.toggle_button = QPushButton('Alternar Exibição', self)
        self.toggle_button.clicked.connect(self.toggle_display)
        self.toggle_button.setObjectName("toggle_button")
        self.left_layout.addWidget(self.toggle_button)

        self.setup_selection_button()


    def setup_buttons(self):
        self.copy_text_button = QPushButton('Copiar Texto', self)
        self.copy_text_button.clicked.connect(self.copy_text)
        self.button_layout.addWidget(self.copy_text_button)

        self.begin_button = QPushButton('Enviar', self)
        self.begin_button.clicked.connect(self.gpt_conversation)
        self.button_layout.addWidget(self.begin_button)

        self.left_layout.addLayout(self.button_layout)


    def setup_text_edit(self):
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Resultado da tradução")
        self.left_layout.addWidget(self.text_edit)


    def setup_page_navigation(self):
        self.prev_page_button = QPushButton('Página Anterior', self)
        self.prev_page_button.clicked.connect(self.prev_page)
        self.page_nav_layout.addWidget(self.prev_page_button)

        self.next_page_button = QPushButton('Próxima Página', self)
        self.next_page_button.clicked.connect(self.next_page)
        self.page_nav_layout.addWidget(self.next_page_button)

        self.left_layout.addLayout(self.page_nav_layout)


    def setup_page_display(self):
        self.page_display_label = QLabel('Página:', self)
        self.left_layout.addWidget(self.page_display_label)

        self.page_input = QLineEdit(self)
        self.page_input.setPlaceholderText("Número da Página")
        self.page_input.returnPressed.connect(self.go_to_page)
        self.left_layout.addWidget(self.page_input)


    def setup_main_layout(self):
        self.main_layout.addLayout(self.left_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
       
        self.scroll_widget = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_widget)

        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.pdf_viewer = QLabel(self.scroll_widget)
        self.scroll_layout.addWidget(self.pdf_viewer)

        self.main_layout.addWidget(self.scroll_area)

        self.capture_button = QPushButton('Capturar', self)
        self.capture_button.clicked.connect(self.capture_screen)
        self.capture_button.hide()

        self.eqlatex = QPushButton('EqLatex', self)
        self.eqlatex.clicked.connect(self.equation_to_latex)
        self.eqlatex.hide()

        self.tradutor_botton = QPushButton('Traduzir', self)
        self.tradutor_botton.clicked.connect(self.translate_text)
        self.tradutor_botton.hide()
       

    def setup_selection_button(self):
        self.toggle_selection_button = QPushButton('Ativar Modo de Seleção de Imagem', self)
        self.toggle_selection_button.setCheckable(True)
        self.toggle_selection_button.clicked.connect(self.toggle_selection_mode)
        self.left_layout.addWidget(self.toggle_selection_button)

        self.rubber_band = BorderOnlyRubberBand(QRubberBand.Shape.Rectangle, self)


    def load_pdf(self):
        options = QFileDialog.Option.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(None, "Abrir Arquivo", "", "PDF Files (*.pdf);;DJVU Files (*.djvu);;All Files (*)", options=options)
        if file_path:
            self.pdf_path = file_path
            self.doc = fitz.open(self.pdf_path)
            self.current_page = 0
            self.update_page()
        else:
            self.pdf_viewer.clear()
            self.text_edit.clear()

            # self.scroll_area.setEnabled(False)
            # self.scroll_area.setVisible(False)


    def update_page(self, prox_page=True):
        if self.doc is not None and 0 <= self.current_page < len(self.doc):
            for i in range(len(self.doc)):
                img_path = f"trash/page_{i}.png"
                if os.path.exists(img_path):
                    os.remove(img_path)

            page = self.doc[self.current_page]
            pix = page.get_pixmap(matrix=fitz.Matrix(self.largura, self.altura))
            img_path = f"trash/page_{self.current_page}.png"
            pix.save(img_path, "PNG")

            pixmap = QPixmap(img_path)

            if self.display_right:
                self.pdf_viewer.setPixmap(pixmap)
            else:
                self.pdf_viewer.clear()
                self.text_edit.setPlainText(page.get_text())


            if prox_page:
                self.page_input.setText(str(self.current_page + 1))


            self.pdf_viewer.setFixedSize(pixmap.width(), pixmap.height())
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setMinimumSize(pixmap.width(), pixmap.height()//2)
            self.scroll_area.setMaximumSize(pixmap.width(), int(pixmap.height()//1.2))

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def next_page(self):
        if self.doc is not None and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.update_page()

    def go_to_page(self):
        try:
            page_number = int(self.page_input.text()) - 1
            if 0 <= page_number < len(self.doc):
                self.current_page = page_number
                self.update_page()
            else:
                self.page_input.setText(str(self.current_page + 1)) 
        except ValueError:
            self.page_input.setText(str(self.current_page + 1)) 

    def gpt_conversation(self):
        if not self.translation_in_progress:
            self.translation_in_progress = True

            if self.doc is not None:
                page = self.doc[self.current_page]
                text = page.get_text()

                worker = APITask(self.prompt_input.text(), text)
                worker.signals.translated.connect(self.handle_translation)
                worker.signals.finished.connect(self.translation_complete)
                QThreadPool.globalInstance().start(worker)

    def handle_translation(self, translation):
        print(translation)
        self.text_edit.setPlainText(translation)

    def translation_complete(self):
        self.translation_in_progress = False

    def copy_text(self):
        self.text_to_copy=""
        if self.doc is not None and 0 <= self.current_page < len(self.doc):
            page = self.doc[self.current_page]
            selected_method = self.extract_method_combobox.currentText()

            if selected_method == "Fitz":
                page_img = ""
                page_text = ""
                for block_extracted1 in page.get_text("blocks"):
                    paragraph = block_extracted1[4]
                    pattern = r"<image: [^>]*width: [^>]*height: [^>]*bpc: [^>]*>"
                    result = re.findall(pattern, paragraph)
                    # if result and page_img:
                    #     page_text += r"""\begin{figure}
                    #         \centering
                    #         \includegraphics[width=0.8\linewidth]{%s}
                    #         \caption{Sua legenda aqui}
                    #         \label{fig:suafigura}
                    #         \end{figure}
                    #         """ % page_img.pop(0)
                    # else:
                    if result:
                        pass
                    else:
                        page_text += paragraph

                self.text_to_copy = page_text

            elif selected_method == "OCR":
                img_path = f"trash/page_{self.current_page}.png"
                page.get_pixmap().save(img_path, "png")

                def ocr_callback(text):
                    self.text_edit.setPlainText(text)
                    self.text_to_copy = text
               
                self.perform_ocr(img_path, ocr_callback)
               
                return

            elif selected_method == "OCR Tesseract":
                img_path = f"trash/page_{self.current_page}.png"
                self.text_to_copy = self.perform_tesseract(img_path)
            else:
                self.text_to_copy = ""

            clipboard = QApplication.clipboard()
            clipboard.setText(self.text_to_copy)

    def toggle_display(self):
        self.display_right = not self.display_right
        self.update_page(False)

    def toggle_selection_mode(self):
        self.selection_mode = not self.selection_mode
        if self.selection_mode:
            self.toggle_selection_button.setText('Desativar Modo de Seleção')
            self.rubber_band.hide()
            self.origin = QPoint()
            self.capture_button.hide()
            self.eqlatex.hide()
            self.tradutor_botton.hide()
        else:
            self.toggle_selection_button.setText('Ativar Modo de Seleção')
            self.tradutor_botton.hide()
            self.rubber_band.hide()
            self.capture_button.hide()
            self.eqlatex.hide()


    def mousePressEvent(self, event):
        if self.selection_mode and event.button() == Qt.MouseButton.LeftButton:
            self.origin = QPoint(event.pos())
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()


    def mouseMoveEvent(self, event):
        if self.selection_mode and not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())


    def mouseReleaseEvent(self, event):
        if self.selection_mode and event.button() == Qt.MouseButton.LeftButton:
            self.rubber_band.show()
            rect = self.rubber_band.geometry()
            self.capture_button.setGeometry(rect.x(), rect.bottom() + 5, rect.width() // 3, 40)
            self.eqlatex.setGeometry(rect.x() + self.capture_button.width(), rect.bottom() + 5, rect.width() // 3, 40)
            self.tradutor_botton.setGeometry(rect.x() + self.eqlatex.width()*2, rect.bottom() + 5, rect.width() // 3, 40)
            self.capture_button.show()
            self.eqlatex.show()
            self.tradutor_botton.show()
                   
    def capture_screen(self):
        rect = self.rubber_band.geometry()
        
        # Ajustar a região de captura para incluir apenas a área interna da seleção
        adjusted_rect = rect.adjusted(1, 1, -1, -1)
        
        pixmap = self.grab(adjusted_rect)
        
        size = adjusted_rect.size()
        new_size = QSize(size.width() - 1, size.height() - 1)

        image_with_selection = QPixmap(new_size)
        image_with_selection.fill(Qt.white)

        painter = QPainter(image_with_selection)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        image_with_selection.save("img_teste/trash/screenshot.png")

        # Oculta widgets
        self.rubber_band.hide()
        self.capture_button.hide()
        self.tradutor_botton.hide()
        self.eqlatex.hide()

   
    def equation_to_latex(self):
        self.capture_screen()
        #img = Image.open(r'img_teste/trash/screenshot.png')
        equation_window = NovaJanela("img_teste/trash/screenshot.png", self.parent())
        equation_window.exec_()

        # eq = self.model(img)
        # print(eq)

    def show_image(self, pixmap):
        self.pdf_viewer.setPixmap(pixmap)

    def perform_ocr(self, img_path, callback):
        worker = OCRWorker(img_path, callback, self)
        self.ocr_thread.start(worker)

    def ampliar_pdf(self):
        self.altura += 0.2
        self.largura += 0.2
        self.update_page()
   
    def reduzir_pdf(self):
        self.altura -= 0.2
        self.largura -= 0.2
        self.update_page()

    def perform_tesseract(self, img_path):
        img = os.path.abspath(img_path)
        img = cv2.imread(img)
        text = pytesseract.image_to_string(img)
        return text
   
    def translate_text(self):
        self.capture_screen()
        # img = cv2.imread("img_print\screenshot.png")
        # text_to_translate = pytesseract.image_to_string(img)
        # translator_thread = TranslatorThread(text_to_translate)
        # translator_thread.finished.connect(self.update_translation)
        # translator_thread.start()

        # translator_thread.stop()

    def update_translation(self, translated_text):
        self.text_edit.setText(translated_text)
    



