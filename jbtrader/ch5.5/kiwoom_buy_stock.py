import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QLabel, QComboBox, QTextEdit
from pykiwoom.kiwoom import Kiwoom


class KiwoomAPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kiwoom Stock Buyer")
        self.setGeometry(100, 100, 500, 300)

        # Kiwoom API 객체 생성
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)  # 로그인 실행 (블록킹 방식)

        # UI 요소 설정
        self.stock_label = QLabel("종목코드:", self)
        self.stock_label.move(20, 30)
        self.StockCode = QLineEdit(self)
        self.StockCode.setGeometry(100, 30, 100, 20)

        self.qty_label = QLabel("수량:", self)
        self.qty_label.move(20, 70)
        self.OrderAmount = QLineEdit(self)
        self.OrderAmount.setGeometry(100, 70, 100, 20)

        self.price_label = QLabel("가격:", self)
        self.price_label.move(20, 110)
        self.OrderPrice = QLineEdit(self)
        self.OrderPrice.setGeometry(100, 110, 100, 20)
        self.OrderPrice.setEnabled(False)  # 기본적으로 비활성화

        self.order_type_label = QLabel("주문유형:", self)
        self.order_type_label.move(20, 150)
        self.OrderType = QComboBox(self)
        self.OrderType.setGeometry(100, 150, 100, 20)
        self.OrderType.addItems(["시장가", "매수가"])
        self.OrderType.currentIndexChanged.connect(self.update_price_input)

        self.buy_button = QPushButton("매수", self)
        self.buy_button.setGeometry(100, 190, 100, 30)
        self.buy_button.clicked.connect(self.buy_stock)

        self.log_label = QLabel("Log:", self)
        self.log_label.move(220, 30)
        self.Log = QTextEdit(self)
        self.Log.setGeometry(220, 50, 250, 200)
        self.Log.setReadOnly(True)

        # 체결 이벤트 연결
        self.kiwoom.OnReceiveChejanData = self.receive_chejan_data

    def update_price_input(self):
        """주문 유형에 따라 가격 입력 활성화/비활성화"""
        if self.OrderType.currentText() == "매수가":
            self.OrderPrice.setEnabled(True)
        else:
            self.OrderPrice.setEnabled(False)
            self.OrderPrice.clear()

    def buy_stock(self):
        """키움 API를 이용하여 주식 매수 주문 실행"""
        account = self.kiwoom.GetLoginInfo("ACCNO").split(';')[0]  # 계좌번호 가져오기
        code = self.StockCode.text()
        qty = self.OrderAmount.text()
        price = self.OrderPrice.text() if self.OrderPrice.isEnabled() else "0"  # 시장가 주문일 경우 가격 0

        if not code or not qty:
            self.Log.append("종목코드와 수량을 입력하세요.")
            return

        # 종목명 가져오기
        stock_name = self.kiwoom.GetMasterCodeName(code)

        order_type = 1  # 1: 매수
        hoga = "00" if self.OrderPrice.isEnabled() else "03"  # 00: 지정가, 03: 시장가

        self.kiwoom.SendOrder(
            "매수주문", "0101", account, order_type, code, int(qty), int(price), hoga, ""
        )
        self.Log.append(f"{stock_name}({code}) {qty}주 매수 주문 실행 ({'지정가' if self.OrderPrice.isEnabled() else '시장가'})")

    def receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신 이벤트 처리"""
        if gubun == "0":  # 주문 체결
            stock_name = self.kiwoom.GetChejanData(302)  # 종목명
            price = self.kiwoom.GetChejanData(910)  # 체결가
            qty = self.kiwoom.GetChejanData(911)  # 체결 수량
            self.Log.append(f"{stock_name} {qty}주 체결 완료 (가격: {price})")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KiwoomAPI()
    window.show()
    sys.exit(app.exec_())
