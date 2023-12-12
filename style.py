

class Styles:
    @staticmethod
    def set_theme(widget):
        widget.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                color: #ecf0f1;
            }


            QPushButton {
                background-color: #ffffff;
                border: 1px solid black;
                color: black;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
            }


            QPushButton:hover {
                background-color: #808080;
            }


            QLineEdit, QTextEdit {
                background-color: #ffffff;
                color: black;
                border: 1px solid #2c3e50;
                padding: 8px;
                border-radius: 8px;
            }


            QComboBox {
                background-color: #ffffff;
                color: #black;
                border: 1px solid black;
                padding: 8px;
                border-radius: 8px;
            }
            #botaomaisemenos{
             font-size: 5px;
            }
        """)

