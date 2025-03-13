from pykiwoom.kiwoom import Kiwoom
import time


def test_kiwoom_connection():
    kiwoom = Kiwoom()
    kiwoom.CommConnect(block=True)  # 로그인 요청

    state = kiwoom.GetConnectState()  # 연결 상태 확인
    if state == 1:
        print("Success")
    else:
        print("Failed")


if __name__ == "__main__":
    test_kiwoom_connection()
