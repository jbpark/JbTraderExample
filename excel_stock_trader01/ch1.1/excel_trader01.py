import pandas as pd
from pykiwoom.kiwoom import Kiwoom
import time

EXCEL_PATH = "stocks.xlsx"
CHECK_INTERVAL = 30  # 몇 초마다 주가를 확인할지

def read_excel(path):
    return pd.read_excel(path)

def name_to_code(kiwoom, name):
    market_codes = kiwoom.GetCodeListByMarket('0') + kiwoom.GetCodeListByMarket('10')
    for code in market_codes:
        if kiwoom.GetMasterCodeName(code) == name:
            return code
    return None

def get_current_price(kiwoom, code):
    price = kiwoom.GetMasterLastPrice(code)
    if isinstance(price, str):
        return int(price.replace(",", ""))
    elif isinstance(price, int):
        return price
    else:
        return 0

def auto_trade_loop(kiwoom, account):
    bought = set()
    sold = set()

    while True:
        df = read_excel(EXCEL_PATH)
        for _, row in df.iterrows():
            name = row['종목명']
            buy_price = int(row['매수가'])
            sell_price = int(row['매도가'])
            code = name_to_code(kiwoom, name)

            if not code:
                print(f"[{name}] 종목 코드 못 찾음.")
                continue

            current_price = get_current_price(kiwoom, code)
            print(f"[{name}] 현재가: {current_price} | 매수: {buy_price} | 매도: {sell_price}")

            qty = 10  # 10주 매매 예시

            if current_price <= buy_price and name not in bought:
                print(f"[매수] {name} @ {current_price}")
                kiwoom.SendOrder("매수", "1001", account, 1, code, qty, 0, "03", "")
                bought.add(name)
                sold.discard(name)

            elif current_price >= sell_price and name not in sold:
                print(f"[매도] {name} @ {current_price}")
                kiwoom.SendOrder("매도", "1002", account, 2, code, qty, 0, "03", "")
                sold.add(name)
                bought.discard(name)

        print(f"🕐 {CHECK_INTERVAL}초 후 다시 확인...\n")
        time.sleep(CHECK_INTERVAL)

def main():
    kiwoom = Kiwoom()
    kiwoom.CommConnect(block=True)
    account = kiwoom.GetLoginInfo("ACCNO")[0]
    auto_trade_loop(kiwoom, account)

if __name__ == "__main__":
    main()
