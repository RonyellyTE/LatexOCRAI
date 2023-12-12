from PyQt5.QtCore import Qt, QRunnable, QCoreApplication
from pix2text import Pix2Text, merge_line_texts
from functools import partial
from PIL import Image
from pix2tex.api.app import predict


class Pix2Work(QRunnable):
    def __init__(self, img_path, callback, viewer_instance):
        super(Pix2Work, self).__init__()
        self.img_path = img_path
        self.callback = callback
        self.viewer_instance = viewer_instance

    def run(self):
        try:
            text = self.perform_ocr(self.img_path)
            callback_partial = partial(self.callback, text)
            if callable(callback_partial):
                callback_partial()

        except Exception as e:
            print(f"Erro no OCR: {e}")

        finally:
            QCoreApplication.processEvents()

    def perform_ocr(self, img_path):
        p2t = Pix2Text(analyzer_config=dict(model_name='mfd'))
        outs = p2t(img_path, resized_shape=1280)
        texto = merge_line_texts(outs, auto_line_break=True)
        
        self.viewer_instance.text_to_copy = texto
        
        return texto
