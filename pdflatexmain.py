from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QScrollArea, QLabel, QMessageBox, QFileDialog, QDialog
)
from PyQt5.QtGui import QKeySequence, QImage, QPixmap, QSyntaxHighlighter, QTextCharFormat, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRegExp
import fitz
from pylatex import Document, Command, Section, Package
import sys
import os
import subprocess
from style import Styles

pdflatex_path = r'miktex\miktex\bin\x64\pdflatex.exe'

from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont
from PyQt5.QtCore import Qt, QRegExp

class LatexSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlighting_rules = []

        command_format = QTextCharFormat()
        command_format.setForeground(Qt.darkGreen)
        command_format.setFontWeight(QFont.Bold)

        brace_format = QTextCharFormat()
        brace_format.setForeground(Qt.red)
        brace_format.setFontWeight(QFont.Bold)

        comment_format = QTextCharFormat()
        comment_format.setForeground(Qt.darkGray)
        comment_format.setFontItalic(True)

        command_rule = QRegExp('\\\\[a-zA-Z]+')
        self.highlighting_rules.append((command_rule, command_format))

        braces = ['{', '}']

        for brace in braces:
            rule = QRegExp(brace)
            self.highlighting_rules.append((rule, brace_format))

        comment_rule = QRegExp('%[^\n]*')
        self.highlighting_rules.append((comment_rule, comment_format))

    def highlightBlock(self, text):
        for pattern, char_format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)

            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, char_format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)


class LatexCompilerThread(QThread):
    compilation_finished = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        self.pdflatex_path = pdflatex_path

    def set_text(self, text):
        self.text = text

    def run(self):
        try:
            output_path = 'output_pdf/output.tex'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.text)

            # doc = Document(output_path)
            # doc.generate_pdf("output.pdf", compiler=self.pdflatex_path, clean_tex=True)
            process = subprocess.run([self.pdflatex_path, output_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if process.returncode == 0:
                self.compilation_finished.emit(True, 'output.pdf')
            else:
                error_message = f"Erro durante a compilação. Consulte a saída abaixo:{process.stderr}"
                print(error_message)
                self.compilation_finished.emit(False, error_message)
        except subprocess.TimeoutExpired:
            error_message = "Tempo limite excedido durante a compilação."
            print(error_message)
            self.compilation_finished.emit(False, error_message)
        except Exception as e:
            error_message = f"Ocorreu um erro: {str(e)}"
            print(error_message)
            self.compilation_finished.emit(False, error_message)

class LatexEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.initUI()

    def initUI(self):
        self.current_page = 0
        self.setWindowTitle('LaTeX Editor')
        self.setGeometry(100, 100, 1200, 600)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setPlaceholderText("Digite seu código LaTeX aqui...")

        self.create_document_button = QPushButton('Criar Documento', self)
        self.create_document_button.clicked.connect(self.create_document)

        self.compile_button = QPushButton('Compilar', self)
        self.compile_button.setShortcut(QKeySequence("Ctrl+R"))
        self.compile_button.clicked.connect(self.compile_document)

        self.save_button = QPushButton('Salvar', self)
        self.save_button.setShortcut(QKeySequence.Save)
        self.save_button.clicked.connect(self.save_document)

        self.open_button = QPushButton('Abrir', self)
        self.open_button.setShortcut(QKeySequence.Open)
        self.open_button.clicked.connect(self.open_document)

        self.fullscreen_button = QPushButton('Tela Cheia', self)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)

        self.pdf_viewer = QLabel(self)
        self.pdf_viewer.setAlignment(Qt.AlignCenter)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.pdf_viewer)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.create_document_button)
        buttons_layout.addWidget(self.compile_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.open_button)
        buttons_layout.addWidget(self.fullscreen_button)

        editor_viewer_layout = QHBoxLayout()
        editor_viewer_layout.addWidget(self.text_edit)
        editor_viewer_layout.addWidget(self.scroll_area)

        main_layout = QVBoxLayout()
        main_layout.addLayout(buttons_layout)
        main_layout.addLayout(editor_viewer_layout)

        container = QWidget(self)
        container.setLayout(main_layout)
        self.setLayout(main_layout)

        self.compile_thread = LatexCompilerThread()
        self.compile_thread.compilation_finished.connect(self.handle_compilation_finished)

        self.syntax_highlighter = LatexSyntaxHighlighter(self.text_edit.document())

        
    def create_document(self):
        self.doc = Document()
        self.doc.preamble.append(Command('title', 'Meu Documento LaTeX'))
        self.doc.preamble.append(Command('author', 'Seu Nome'))
        self.doc.preamble.append(Command('date', '\\today'))
        self.doc.append(Section('Introdução'))
        self.doc.append('Digite seu conteúdo LaTeX aqui...')
        self.doc.preamble.append(Package('inputenc', options=['utf8']))
        self.doc.preamble.append(Package('graphicx'))

        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Documento LaTeX", "", "Arquivos LaTeX (*.tex)")

        if file_path:
            if not file_path.endswith(".tex"):
                file_path += ".tex"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.doc.dumps())

            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.text_edit.setPlainText(content)
            if file_path:
                self.file_path = file_path

    def compile_document(self):
        self.current_page = self.scroll_area.verticalScrollBar().value()
        text = self.text_edit.toPlainText()
        self.compile_thread.set_text(text)
        self.compile_thread.start()

    def handle_compilation_finished(self, success, result):
        if success:
            self.display_pdf(result)
            self.scroll_area.verticalScrollBar().setValue(self.current_page)
        else:
            self.show_error_message(result)

    def display_pdf(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        total_pages = pdf_document.page_count

        content_widget = QWidget()
        page_layout = QVBoxLayout(content_widget)

        for page_num in range(total_pages):
            label = QLabel(content_widget)
            pdf_page = pdf_document[page_num]
            image = pdf_page.get_pixmap()

            qimage = QImage(image.samples, image.width, image.height, image.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            label.setPixmap(pixmap)
            page_layout.addWidget(label)

        content_widget.setLayout(page_layout)
        self.scroll_area.setWidget(content_widget)

        self.scroll_area.closeEvent = lambda event: pdf_document.close() or event.accept()

    def save_document(self):
        if self.file_path:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())

            print(f"Documento LaTeX salvo em {self.file_path}")
        else:
            self.save_document_as()

    def save_document_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Documento LaTeX", "", "Arquivos LaTeX (*.tex)")

        if file_path:
            if not file_path.endswith(".tex"):
                file_path += ".tex"

            self.file_path = file_path
            text = self.text_edit.toPlainText()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"Documento LaTeX salvo em {file_path}")

    def show_error_message(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Erro de Compilação")
        error_dialog.setText("Ocorreu um erro durante a compilação do código LaTeX.")
        error_dialog.setDetailedText(message)
        error_dialog.exec_()

    def open_document(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo LaTeX", "", "Arquivos LaTeX (*.tex)")

        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.text_edit.setPlainText(content)
            self.file_path = file_path
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setText("Tela Cheia")
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("Reduzir")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = LatexEditor()
    editor.show()
    sys.exit(app.exec_())
