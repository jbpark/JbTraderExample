import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel
from pykiwoom.kiwoom import Kiwoom


class BalanceViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect()

    def initUI(self):
        self.setWindowTitle("잔고 조회")
        self.setGeometry(100, 100, 600, 500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 예수금, 총평가, 추정자산 라벨 추가
        self.deposit_label = QLabel("예수금: ")
        self.total_eval_label = QLabel("총평가: ")
        self.estimated_asset_label = QLabel("추정자산: ")
        layout.addWidget(self.deposit_label)
        layout.addWidget(self.total_eval_label)
        layout.addWidget(self.estimated_asset_label)

        # 테이블 위젯 생성
        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)

        # 조회 버튼 생성
        self.btn_refresh = QPushButton("잔고 조회")
        self.btn_refresh.clicked.connect(self.load_balance)
        layout.addWidget(self.btn_refresh)

    def load_balance(self):
        account_list = self.kiwoom.GetLoginInfo("ACCNO")  # 계좌 목록 가져오기
        if isinstance(account_list, list) and account_list:  # 리스트이고 값이 있으면
            account_num = account_list[0]  # 첫 번째 계좌 선택
        else:
            print("계좌 정보를 가져오지 못했습니다.")
            return

        self.kiwoom.SetInputValue("계좌번호", account_num)
        self.kiwoom.SetInputValue("비밀번호", "")  # 필요 시 입력
        self.kiwoom.SetInputValue("비밀번호입력매체구분", "00")
        self.kiwoom.SetInputValue("조회구분", "1")

        self.kiwoom.CommRqData("opw00018_req", "opw00018", 0, "0101")

        if self.kiwoom.tr_data is None:
            print("tr_data가 None입니다. 데이터 요청이 실패했을 가능성이 있습니다.")
            return

        if "opw00018" not in self.kiwoom.tr_data or self.kiwoom.tr_data["opw00018"] is None:
            print("잔고 데이터를 가져오지 못했습니다.")
            return

        data = self.kiwoom.tr_data["opw00018"]

        # 예수금, 총평가, 추정자산 업데이트
        self.deposit_label.setText(f"예수금: {data.get('예수금', 'N/A')}")
        self.total_eval_label.setText(f"총평가: {data.get('총평가', 'N/A')}")
        self.estimated_asset_label.setText(f"추정자산: {data.get('추정자산', 'N/A')}")

        columns = ["종목명", "평가금액", "수익률", "보유수량", "매입가"]
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)

        stocks = data.get("stocks", [])
        self.tableWidget.setRowCount(len(stocks))

        for row, item in enumerate(stocks):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(item.get('종목명', 'N/A')))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(str(item.get('평가금액', 'N/A'))))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(str(item.get('수익률', 'N/A'))))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(str(item.get('보유수량', 'N/A'))))
            self.tableWidget.setItem(row, 4, QTableWidgetItem(str(item.get('매입가', 'N/A'))))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = BalanceViewer()
    viewer.show()
    sys.exit(app.exec_())
