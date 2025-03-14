import configparser
import time
import os
from pywinauto import application
from pywinauto import timings

# 설정 파일 읽기
config = configparser.ConfigParser()
config.read("kiwoom.conf", encoding="utf-8")

# 로그인 정보 가져오기
kiwoom_id = config["LOGIN"]["id"]
kiwoom_pw = config["LOGIN"]["password"]
kiwoom_cert_pw = config["LOGIN"]["cert_password"]

hts_path = "C:/KiwoomFlash3/bin/nkministarter.exe"

# 번개 HTS 실행
if not os.path.exists(hts_path):
    raise FileNotFoundError(f"HTS 실행 파일을 찾을 수 없습니다: {hts_path}")

app = application.Application()
app.start(hts_path)

title = "번개3 Login"
dlg = timings.wait_until_passes(20, 0.5, lambda: app.window(title=title))

pass_ctrl = dlg.Edit2
pass_ctrl.SetFocus()
pass_ctrl.TypeKeys(kiwoom_pw)

cert_ctrl = dlg.Edit3
cert_ctrl.SetFocus()
cert_ctrl.TypeKeys(kiwoom_cert_pw)

btn_ctrl = dlg.Button0
btn_ctrl.Click()

time.sleep(30)
os.system("taskkill /im nkmini.exe")

print("HTS 실행 완료")
