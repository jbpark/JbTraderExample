import configparser
import time
import os
from pywinauto import Application

# 설정 파일 읽기
config = configparser.ConfigParser()
config.read("kiwoom.conf", encoding="utf-8")

# 로그인 정보 가져오기
kiwoom_id = config["LOGIN"]["id"]
kiwoom_pw = config["LOGIN"]["password"]
kiwoom_cert_pw = config["LOGIN"]["cert_password"]
hts_path = config["HTS"]["path"]

# 번개 HTS 실행
if not os.path.exists(hts_path):
    raise FileNotFoundError(f"HTS 실행 파일을 찾을 수 없습니다: {hts_path}")

app = Application(backend="win32").start(hts_path)
time.sleep(10)  # 프로그램이 실행될 시간을 충분히 확보

# 현재 실행 중인 모든 창 목록 가져오기
windows = app.windows()

# "업데이트" 관련 창 찾기
update_window = None
for window in windows:
    if "업데이트" in window.window_text():
        update_window = window
        break

# 업데이트 창이 있으면 "확인" 또는 "예" 버튼 클릭
if update_window:
    try:
        update_window.set_focus()
        if update_window.child_window(title="확인", control_type="Button").exists():
            update_window.child_window(title="확인", control_type="Button").click()
        elif update_window.child_window(title="예", control_type="Button").exists():
            update_window.child_window(title="예", control_type="Button").click()
        print("업데이트 완료")
        time.sleep(5)
    except Exception as e:
        print(f"업데이트 처리 중 오류 발생: {e}")
else:
    print("업데이트 창을 찾을 수 없습니다.")

# 로그인 창 탐색
login_window = None
for window in app.windows():
    if "번개 HTS" in window.window_text():
        login_window = window
        break

# 로그인 정보 입력
if login_window:
    try:
        login_window.set_focus()
        login_window.child_window(control_type="Edit", found_index=1).set_text(kiwoom_id)
        login_window.child_window(control_type="Edit", found_index=2).set_text(kiwoom_pw)
        login_window.child_window(control_type="Edit", found_index=3).set_text(kiwoom_cert_pw)
        login_window.child_window(title="로그인", control_type="Button").click()
        print("로그인 완료")
    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
else:
    print("로그인 창을 찾을 수 없습니다.")

print("HTS 실행 완료")
