import sys
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from pykiwoom.kiwoom import Kiwoom


class StockTrader(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("guruma_one.ui", self)  # UI 파일 로드

        self.kiwoom = Kiwoom()  # Kiwoom API 객체 생성
        self.kiwoom.CommConnect(block=True)  # API 로그인 (블록킹 방식)

        # orderType 초기 설정
        self.set_order_type()

        # 서버 연결 상태 확인 후 로그 출력
        self.check_server_connection()

        # 계좌 정보 가져오기
        self.get_account_info()

        # 주문 버튼 이벤트 설정
        self.buyButton.clicked.connect(self.process_order)

        # 체결 이벤트 처리
        self.kiwoom.OnReceiveChejanData = self.receive_chejan_data

    def set_order_type(self):
        # orderType 초기 설정
        self.orderType.addItems(["시장가", "지정가"])
        self.orderType.setCurrentText("시장가")

    def check_server_connection(self):
        """키움증권 서버 연결 상태 확인 후 로그 출력"""
        server = self.kiwoom.GetLoginInfo("GetServerGubun")
        if server == "1":
            self.logTextEdit.append("모의 투자 서버 연결 성공")
        else:
            self.logTextEdit.append("실 서버 연결 성공")

    def get_account_info(self):
        """로그인한 계좌 정보를 가져와 ComboBox에 추가"""
        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        self.accountComboBox.addItems(accounts)

    def process_order(self):
        """orderType 선택에 따라 매수 주문을 실행"""
        order_type = self.orderType.currentText()
        stock_code = self.stockCode.text()
        buy_price = self.buyPrice.text()
        buy_amount = self.buyAmount.text()
        sell_price = self.sellPrice.text()
        sell_amount = self.sellAmount.text()
        account = self.accountComboBox.currentText()

        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목 코드를 입력하세요.")
            self.logTextEdit.append("종목 코드를 입력하세요.")
            return

        if not order_type:
            QMessageBox.warning(self, "입력 오류", "주문 종류를 선택하세요.")
            self.logTextEdit.append("주문 종류를 선택하세요.")
            return

        if order_type == "지정가" and not buy_price:
            QMessageBox.warning(self, "입력 오류", "매수 금액을 입력하세요.")
            self.logTextEdit.append("매수 금액을 입력하세요.")
            return

        if not buy_amount:
            QMessageBox.warning(self, "입력 오류", "매수 수량을 입력하세요.")
            self.logTextEdit.append("매수 수량을 입력하세요.")
            return

        if order_type == "시장가":
            order_type_code = 1  # 시장가 매수 주문 코드
            price = 0  # 시장가는 가격 입력 없이 0으로 설정
            msg = f"{stock_code} 시장가로 {buy_amount}주 매수 주문 실행"
        elif order_type == "지정가":
            if not buy_price:
                self.logTextEdit.append("매수 가격을 입력하세요.")
                return
            order_type_code = 0  # 지정가 매수 주문 코드
            price = int(buy_price)
            msg = f"{stock_code} {buy_price}원으로 {buy_amount}주 매수 주문 실행"
        else:
            return

        self.kiwoom.SendOrder("매수주문", "0101", account, order_type_code, stock_code, int(buy_amount), price, "00", "")
        self.logTextEdit.append(msg)

    def receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 이벤트가 발생했을 때 실행되는 함수"""
        if gubun == "0":  # 매수 체결
            stock_code = self.kiwoom.GetChejanData(9001).strip()
            stock_name = self.kiwoom.GetMasterCodeName(stock_code)
            price = self.kiwoom.GetChejanData(910).strip()
            amount = self.kiwoom.GetChejanData(900).strip()
            self.logTextEdit.append(f"{stock_name} {price}원으로 {amount}주 매수 체결 완료")

            # 매수 체결 후 매도 주문 실행
            sell_price = self.sellPrice.text()
            sell_amount = self.sellAmount.text()
            account = self.accountComboBox.currentText()
            self.sell_order(stock_code, sell_price, sell_amount, account)
        elif gubun == "1":  # 매도 체결
            stock_code = self.kiwoom.GetChejanData(9001).strip()
            stock_name = self.kiwoom.GetMasterCodeName(stock_code)
            price = self.kiwoom.GetChejanData(910).strip()
            amount = self.kiwoom.GetChejanData(900).strip()
            self.logTextEdit.append(f"{stock_name} {price}원으로 {amount}주 매도 체결 완료")

    def sell_order(self, stock_code, sell_price, sell_amount, account):
        """매수 체결 후 매도 주문 실행"""
        if not sell_price or not sell_amount:
            self.logTextEdit.append("매도가격과 매도 수량을 입력하세요.")
            return

        order_type_code = 1  # 시장가 매도
        msg = f"{stock_code} {sell_price}원으로 {sell_amount}주 매도 주문 실행"

        self.kiwoom.SendOrder("매도주문", "0101", account, order_type_code, stock_code, int(sell_amount), int(sell_price),
                              "00", "")
        self.logTextEdit.append(msg)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = StockTrader()
    window.show()
    sys.exit(app.exec_())
