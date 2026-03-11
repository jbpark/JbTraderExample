import pyupbit
import time
import pandas as pd

# 업비트 API 키 입력
access_key = "YOUR_ACCESS_KEY"
secret_key = "YOUR_SECRET_KEY"
upbit = pyupbit.Upbit(access_key, secret_key)

# 엑셀에서 매매 전략 불러오기
df = pd.read_excel("coin_trading.xlsx")

def get_current_price(ticker):
    try:
        return pyupbit.get_current_price(ticker)
    except Exception as e:
        print(f"가격 조회 실패: {e}")
        return None

for index, row in df.iterrows():
    coin_name = row['코인명']
    buy_price = row['매수가']
    sell_price = row['매도가']

    ticker = f"KRW-{coin_name}"
    current_price = get_current_price(ticker)

    if current_price is None:
        continue

    print(f"[{coin_name}] 현재가: {current_price}, 목표 매수가: {buy_price}, 목표 매도가: {sell_price}")

    # 매수 조건
    if current_price <= buy_price:
        print(f"📥 {coin_name} 매수 시도 중...")
        try:
            krw_balance = upbit.get_balance("KRW")
            if krw_balance >= 5000:
                order = upbit.buy_market_order(ticker, 5000)  # 5000원 매수
                print(f"✅ 매수 완료: {order}")
            else:
                print("❌ 잔고 부족")
        except Exception as e:
            print(f"매수 실패: {e}")

    # 매도 조건
    elif current_price >= sell_price:
        print(f"📤 {coin_name} 매도 시도 중...")
        try:
            coin_balance = upbit.get_balance(ticker)
            if coin_balance and coin_balance > 0:
                order = upbit.sell_market_order(ticker, coin_balance)
                print(f"✅ 매도 완료: {order}")
            else:
                print("❌ 보유 수량 없음")
        except Exception as e:
            print(f"매도 실패: {e}")

    time.sleep(1)  # 너무 자주 호출하면 제한 걸림
