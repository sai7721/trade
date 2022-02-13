import time
import pyupbit
import datetime
import requests

access = "SijZbF3zKypf6A9SBbEgg8XxuUgR8YxmxG0P0OtP"
secret = "K6OKreFQ1GPGmzAx6p1VGdU4Ac2keR1eIlM9DPtd"
myToken = "-"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_balance(ticker):
    """매수 평균가 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0

def scalping_trade(coinString, coin):
    """스캘핑 트레이드"""
    coinBidPrice[coinString] = pyupbit.get_orderbook(ticker="KRW-" + coin)["orderbook_units"][0]["bid_price"]     # KRW-coin1 현재 매수 호가 (원화 금액)
    coinAskPrice[coinString] = pyupbit.get_orderbook(ticker="KRW-" + coin)["orderbook_units"][0]["ask_price"]     # KRW-coin1 현재 매도 호가 (원화 금액)
    """손절 타이밍 이후 쿨다운 체크"""
    cooldownState = False
    if type(coinCooldown[coinString]) != int:
        if coinCooldown[coinString] + datetime.timedelta(seconds=60) <= datetime.datetime.now():
            coinCooldown[coinString] = 0
            cooldownState = True
    else:
        cooldownState = True

    # 아직 주문한게 없고, 매도 호가가 1,000원 초과 & 3000원 이하 일 때
    if coinOrderCount[coinString] == 0 and 3000 >= coinAskPrice[coinString] > 1000 and cooldownState:
        # 목표 매수 가격이 있을 경우
        if coinTargetBidPrice[coinString] > 0:
            # 목표 매수 가격보다 현재 매도 호가가 낮거나 같으면 매수
            if coinTargetBidPrice[coinString] >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                # 평균 매수 가격 설정
                coinAveragePrice[coinString] = coinAskPrice[coinString]
                # 주문 카운트 설정
                coinOrderCount[coinString] = 1
                # 물타기 횟수
                coinScaleTradingCount[coinString] = 0
            # 목표 매수 가격 보다 현재 매도 호가가 10 이상 차이나면, 그냥 매수해버리자. (오르는 시장에 따라 붙기 위해)
            if coinTargetBidPrice[coinString] + 10 <= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                # 평균 매수 가격 설정
                coinAveragePrice[coinString] = coinAskPrice[coinString]
                # 주문 카운트 설정
                coinOrderCount[coinString] = 1
                # 물타기 횟수
                coinScaleTradingCount[coinString] = 0
        # 목표 매수 가격이 없을 경우
        else:
            # 현재 매도 호가로 매수 ====================================================================================================================
            upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
            # 평균 매수 가격 설정
            coinAveragePrice[coinString] = coinAskPrice[coinString]
            # 주문 카운트 설정
            coinOrderCount[coinString] = 1
            # 물타기 횟수
            coinScaleTradingCount[coinString] = 0

    # 주문한게(보유한 코인)이 있을 때
    if coinOrderCount[coinString] == 1 and cooldownState:
        # 물타기 횟수가 0일 때
        if coinScaleTradingCount[coinString] == 0:
            # 평균 매수 가격 +5 보다 현재 매수 호가가 높거나 같을 때
            if coinAveragePrice[coinString] + 5 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                # 목표 매수 가격 설정
                coinTargetBidPrice[coinString] = coinBidPrice[coinString] - 5 # 매수 호가 -5를 목표 매수 가격으로 설정한다.
                # 주문 카운트 설정
                coinOrderCount[coinString] = 0
            # 평균 매수 가격 -10 보다 현재 매도 호가가 낮거나 같을 때
            if coinAveragePrice[coinString] - 10 >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                # 평균 매수 가격 설정
                coinAveragePrice[coinString] = coinAveragePrice[coinString] - 5 # 물타기 시 평균 매수 가격이 -5가 된다.
                # 물타기 횟수
                coinScaleTradingCount[coinString] = 1
                #슬랙 메시지
                post_message(myToken,"#coin", "KRW-" + coin + ", 평균 매수 가격 :" + coinAveragePrice[coinString] + " +5 일때 판매(매도호가), 물타기 횟수 :" + coinScaleTradingCount[coinString] + ", 매수 평균가 :" + get_balance(coin))
        # 물타기 횟수가 1일 때
        if coinScaleTradingCount[coinString] == 1:
            # 평균 매수 가격 +5 보다 현재 매수 호가가 높거나 같을 때
            if coinAveragePrice[coinString] + 5 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                # 목표 매수 가격 설정
                coinTargetBidPrice[coinString] = coinBidPrice[coinString] - 5 # 매수 호가 -5를 목표 매수 가격으로 설정한다.
                # 주문 카운트 설정
                coinOrderCount[coinString] = 0
            # 평균 매수 가격 -15 보다 현재 매도 호가가 낮거나 같을 때
            if coinAveragePrice[coinString] - 15 >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base * 2 *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                # 평균 매수 가격 설정
                coinAveragePrice[coinString] = coinAveragePrice[coinString] - 5 # 물타기 시 평균 매수 가격이 -2.5가 된다.
                # 물타기 횟수
                coinScaleTradingCount[coinString] = 2
                #슬랙 메시지
                post_message(myToken,"#coin", "KRW-" + coin + ", 평균 매수 가격 :" + coinAveragePrice[coinString] + " +5 일때 판매(매도호가), 물타기 횟수 :" + coinScaleTradingCount[coinString] + ", 매수 평균가 :" + get_balance(coin))
        # 물타기 횟수가 2일 때
        if coinScaleTradingCount[coinString] == 2:
            # 평균 매수 가격 +5 보다 현재 매수 호가가 높거나 같을 때
            if coinAveragePrice[coinString] + 5 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                # 목표 매수 가격 설정
                coinTargetBidPrice[coinString] = coinBidPrice[coinString] - 5 # 매수 호가 -5를 목표 매수 가격으로 설정한다.
                # 주문 카운트 설정
                coinOrderCount[coinString] = 0
            # 평균 매수 가격 -15 보다 현재 매도 호가가 낮거나 같을 때
            if coinAveragePrice[coinString] - 15 >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base * 2 *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                # 평균 매수 가격 설정
                coinAveragePrice[coinString] = coinAveragePrice[coinString] - 5
                # 물타기 횟수
                coinScaleTradingCount[coinString] = 3
                #슬랙 메시지
                post_message(myToken,"#coin", "KRW-" + coin + ", 평균 매수 가격 :" + coinAveragePrice[coinString] + " +5 일때 판매(매도호가), 물타기 횟수 :" + coinScaleTradingCount[coinString] + ", 매수 평균가 :" + get_balance(coin))
        # 물타기 횟수가 3일 때
        if coinScaleTradingCount[coinString] == 3:
            # 평균 매수 가격 +5 보다 현재 매수 호가가 높거나 같을 때
            if coinAveragePrice[coinString] + 5 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                # 목표 매수 가격 설정
                coinTargetBidPrice[coinString] = coinBidPrice[coinString] - 5 # 매수 호가 -5를 목표 매수 가격으로 설정한다.
                # 주문 카운트 설정
                coinOrderCount[coinString] = 0
            # 평균 매수 가격 -15 보다 현재 매도 호가가 낮거나 같을 때
            if coinAveragePrice[coinString] - 15 >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base * 2 *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                # 평균 매수 가격 설정
                coinAveragePrice[coinString] = coinAveragePrice[coinString] - 5
                # 물타기 횟수
                coinScaleTradingCount[coinString] = 4
                #슬랙 메시지
                post_message(myToken,"#coin", "KRW-" + coin + ", 평균 매수 가격 :" + coinAveragePrice[coinString] + " +5 일때 판매(매도호가), 물타기 횟수 :" + coinScaleTradingCount[coinString] + ", 매수 평균가 :" + get_balance(coin))
        # 물타기 횟수가 4일 때
        if coinScaleTradingCount[coinString] == 4:
            # 평균 매수 가격 +5 보다 현재 매수 호가가 높거나 같을 때
            if coinAveragePrice[coinString] + 5 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                # 목표 매수 가격 설정
                coinTargetBidPrice[coinString] = coinBidPrice[coinString] - 5 # 매수 호가 -5를 목표 매수 가격으로 설정한다.
                # 주문 카운트 설정
                coinOrderCount[coinString] = 0
            # 평균 매수 가격 -15 보다 현재 매도 호가가 낮거나 같을 때
            if coinAveragePrice[coinString] - 15 >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base * 2 *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                # 평균 매수 가격 설정
                coinAveragePrice[coinString] = coinAveragePrice[coinString] - 5
                # 물타기 횟수
                coinScaleTradingCount[coinString] = 5
                #슬랙 메시지
                post_message(myToken,"#coin", "KRW-" + coin + ", 평균 매수 가격 :" + coinAveragePrice[coinString] + " +5 일때 판매(매도호가), 물타기 횟수 :" + coinScaleTradingCount[coinString] + ", 매수 평균가 :" + get_balance(coin))
        # 물타기 횟수가 5일 때
        if coinScaleTradingCount[coinString] == 5:
            # 평균 매수 가격 +5 보다 현재 매수 호가가 높거나 같을 때
            if coinAveragePrice[coinString] + 5 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                # 목표 매수 가격 설정
                coinTargetBidPrice[coinString] = coinBidPrice[coinString] - 5 # 매수 호가 -5를 목표 매수 가격으로 설정한다.
                # 주문 카운트 설정
                coinOrderCount[coinString] = 0
            # 평균 매수 가격 -15 보다 현재 매도 호가가 낮거나 같을 때 손절한다!!
            if coinAveragePrice[coinString] - 15 >= coinAskPrice[coinString]:
                #슬랙 메시지
                post_message(myToken,"#coin", "KRW-" + coin + ", 손절 매도가 : " + coinAskPrice[coinString] + ", 매수 평균가 :" + get_balance(coin))
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                # 목표 매수 가격 설정
                coinTargetBidPrice[coinString] = 0 # 손절시에는 목표 매수 가격을 설정하지 않는다.
                # 주문 카운트 설정
                coinOrderCount[coinString] = 0
                # 쿨 다운 시간 설정
                coinCooldown[coinString] = datetime.datetime.now()

# 로그인
upbit = pyupbit.Upbit(access, secret)
# 시작 메세지 슬랙 전송
post_message(myToken,"#coin", "스캘핑 트레이드 시작")

seed = 500000 # 5개를 돌리므로, X5 만큼 원화가 있어야함
seed_1Base = seed * 0.1 # 시드를 10개로 나눈다.

coin1 = "BORA" #보라
coin2 = "PUNDIX" #펀디엑스
coin3 = "MANA" #디센트럴랜드
coin4 = "PLA" #플레이댑
coin5 = "XRP" #리플

# 주문 카운트
coinOrderCount = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0}
# 목표 매수 가격
coinTargetBidPrice = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0}
# 매수 가격
coinBidPrice = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0}
# 매도 가격
coinAskPrice = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0}
# 평균 매수 가격
coinAveragePrice = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0}
# 물타기 횟수
coinScaleTradingCount = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0}
# 손절 후 쿨타임
coinCooldown =  {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0}

while True:
    try:
        scalping_trade('coin1', coin1)
        scalping_trade('coin2', coin2)
        scalping_trade('coin3', coin3)
        scalping_trade('coin4', coin4)
        scalping_trade('coin5', coin5)
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#coin", e)
        time.sleep(1)
