import sys
import traceback
from enum import Enum
import time

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
from pykiwoom.kiwoom import Kiwoom
import configparser
from PyQt5.QtCore import QTimer


# 주문 유형 Enum (매수/매도)
class OrderType(Enum):
    BUY = 1  # 매수
    SELL = 2  # 매도
    CANCEL_BUY = 3  # 매수 취소
    CANCEL_SELL = 4  # 매도 취소
    MODIFY_BUY = 5  # 매수 정정
    MODIFY_SELL = 6  # 매도 정정


# 주문 호가 유형 Enum
class HogaType(Enum):
    LIMIT = "00"  # 지정가
    MARKET = "03"  # 시장가
    CONDITIONAL_LIMIT = "05"  # 조건부지정가
    BEST_LIMIT = "06"  # 최유리지정가
    BEST_PRIORITY_LIMIT = "07"  # 최우선지정가

    LIMIT_IOC = "10"  # 지정가 IOC
    MARKET_IOC = "13"  # 시장가 IOC
    BEST_IOC = "16"  # 최유리 IOC

    LIMIT_FOK = "20"  # 지정가 FOK
    MARKET_FOK = "23"  # 시장가 FOK
    BEST_FOK = "26"  # 최유리 FOK

    PRE_MARKET_CLOSE = "61"  # 장전 시간외 종가
    AFTER_HOURS_SINGLE = "62"  # 시간외 단일가
    POST_MARKET_CLOSE = "81"  # 장후 시간외 종가

def get_cell_value_or_error(df, row_idx, col_name):
    try:
        return df.at[row_idx, col_name]  # 특정 위치의 값 반환
    except KeyError:
        raise ValueError(f"Invalid index '{row_idx}' or column '{col_name}'")

