from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QLineEdit, QTextEdit, QLabel
from PyQt5.QtCore import Qt
from pykiwoom.kiwoom import Kiwoom
import sys


def get_stock_name(kiwoom, code):
    stock_info = kiwoom.GetMasterCodeName(code)
    return stock_info if stock_info else "알 수 없는 종목"


class KiwoomSellApp(QWidget):
    def __init__(self):
        super().__init__()
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)  # 로그인

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 종목 코드 입력
        self.stock_code_label = QLabel("종목 코드:")
        self.stock_code = QLineEdit()
        layout.addWidget(self.stock_code_label)
        layout.addWidget(self.stock_code)

        # 매도 유형 선택
        self.order_type_label = QLabel("매도 유형:")
        self.order_type = QComboBox()
        self.order_type.addItems(["시장가", "매도가"])
        self.order_type.currentIndexChanged.connect(self.order_type_changed)
        layout.addWidget(self.order_type_label)
        layout.addWidget(self.order_type)

        # 매도가 입력 (매도가 선택 시 활성화)
        self.order_price_label = QLabel("매도가:")
        self.order_price = QLineEdit()
        self.order_price.setDisabled(True)
        layout.addWidget(self.order_price_label)
        layout.addWidget(self.order_price)

        # 수량 입력
        self.order_amount_label = QLabel("수량:")
        self.order_amount = QLineEdit()
        layout.addWidget(self.order_amount_label)
        layout.addWidget(self.order_amount)

        # 매도 버튼
        self.sell_button = QPushButton("매도 주문")
        self.sell_button.clicked.connect(self.sell_stock)
        layout.addWidget(self.sell_button)

        # 로그 창
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)
        self.setWindowTitle("Kiwoom 매도 주문 시스템")

    def order_type_changed(self):
        """ 매도 유형 변경 시 매도가 입력 활성화 여부 설정 """
        if self.order_type.currentText() == "매도가":
            self.order_price.setDisabled(False)
        else:
            self.order_price.setDisabled(True)

    def sell_stock(self):
        """ 매도 주문 실행 """
        stock_code = self.stock_code.text().strip()
        order_type = 1 if self.order_type.currentText() == "시장가" else 0  # 1: 시장가, 0: 지정가
        order_price = self.order_price.text().strip() if order_type == 0 else ""
        order_amount = self.order_amount.text().strip()

        if not stock_code or not order_amount:
            self.log.append("[오류] 종목 코드와 수량을 입력하세요.")
            return

        # 종목명 조회
        stock_name = get_stock_name(self.kiwoom, stock_code)

        # 매도 주문 전송
        order_id = self.kiwoom.SendOrder(
            "매도주문", "0101", self.kiwoom.GetLoginInfo("ACCNO").split(';')[0], 2,
            stock_code, int(order_amount), int(order_price) if order_price else 0,
            order_type, ""
        )

        self.log.append(
            f"[주문] {stock_name} ({stock_code}) 매도 주문 - 가격: {order_price if order_price else '시장가'}, 수량: {order_amount}")

        # 체결 이벤트 감지하여 로그 업데이트
        self.kiwoom.OnReceiveChejanData = self.order_filled

    def order_filled(self, gubun, item_cnt, fid_list):
        """ 체결 완료 시 로그 업데이트 """
        if gubun == "0":  # 체결 정보
            stock_code = self.kiwoom.GetChejanData(9001).strip()[1:]  # 종목코드 앞에 'A'가 붙어있음
            stock_name = get_stock_name(self.kiwoom, stock_code)
            self.log.append(f"[체결] {stock_name} ({stock_code}) 매도 주문 체결 완료")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KiwoomSellApp()
    window.show()
    sys.exit(app.exec_())
