import sys
from PyQt5.QtWidgets import QApplication
from app import * 

def main():
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()