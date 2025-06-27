import sys
import time
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from pykiwoom.kiwoom import Kiwoom

EXCEL_PATH = "stocks.xlsx"
LOG_FILE = "trade_log.txt"
INTERVAL_MS = 30000  # 30초 주기

class TradingBot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("\U0001F4C8 Excel 기반 자동 매매 시스템")
        self.setGeometry(300, 100, 900, 700)

        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)
        self.account = self.kiwoom.GetLoginInfo("ACCNO")[0]
        self.account_pw = ""

        self.bought_set = set()
        self.sold_set = set()

        self.init_ui()
        self.get_password()
        self.update_holdings()
        self.log("시스템 트레이딩 시작됨 ✅")

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_trading)
        self.timer.start(INTERVAL_MS)

    def init_ui(self):
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)

        self.btn_manual = QPushButton("\U0001F501 수동 실행")
        self.btn_manual.clicked.connect(self.run_trading)

        self.status_label = QLabel("⏱️ 대기 중...")

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["종목명", "수량", "매입가", "현재가"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addWidget(self.text_log)
        layout.addWidget(self.status_label)
        layout.addWidget(self.btn_manual)
        layout.addWidget(QLabel("\n📦 현재 보유 종목"))
        layout.addWidget(self.table)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def get_password(self):
        pw, ok = QInputDialog.getText(self, "계좌 비밀번호 입력", "계좌 비밀번호를 입력하세요:", QLineEdit.Password)
        if ok and pw:
            self.account_pw = pw
            self.log("🔐 계좌 비밀번호가 등록되었습니다.")
        else:
            QMessageBox.critical(self, "오류", "비밀번호가 입력되지 않았습니다. 프로그램을 종료합니다.")
            sys.exit(1)

    def log(self, message):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{now}] {message}"
        self.text_log.append(log_msg)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")

    def read_excel(self):
        return pd.read_excel(EXCEL_PATH)

    def name_to_code(self, name):
        codes = self.kiwoom.GetCodeListByMarket('0') + self.kiwoom.GetCodeListByMarket('10')
        for code in codes:
            if self.kiwoom.GetMasterCodeName(code) == name:
                return code
        return None

    def get_current_price(self, code):
        price = self.kiwoom.GetMasterLastPrice(code)
        if isinstance(price, str):
            return int(price.replace(",", ""))
        elif isinstance(price, int):
            return price
        else:
            return 0

    def run_trading(self):
        self.status_label.setText("🔍 주가 확인 중...")
        df = self.read_excel()

        for _, row in df.iterrows():
            name = row['종목명']
            buy_price = int(row['매수가'])
            sell_price = int(row['매도가'])
            code = self.name_to_code(name)

            if not code:
                self.log(f"[오류] 종목명 {name} → 코드 변환 실패")
                continue

            current = self.get_current_price(code)
            self.log(f"{name} 현재가: {current} / 매수: {buy_price} / 매도: {sell_price}")

            qty = 10

            if current <= buy_price and name not in self.bought_set:
                self.log(f"📥 매수 주문: {name} @ {current}")
                self.kiwoom.SendOrder("매수", "1001", self.account, 1, code, qty, 0, "03", "")
                self.bought_set.add(name)
                self.sold_set.discard(name)

            elif current >= sell_price and name not in self.sold_set:
                self.log(f"📤 매도 주문: {name} @ {current}")
                self.kiwoom.SendOrder("매도", "1002", self.account, 2, code, qty, 0, "03", "")
                self.sold_set.add(name)
                self.bought_set.discard(name)

        self.update_holdings()
        self.status_label.setText("⏱️ 대기 중...")

    def update_holdings(self):
        try:
            data = self.kiwoom.block_request("opw00018",
                                             계좌번호=self.account,
                                             비밀번호=self.account_pw,
                                             비밀번호입력매체구분="00",
                                             조회구분=2,
                                             output="계좌평가잔고개별합산",
                                             next=0)

            self.log(f"[디버그] 계좌번호: {self.account}")
            self.log(f"[디버그] 비밀번호: {'입력됨' if self.account_pw else '미입력'}")
            self.log(f"[디버그] opw00018 응답 타입: {type(data)}")
            self.log(f"[디버그] opw00018 응답: {data}")

            if not isinstance(data, dict) or '종목번호' not in data:
                self.log("[경고] 보유 종목 정보가 없습니다.")
                self.table.setRowCount(0)
                return

            codes = data['종목번호']
            names = data['종목명']
            qtys = data['보유수량']
            prices = data['매입가']

            self.table.setRowCount(len(codes))
            for i in range(len(codes)):
                name = names[i].strip()
                qty = int(qtys[i]) if str(qtys[i]).strip().isdigit() else 0
                buy_price = int(prices[i]) if str(prices[i]).strip().isdigit() else 0
                cur_price = self.get_current_price(codes[i].strip())

                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(str(qty)))
                self.table.setItem(i, 2, QTableWidgetItem(str(buy_price)))
                self.table.setItem(i, 3, QTableWidgetItem(str(cur_price)))
        except Exception as e:
            self.log(f"[보유 종목 조회 오류] {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    bot = TradingBot()
    bot.show()
    sys.exit(app.exec_())
