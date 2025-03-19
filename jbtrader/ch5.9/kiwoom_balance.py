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
        self.deposit_label = QLabel("D+2추정예수금: ")
        self.total_eval_label = QLabel("추정예탁자산: ")
        self.estimated_asset_label = QLabel("누적투자손익: ")
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

        df = self.kiwoom.block_request("opw00018",
                                       계좌번호=account_num,
                                       비밀번호="",
                                       비밀번호입력매체구분="00",
                                       조회구분=2,
                                       output="계좌평가잔고개별합산",
                                       next=0)

        columns = ["종목명", "평가손익", "수익률", "보유수량", "매입가"]
        self.tableWidget.setColumnCount(len(columns))
        self.tableWidget.setHorizontalHeaderLabels(columns)

        self.tableWidget.setRowCount(len(df))

        rowNum = 0
        for index, row in df.iterrows():
            self.tableWidget.setItem(rowNum, 0, QTableWidgetItem(row['종목명']))
            self.tableWidget.setItem(rowNum, 1, QTableWidgetItem(str(int(row['평가손익']))))
            self.tableWidget.setItem(rowNum, 2, QTableWidgetItem(str(float(row['수익률(%)']))))
            self.tableWidget.setItem(rowNum, 3, QTableWidgetItem(str(int(row['보유수량']))))
            self.tableWidget.setItem(rowNum, 4, QTableWidgetItem(str(int(row['매입가']))))
            rowNum += 1

        df = self.kiwoom.block_request("opw00004",
                                       계좌번호=account_num,
                                       비밀번호="",
                                       상장폐지조회구분=0,
                                       비밀번호입력매체구분="00",
                                       output="계좌평가현황",
                                       next=0)

        self.deposit_label.setText(f"D+2추정예수금: {str(int(df['D+2추정예수금'][0]))}")
        self.total_eval_label.setText(f"추정예탁자산: {str(int(df['추정예탁자산'][0]))}")
        self.estimated_asset_label.setText(f"누적투자손익: {str(int(df['누적투자손익'][0]))}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = BalanceViewer()
    viewer.show()
    sys.exit(app.exec_())
