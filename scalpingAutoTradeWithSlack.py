import time
from numpy import true_divide
import pyupbit
import datetime
import requests
import math

access = "SijZbF3zKypf6A9SBbEgg8XxuUgR8YxmxG0P0OtP"
secret = "K6OKreFQ1GPGmzAx6p1VGdU4Ac2keR1eIlM9DPtd"
myToken = "-"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
# 시작 메세지 슬랙 전송
post_message(myToken,"#coin", "autotrade start")

buyCooldown = True

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-SAND")
        end_time = start_time + datetime.timedelta(days=1)
        # 9:00 < 현재 < 8:59:50
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-SAND", 0.3)
            ma15 = get_ma15("KRW-SAND")
            current_price = get_current_price("KRW-SAND")
            if target_price < current_price and ma15 < current_price and buyCooldown:
                buy_result = upbit.buy_market_order("KRW-SAND", math.floor(get_balance("KRW")*0.9995)) # 수수료 금액을 제외한 금액 만큼 매수한다.
                post_message(myToken,"#coin", "SAND buy : " +str(buy_result))
                buyCooldown = False
        else:
            buyCooldown = True
            sell_result = upbit.sell_market_order("KRW-SAND") #2번째 인자값이 없으면 전량 매도 한다고한다..
            # sell_result = upbit.sell_market_order("KRW-SAND", get_balance("SAND"))
            # sell_result = upbit.sell_market_order("KRW-SAND", get_balance("SAND")*0.9995) # 팔때는 수수료를 감안하지 않아도 된다.
            post_message(myToken,"#coin", "SAND sell : " +str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#coin", e)
        time.sleep(1)
