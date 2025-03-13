import sys
from PyQt5 import QtWidgets, uic


def main():
    app = QtWidgets.QApplication(sys.argv)

    # UI 파일 로드
    MainWindow = uic.loadUi("guruma_one.ui")

    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
