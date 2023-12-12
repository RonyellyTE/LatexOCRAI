from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSignal, QObject, QTimer
import g4f, re, os
import pytesseract
from PIL import Image 
import fitz
from Ateste import extract_images

class WorkerSignals(QObject):
    translated = pyqtSignal(str)
    finished = pyqtSignal()

class APITask(QRunnable):
    def __init__(self, prompt, text):
        super().__init__()

        self.prompt = prompt
        self.text = text
        self.signals = WorkerSignals()

    def run(self):
        print("Ok")
        print(self.text)
        quest = ""
        pattern = re.compile(r'\\begin\{document\}(.*?)\\end\{document\}', re.DOTALL)
        traducao = ""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo_16k,
            messages=[{"role": "user", "content": f"""{self.prompt} {self.text}"""}],
        )
        for message in response:
            quest += message
        '''if quest:
            extract_tex_querry = pattern.search(quest)
            if extract_tex_querry:
                traducao = extract_tex_querry.group(1)'''
        print(quest)
        self.signals.translated.emit(quest)
        self.signals.finished.emit()
    
'''class OCRWorkerSignals(QObject):
    finished = pyqtSignal(str)

class OCRWorker(QRunnable):
    def __init__(self, doc, current_page, img_path, method):
        super().__init__()
        self.current_page = current_page
        self.img_path = img_path
        self.method = method
        self.doc = doc
        self.signals = OCRWorkerSignals()

    def run(self):
        if self.method == "Fitz":
            text = self.perform_fitz(self.img_path)
            self.signals.finished.emit(text)
        elif self.method == "OCR":
            text = self.perform_ocr(self.img_path)
            self.signals.finished.emit(text)
        elif self.method == "OCR Tesseract":
            text = self.perform_ocr_tesseract(self.img_path)
            self.signals.finished.emit(text)

    def perform_fitz(self):
        if self.doc is not None and 0 <= self.current_page < len(self.doc):
            page = self.doc[self.current_page]
            selected_method = self.extract_method_combobox.currentText()

            if selected_method == "Fitz":
                page_img = extract_images(self.doc, self.current_page, page)
                page_text = ""
                for block_extracted1 in page.get_text("blocks"):
                    paragraph = block_extracted1[4]
                    padrao = r"<image: [^>]*width: [^>]*height: [^>]*bpc: [^>]*>"
                    resultado = re.findall(padrao, paragraph)
                    if resultado and page_img:
                        page_text += r"""\begin{figure}
            \centering
            \includegraphics[width=0.8\linewidth]{%s}
            \caption{Sua legenda aqui}
            \label{fig:suafigura}
            \end{figure}
            """ % page_img.pop(0)
                    else:
                        page_text += paragraph
        return page_text

    def perform_ocr(self, img_path):
        text = ""
        img_path = f"trash/page_{self.current_page}.jpg"
        self.doc[self.current_page].get_pixmap().save(img_path, "jpg")
        text = self.perform_ocr(img_path)
        os.remove(img_path)
        return text
        pass

    def perform_ocr_tesseract(self, img_path):
        try:
            texto = pytesseract.image_to_string(Image.open(img_path))
            return texto
        except Exception as e:
            print(f"Erro ao realizar OCR Tesseract: {e}")
            return ""'''