class StockTrader(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("guruma_one.ui", self)  # UI 파일 로드

        # 서버구분 > 실서버: "0", 모의투자 서버: "1"
        self.serverGubun = None

        self.kiwoom = Kiwoom()  # Kiwoom API 객체 생성
        self.kiwoom.CommConnect(block=True)  # API 로그인 (블록킹 방식)

        # 기본 Text
        # 테스트 종목 코드 기본 설정
        # 종목 코드 : 삼성전자
        if hasattr(self, "stockCode"):
            self.stockCode.setText("005930")

        # 매수 수량 : 1
        if hasattr(self, "buyAmount"):
            self.buyAmount.setText("1")

        # orderType 초기 설정
        self.set_order_type()

        # 서버 연결 상태 확인 후 로그 출력
        self.check_server_connection()

        # 계좌 정보 가져오기
        self.get_account_info()

        # TR 수신 이벤트
        self.kiwoom.OnReceiveTrData = self.receive_tr_data

        # 체결 이벤트 처리
        self.kiwoom.OnReceiveChejanData = self.receive_chejan_data

        # 실시간 데이터 수신 이벤트
        self.kiwoom.OnReceiveRealData = self.receive_real_data

        # 수신 메시지 이벤트
        self.kiwoom.OnReceiveMsg = self.receive_msg

        # 조건식 목록 요청에 대한 응답 이벤트
        self.kiwoom.OnReceiveConditionVer = self.receive_condition_ver

        # (1회성, 실시간) 종목 조건검색 요청시 발생되는 이벤트
        self.kiwoom.OnReceiveTrCondition = self.receive_tr_condition

        # 실시간 종목 조건검색 요청시 발생되는 이벤트
        self.kiwoom.OnReceiveRealCondition = self.receive_real_condition
        self.kiwoom._set_signals_slots()

        # 주문 버튼 이벤트 설정
        self.buyButton.clicked.connect(self.process_order)

        # 주기적으로 가격 업데이트를 위한 타이머 설정
        self.price_update_timer = QTimer(self)
        self.price_update_timer.timeout.connect(self.update_stock_price)
        self.price_update_timer.start(5000)  # 5초마다 실행

        self.buyPrice.installEventFilter(self)
        self.sellPrice.installEventFilter(self)

    def addLog(self, *args):
        print(args)
        output = " ".join(map(str, args))
        self.logTextEdit.append(output)

    def load_balance(self):
        if self.kiwoom.GetConnectState() == 0:
            print("키움증권 로그인 실패!")
        else:
            print("키움증권 로그인 성공!")

        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        print("계좌 목록:", accounts)

        if isinstance(accounts, list):  # 리스트이면 첫 번째 계좌 선택
            account_num = accounts[0]
        else:  # 문자열이면 split() 사용
            account_num = accounts.strip().split(';')[0]

        print("사용할 계좌:", account_num)

        df = self.kiwoom.block_request("opw00004",
                                       계좌번호=account_num,
                                       비밀번호="",
                                       상장폐지조회구분=0,
                                       비밀번호입력매체구분="00",
                                       output="계좌평가현황",
                                       next=0)

        # 예수금, 추정예탁자산, 누적투자손익 업데이트
        item = QTableWidgetItem(str(int(df['D+2추정예수금'][0])))
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.accountBalance.setItem(1, 0, item)

        item = QTableWidgetItem(str(int(df['추정예탁자산'][0])))
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.accountBalance.setItem(1, 1, item)

        item = QTableWidgetItem(str(int(df['누적투자손익'][0])))
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.accountBalance.setItem(1, 2, item)

    def load_stocks(self):
        if self.kiwoom.GetConnectState() == 0:
            print("키움증권 로그인 실패!")
        else:
            print("키움증권 로그인 성공!")

        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        print("계좌 목록:", accounts)

        if isinstance(accounts, list):  # 리스트이면 첫 번째 계좌 선택
            account_num = accounts[0]
        else:  # 문자열이면 split() 사용
            account_num = accounts.strip().split(';')[0]

        print("사용할 계좌:", account_num)

        df = self.kiwoom.block_request("opw00018",
                                       계좌번호=account_num,
                                       비밀번호="",
                                       비밀번호입력매체구분="00",
                                       조회구분=2,
                                       output="계좌평가잔고개별합산",
                                       next=0)

        columns = ["종목명", "평가손익", "수익률(%)", "보유수량", "매입가"]
        self.accountStocks.setColumnCount(len(columns))
        self.accountStocks.setHorizontalHeaderLabels(columns)

        self.accountStocks.setRowCount(len(df))

        rowNum = 0
        for index, row in df.iterrows():
            self.accountStocks.setItem(rowNum, 0, QTableWidgetItem(row['종목명']))
            self.accountStocks.setItem(rowNum, 1, QTableWidgetItem(str(int(row['평가손익']))))
            self.accountStocks.setItem(rowNum, 2, QTableWidgetItem(str(float(row['수익률(%)']))))
            self.accountStocks.setItem(rowNum, 3, QTableWidgetItem(str(int(row['보유수량']))))
            self.accountStocks.setItem(rowNum, 4, QTableWidgetItem(str(int(row['매입가']))))
            rowNum += 1

    def set_order_type(self):
        # orderType 초기 설정
        self.orderType.addItems(["시장가", "지정가"])
        self.orderType.setCurrentText("시장가")

    def receive_real_condition(self, code, event, conditionName, conditionIndex):
        """
        실시간 종목 조건검색 요청시 발생되는 이벤트

        :param code: string - 종목코드
        :param event: string - 이벤트종류("I": 종목편입, "D": 종목이탈)
        :param conditionName: string - 조건식 이름
        :param conditionIndex: string - 조건식 인덱스(여기서만 인덱스가 string 타입으로 전달됨)
        """

        self.addLog("[receiveRealCondition]")

        self.addLog("종목코드: ", code)
        self.addLog("이벤트: ", "종목편입" if event == "I" else "종목이탈")

    def receive_tr_condition(self, screenNo, codes, conditionName, conditionIndex, inquiry):
        """
        (1회성, 실시간) 종목 조건검색 요청시 발생되는 이벤트

        :param screenNo: string
        :param codes: string - 종목코드 목록(각 종목은 세미콜론으로 구분됨)
        :param conditionName: string - 조건식 이름
        :param conditionIndex: int - 조건식 인덱스
        :param inquiry: int - 조회구분(0: 남은데이터 없음, 2: 남은데이터 있음)
        """

        self.addLog("[receiveTrCondition]")

    def receive_condition_ver(self, receive, msg):
        """
        getConditionLoad() 메서드의 조건식 목록 요청에 대한 응답 이벤트

        :param receive: int - 응답결과(1: 성공, 나머지 실패)
        :param msg: string - 메세지
        """

        try:
            if not receive:
                return

            self.condition = self.getConditionNameList()
            self.addLog("조건식 개수: ", len(self.condition))

            for key in self.condition.keys():
                self.addLog("조건식: ", key, ": ", self.condition[key])
                self.addLog("key type: ", type(key))

        except Exception as e:
            self.addLog(e)

        finally:
            self.conditionLoop.exit()

    def receive_msg(self, screenNo, requestName, trCode, msg):
        """
        수신 메시지 이벤트

        서버로 어떤 요청을 했을 때(로그인, 주문, 조회 등), 그 요청에 대한 처리내용을 전달해준다.

        :param screenNo: string - 화면번호(4자리, 사용자 정의, 서버에 조회나 주문을 요청할 때 이 요청을 구별하기 위한 키값)
        :param requestName: string - TR 요청명(사용자 정의)
        :param trCode: string
        :param msg: string - 서버로 부터의 메시지
        """

        if "RC4058" in msg:
            if self.serverGubun == "1":
                QMessageBox.warning(self, "장 종료 오류", "오늘 모의 투자 장 종료되었습니다.")
            else:
                QMessageBox.warning(self, "장 종료 오류", "오늘 실 서버 장 종료되었습니다.")

        self.addLog(f"receive_msg :: msg={msg}")

    def receive_real_data(self, code, realType, realData):
        """
        실시간 데이터 수신 이벤트

        실시간 데이터를 수신할 때 마다 호출되며,
        setRealReg() 메서드로 등록한 실시간 데이터도 이 이벤트 메서드에 전달됩니다.
        getCommRealData() 메서드를 이용해서 실시간 데이터를 얻을 수 있습니다.

        :param code: string - 종목코드
        :param realType: string - 실시간 타입(KOA의 실시간 목록 참조)
        :param realData: string - 실시간 데이터 전문
        """

        if realType == "주식체결":
            체결시간 = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, 20)  # HHMMSS
            현재가 = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, 10)  # ±현재가
            등락율 = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, 12)  # ±등락율
            체결량 = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, 15)  # 체결량

            print(f"[{code}] 체결시간: {체결시간}, 현재가: {현재가}, 등락율: {등락율}, 체결량: {체결량}")

        try:
            self.addLog("[receiveRealData]")
            self.addLog("({})".format(realType))

        except Exception as e:
            self.addLog('{}'.format(e))

    def receive_tr_data(self, screenNo, requestName, trCode, recordName, inquiry,
                        deprecated1, deprecated2, deprecated3, deprecated4):
        """
        TR 수신 이벤트

        조회요청 응답을 받거나 조회데이터를 수신했을 때 호출됩니다.
        requestName과 trCode는 commRqData()메소드의 매개변수와 매핑되는 값 입니다.
        조회데이터는 이 이벤트 메서드 내부에서 getCommData() 메서드를 이용해서 얻을 수 있습니다.

        :param screenNo: string - 화면번호(4자리)
        :param requestName: string - TR 요청명(commRqData() 메소드 호출시 사용된 requestName)
        :param trCode: string
        :param recordName: string
        :param inquiry: string - 조회('0': 남은 데이터 없음, '2': 남은 데이터 있음)
        """

        self.addLog(f"스크린 번호: {screenNo}")
        self.addLog(f"요청명: {requestName}")
        self.addLog(f"트랜잭션 코드: {trCode}")
        self.addLog(f"기록 이름: {recordName}")
        self.addLog(f"이전 여부: {inquiry}")

        # 주문 결과 처리 (KOA_NORMAL_BUY_KP_ORD)
        if trCode == "KOA_NORMAL_BUY_KP_ORD":
            # 체결 결과 받기
            체결가격 = self.kiwoom.GetCommData(trCode, recordName, 0, "체결가격")
            체결수량 = self.kiwoom.GetCommData(trCode, recordName, 0, "체결수량")
            주문상태 = self.kiwoom.GetCommData(trCode, recordName, 0, "주문상태")

            self.addLog(f"체결가격: {체결가격}")
            self.addLog(f"체결수량: {체결수량}")
            self.addLog(f"주문상태: {주문상태}")

            if 주문상태 == "완료":
                self.addLog("주문이 체결되었습니다.")
            elif 주문상태 == "취소":
                self.addLog("장 종료로 인해 주문이 취소되었습니다.")
            else:
                self.addLog("주문 처리에 실패했습니다.")

        self.addLog("receiveTrData 실행: ", screenNo, requestName, trCode, recordName, inquiry)

    def check_server_connection(self):
        """키움증권 서버 연결 상태 확인 후 로그 출력"""
        self.serverGubun = self.kiwoom.GetLoginInfo("GetServerGubun")
        if self.serverGubun == "1":
            self.addLog("모의 투자 서버 연결 성공")
        else:
            self.addLog("실 서버 연결 성공")

        # 계좌 잔고
        self.load_balance()

        # 보유 종목
        self.load_stocks()

    def get_account_info(self):
        """로그인한 계좌 정보를 가져와 ComboBox에 추가"""
        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        self.accountComboBox.addItems(accounts)

    def process_order(self):
        """orderType 선택에 따라 매수 주문을 실행"""
        order_type = self.orderType.currentText()
        stock_code = self.stockCode.text()
        buy_price = self.buyPrice.currentData()
        buy_amount = self.buyAmount.text()
        sell_price = self.sellPrice.currentData()
        sell_amount = self.sellAmount.text()
        account = self.accountComboBox.currentText()

        if not stock_code:
            QMessageBox.warning(self, "입력 오류", "종목 코드를 입력하세요.")
            self.addLog("종목 코드를 입력하세요.")
            return

        if not order_type:
            QMessageBox.warning(self, "입력 오류", "주문 종류를 선택하세요.")
            self.addLog("주문 종류를 선택하세요.")
            return

        if order_type == "지정가" and not buy_price:
            QMessageBox.warning(self, "입력 오류", "매수 금액을 입력하세요.")
            self.addLog("매수 금액을 입력하세요.")
            return

        if not buy_amount:
            QMessageBox.warning(self, "입력 오류", "매수 수량을 입력하세요.")
            self.addLog("매수 수량을 입력하세요.")
            return

        if order_type == "시장가":
            order_type_code = OrderType.BUY.value  # order type 매수
            hoga = HogaType.MARKET.value  # 시장가 주문
            price = 0  # 시장가는 가격 입력 없이 0으로 설정
            msg = f"{stock_code} 시장가로 {buy_amount}주 매수 주문 실행"
        elif order_type == "지정가":
            if not buy_price:
                self.addLog("매수 가격을 입력하세요.")
                return
            order_type_code = OrderType.BUY.value  # order type 매수
            hoga = HogaType.LIMIT.value  # 지정가 주문
            price = int(buy_price)
            msg = f"{stock_code} {buy_price}원으로 {buy_amount}주 매수 주문 실행"
        else:
            return

        self.addLog(msg)

        # kiwoom.SendOrder
        # 1번째 파라미터 = 사용자가 임의로 지정할 수 있는 요청 이름
        # 2번째 파라미터 = 화면 번호 ('0001' ~ '9999')
        # 3번째 파라미터 = 계좌 번호 10자리
        # 4번째 파라미터 = 주문 타입
        #                 1 - 신규 매수, 2 - 신규 매도, 3 - 매수 취소,
        #                 4 - 매도 취소, 5 - 매수 정정, 6 - 매도 정정
        # 5번째 파라미터 = 종목 코드
        # 6번째 파라미터 = 주문 수량
        # 7번째 파라미터 = 주문 단가
        # 8번째 파라미터 = 호가
        #                 00 - 지정가, 03 - 시장가,
        #                 05 - 조건부지정가, 06 - 최유리지정가, 07 - 최우선지정가,
        #                 10 - 지정가IOC, 13 - 시장가IOC, 16 - 최유리IOC
        #                 20 - 지정가FOK, 23 - 시장가FOK, 26 - 최유리FOK
        #                 61 - 장전시간외종가, 62 - 시간외단일가, 81 - 장후시간외종가
        # 9번째 파라미터 = 원문 주문 번호 (신규 주문 시 공백, 정정이나 취소 시 원문 주문 번호 입력)

        try:
            if order_type == "시장가":
                result = self.kiwoom.SendOrder("시장가매수", "0101", account, order_type_code, stock_code, int(buy_amount),
                                               price, hoga, "")
            else:
                result = self.kiwoom.SendOrder("지정가매수", "0101", account, order_type_code, stock_code, int(buy_amount),
                                               price, hoga, "")
            if result != 0:
                raise Exception(f"SendOrder 실패! 리턴값: {result}")

            self.addLog("✅ SendOrder 성공!")
        except Exception as e:
            self.addLog("❌ 예외 발생!")
            self.addLog(f"에러 메시지: {str(e)}")
            self.addLog("🔹 상세 오류 정보:")
            traceback.print_exc()  # 전체 스택 트레이스 출력

    def receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(f"receive_chejan_data :: gubun:{gubun}")

        """체결 이벤트가 발생했을 때 실행되는 함수"""
        if gubun == "0":  # 매수 체결
            stock_code = self.kiwoom.GetChejanData(9001).strip().lstrip('A')  # 종목 코드
            stock_name = self.kiwoom.GetChejanData(302).strip()  # 종목명
            order_no = self.kiwoom.GetChejanData(9203)  # 주문번호
            price = self.kiwoom.GetChejanData(910).strip() # 주문 가격
            amount = self.kiwoom.GetChejanData(900).strip() # 주문 수량
            executed_quantity = self.kiwoom.GetChejanData(911).strip()  # 체결 수량
            trade_type = self.kiwoom.GetChejanData(913).strip()  # 매매 구분 (1: 매수, 2: 매도)
            self.addLog(f"{stock_name} {price}원으로 {amount}주 매수 체결 완료")

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
            self.addLog(f"{stock_name} {price}원으로 {amount}주 매도 체결 완료")

    def sell_order(self, stock_code, sell_price, sell_amount, account):
        """매수 체결 후 매도 주문 실행"""
        if not sell_price or not sell_amount:
            self.addLog("매도가격과 매도 수량을 입력하세요.")
            return

        order_type_code = OrderType.SELL.value  # 2: 매도
        hoga = HogaType.LIMIT.value  # 지정가 주문
        msg = f"{stock_code} {sell_price}원으로 {sell_amount}주 매도 주문 실행"

        order_id = self.kiwoom.SendOrder("지정가매도", "0101", account, order_type_code, stock_code, int(sell_amount), int(sell_price),
                              hoga, "")

        # 주문 결과 확인
        if order_id == 0:
            self.addLog("지정가 매도 주문 성공!")
        else:
            self.addLog(f"주문 실패! 오류 코드: {order_id}")

        self.addLog(msg)

    def eventFilter(self, obj, event):
        if (obj == self.buyPrice or obj == self.sellPrice) and event.type() == event.MouseButtonPress:
            self.on_combobox_clicked()
        return super().eventFilter(obj, event)

    def on_combobox_clicked(self):
        print("QComboBox가 클릭되었습니다!")  # 특정 함수 실행
        self.stop_price_update()

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

    def update_stock_price(self):
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

        print("opt10001 :: 주식기본정보")
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

        for i in range(20, -21, -1):  # -20호가부터 +20호가까지 추가
            price = current_price + i * price_tick
            label = f"{i}호가: {price}" if i != 0 else f"현재가: {price}"
            self.buyPrice.addItem(label, price)
            self.sellPrice.addItem(label, price)

        # 기본값 설정: buyPrice는 현재가, sellPrice는 +1호가
        self.buyPrice.setCurrentIndex(20)
        self.sellPrice.setCurrentIndex(19)

        self.logTextEdit.append(f"현재가 {current_price}원부터 ±20호가까지 설정 완료")

    def stop_price_update(self):
        """
        사용자가 가격을 선택하면 타이머 정지
        """
        print("stop_price_update")
        self.price_update_timer.stop()
        self.logTextEdit.append("가격 선택 완료. 자동 업데이트 중지")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = StockTrader()
    window.show()
    sys.exit(app.exec_())
