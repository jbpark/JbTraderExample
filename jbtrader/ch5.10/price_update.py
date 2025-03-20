import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
from pykiwoom.kiwoom import Kiwoom


def get_cell_value_or_error(df, row_idx, col_name):
    try:
        return df.at[row_idx, col_name]  # 특정 위치의 값 반환
    except KeyError:
        raise ValueError(f"Invalid index '{row_idx}' or column '{col_name}'")


class GurumaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("guruma_one.ui", self)  # UI 파일 로드

        self.kiwoom = Kiwoom()  # Kiwoom 인스턴스 생성
        self.kiwoom.CommConnect()  # API 연결

        self.kiwoom.OnEventConnect = self.event_connect  # 연결 이벤트 핸들러

        # 버튼 클릭 이벤트 연결
        self.buyButton.clicked.connect(self.update_stock_price)

        # 주기적으로 가격 업데이트를 위한 타이머 설정
        self.price_update_timer = QTimer(self)
        self.price_update_timer.timeout.connect(self.update_stock_price)
        self.price_update_timer.start(5000)  # 5초마다 실행

        self.buyPrice.installEventFilter(self)
        self.sellPrice.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (obj == self.buyPrice or obj == self.sellPrice) and event.type() == event.MouseButtonPress:
            self.on_combobox_clicked()
        return super().eventFilter(obj, event)

    def on_combobox_clicked(self):
        print("QComboBox가 클릭되었습니다!")  # 특정 함수 실행
        self.stop_price_update()

    def event_connect(self, err_code):
        """
        키움증권 API 연결 이벤트 처리
        """
        if err_code == 0:
            server_type = self.kiwoom.GetLoginInfo("GetServerGubun")
            if server_type == "1":
                self.logTextEdit.append("모의 투자 서버 연결 성공")
            else:
                self.logTextEdit.append("실 서버 연결 성공")
            self.load_accounts()
        else:
            self.logTextEdit.append("API 연결 실패")

    def load_accounts(self):
        """
        계좌 정보를 가져와서 accountComboBox에 출력
        """
        accounts = self.kiwoom.GetLoginInfo("ACCNO").split(';')
        self.accountComboBox.addItems([acc for acc in accounts if acc])

    def update_stock_price(self):
        """
        stockCode 입력 시 현재 가격 및 상하 몇 호가 가격을 buyPrice, sellPrice에 반영
        """
        stock_code = self.stockCode.text().strip()
        if not stock_code:
            self.logTextEdit.append("종목 코드를 입력하세요.")
            return

        self.kiwoom.SetInputValue("종목코드", stock_code)
        self.kiwoom.CommRqData("주식기본정보", "opt10001", 0, "0101")
        QTimer.singleShot(5000, self.process_stock_price)

    def get_price_tick(self, price):
        """
        현재가를 기반으로 호가 단위를 계산하는 함수
        """
        if price < 1000:
            return 1
        elif price < 5000:
            return 5
        elif price < 10000:
            return 10
        elif price < 50000:
            return 50
        elif price < 100000:
            return 100
        elif price < 500000:
            return 500
        else:
            return 1000

    def process_stock_price(self):
        """
        조회한 주식 정보를 buyPrice와 sellPrice에 반영
        """
        """
                조회한 주식 정보를 buyPrice와 sellPrice에 반영
                """

        stock_code = self.stockCode.text().strip()
        if not stock_code:
            self.logTextEdit.append("종목 코드를 입력하세요.")
            return

        df = self.kiwoom.block_request("opt10001",
                                       종목코드=stock_code,
                                       output="주식기본정보",
                                       next=0)

        current_price_str = get_cell_value_or_error(df, 0, '현재가')
        if not current_price_str:
            self.logTextEdit.append("현재가 정보를 가져올 수 없습니다.")
            return

        current_price_str = str(int(current_price_str))

        try:
            current_price = abs(int(current_price_str))
        except ValueError:
            self.logTextEdit.append("현재가 변환 오류: {current_price_str}")
            return

        price_tick = self.get_price_tick(current_price)

        self.buyPrice.clear()
        self.sellPrice.clear()

        for i in range(-20, 21):  # -20호가부터 +20호가까지 추가
            price = current_price + i * price_tick
            label = f"{i}호가: {price}" if i != 0 else f"현재가: {price}"
            self.buyPrice.addItem(label, price)
            self.sellPrice.addItem(label, price)

        # 기본값 설정: buyPrice는 현재가, sellPrice는 +1호가
        self.buyPrice.setCurrentIndex(20)
        self.sellPrice.setCurrentIndex(21)

        self.logTextEdit.append(f"현재가 {current_price}원부터 ±20호가까지 설정 완료")

    def stop_price_update(self):
        """
        사용자가 가격을 선택하면 타이머 정지
        """
        print("stop_price_update")
        self.price_update_timer.stop()
        self.logTextEdit.append("가격 선택 완료. 자동 업데이트 중지")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GurumaApp()
    window.show()
    sys.exit(app.exec_())
