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
    # KRW-coin 현재 매수 호가 (원화 금액)
    coinBidPrice[coinString] = pyupbit.get_orderbook(ticker="KRW-" + coin)["orderbook_units"][0]["bid_price"]
    # KRW-coin 현재 매도 호가 (원화 금액)
    coinAskPrice[coinString] = pyupbit.get_orderbook(ticker="KRW-" + coin)["orderbook_units"][0]["ask_price"]

    # 아직 주문한게 없고, 매도 호가가 1,000원 초과 & 3000원 이하 일 때
    if coinOrderCount[coinString] == 0 and 3000 >= coinAskPrice[coinString] > 1000:
        # 현재 매도 호가로 매수 ====================================================================================================================
        upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
        coinOrderBidPrice[coinString][1] = coinAskPrice[coinString] # 주문 매수 가격
        coinOrderBidVolume[coinString][1] = (seed_1Base *0.9995) / coinAskPrice[coinString] # 주문 매수 수량
        coinOrderCount[coinString] = 1
    # 주문한게 있을 때
    if coinOrderCount[coinString] > 0:
        # 주문 개수만큼 for문을 돌린다.
        count = coinOrderCount[coinString]
        for i in range(count): # 0 부터 시작
            searchCount = count - i # 확인할 숫자(큰 수부터 확인한다.)
            # 원하는 판매 가격과 매수 호가를 비교한다.
            if coinOrderBidPrice[coinString][searchCount] + 5 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, coinOrderBidVolume[coinString][searchCount]) # 주문 매수 수량만큼 판매한다.
                coinOrderCount[coinString] = coinOrderCount[coinString] - 1 # 판매했으므로, 주문 카운트를 하나 차감한다.
                coinCooldown[coinString] = 0
            # 현재 주문 수량이 최대 주문 수량보다 적고, 매수 가격 -5보다 현재 매도호가 가격이 더 낮거나 같은지 비교한다.
            elif coinOrderCount[coinString] < OrderMaxCount and coinOrderBidPrice[coinString][searchCount] -5 >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                coinOrderBidPrice[coinString][searchCount + 1] = coinAskPrice[coinString] # 주문 매수 가격
                coinOrderBidVolume[coinString][searchCount + 1] = (seed_1Base *0.9995) / coinAskPrice[coinString] # 주문 매수 수량
                coinOrderCount[coinString] = coinOrderCount[coinString] + 1
            # 매수 가격 -150보다 현재 매수 호가가 더 낮거나 같은지 비교한다.
            elif coinOrderBidPrice[coinString][searchCount] - 150 <= coinBidPrice[coinString]:
                # 손절 쿨타임 설정 60초 후에도 해당 가격이면, 손절한다.
                if type(coinCooldown[coinString]) != int:
                    if coinCooldown[coinString] + datetime.timedelta(seconds=60) <= datetime.datetime.now():
                        #슬랙 메시지
                        post_message(myToken,"#coin", "KRW-" + coin + ", 손절 매도가 : " + str(coinAskPrice[coinString]) + ", 매수 평균가 :" + str(get_balance(coin)))
                        coinCooldown[coinString] = 0
                        # 매도 호가가 1,000원 초과 일 때
                        if coinAskPrice[coinString] > 1000:
                            # 현재 매수 호가로 매도 ====================================================================================================================
                            upbit.sell_market_order("KRW-" + coin, coinOrderBidVolume[coinString][searchCount]) # 주문 매수 수량만큼 판매한다.
                            # 바로 현재 매도 호가로 매수 ================================================================================================================
                            upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                            coinOrderBidPrice[coinString][searchCount + 1] = coinAskPrice[coinString] # 주문 매수 가격
                            coinOrderBidVolume[coinString][searchCount + 1] = (seed_1Base *0.9995) / coinAskPrice[coinString] # 주문 매수 수량
                        # 매도 호가가 1,000원 이하이면, 전량 매도
                        else:
                            coinOrderCount[coinString] = 0
                            upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                else:
                    coinCooldown[coinString] = datetime.datetime.now()
                    #슬랙 메시지
                    post_message(myToken,"#coin", coin + "60초 후 손절합니다. 손절 매도가 : "  + str(coinAskPrice[coinString]))
    # 여기부터는 더 낮은 금액
    # 아직 주문한게 없고, 매도 호가가 100원 초과 & 300원 이하 일 때
    if coinOrderCount[coinString] == 0 and 300 >= coinAskPrice[coinString] > 100:
        # 현재 매도 호가로 매수 ====================================================================================================================
        upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
        coinOrderBidPrice[coinString][1] = coinAskPrice[coinString] # 주문 매수 가격
        coinOrderBidVolume[coinString][1] = (seed_1Base *0.9995) / coinAskPrice[coinString] # 주문 매수 수량
        coinOrderCount[coinString] = 1
    # 주문한게 있을 때
    if coinOrderCount[coinString] > 0:
        # 주문 개수만큼 for문을 돌린다.
        count = coinOrderCount[coinString]
        for i in range(count): # 0 부터 시작
            searchCount = count - i # 확인할 숫자(큰 수부터 확인한다.)
            # 원하는 판매 가격과 매수 호가를 비교한다.
            if coinOrderBidPrice[coinString][searchCount] + 1 <= coinBidPrice[coinString]:
                # 현재 매수 호가로 매도 ====================================================================================================================
                upbit.sell_market_order("KRW-" + coin, coinOrderBidVolume[coinString][searchCount]) # 주문 매수 수량만큼 판매한다.
                coinOrderCount[coinString] = coinOrderCount[coinString] - 1 # 판매했으므로, 주문 카운트를 하나 차감한다.
                coinCooldown[coinString] = 0
            # 현재 주문 수량이 최대 주문 수량보다 적고, 매수 가격 -1보다 현재 매도호가 가격이 더 낮거나 같은지 비교한다.
            elif coinOrderCount[coinString] < OrderMaxCount and coinOrderBidPrice[coinString][searchCount] -1 >= coinAskPrice[coinString]:
                # 현재 매도 호가로 매수 ====================================================================================================================
                upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                coinOrderBidPrice[coinString][searchCount + 1] = coinAskPrice[coinString] # 주문 매수 가격
                coinOrderBidVolume[coinString][searchCount + 1] = (seed_1Base *0.9995) / coinAskPrice[coinString] # 주문 매수 수량
                coinOrderCount[coinString] = coinOrderCount[coinString] + 1
            # 매수 가격 -30보다 현재 매수 호가가 더 낮거나 같은지 비교한다.
            elif coinOrderBidPrice[coinString][searchCount] - 30 <= coinBidPrice[coinString]:
                # 손절 쿨타임 설정 60초 후에도 해당 가격이면, 손절한다.
                if type(coinCooldown[coinString]) != int:
                    if coinCooldown[coinString] + datetime.timedelta(seconds=60) <= datetime.datetime.now():
                        #슬랙 메시지
                        post_message(myToken,"#coin", "KRW-" + coin + ", 손절 매도가 : " + str(coinAskPrice[coinString]) + ", 매수 평균가 :" + str(get_balance(coin)))
                        coinCooldown[coinString] = 0
                        # 매도 호가가 100원 초과 일 때
                        if coinAskPrice[coinString] > 100:
                            # 현재 매수 호가로 매도 ====================================================================================================================
                            upbit.sell_market_order("KRW-" + coin, coinOrderBidVolume[coinString][searchCount]) # 주문 매수 수량만큼 판매한다.
                            # 바로 현재 매도 호가로 매수 ================================================================================================================
                            upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
                            coinOrderBidPrice[coinString][searchCount + 1] = coinAskPrice[coinString] # 주문 매수 가격
                            coinOrderBidVolume[coinString][searchCount + 1] = (seed_1Base *0.9995) / coinAskPrice[coinString] # 주문 매수 수량
                        # 매도 호가가 100원 이하이면, 전량 매도
                        else:
                            coinOrderCount[coinString] = 0
                            upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다.
                else:
                    coinCooldown[coinString] = datetime.datetime.now()
                    #슬랙 메시지
                    post_message(myToken,"#coin", coin + "60초 후 손절합니다.")

# 로그인
upbit = pyupbit.Upbit(access, secret)
# 시작 메세지 슬랙 전송
post_message(myToken,"#coin", "스캘핑 트레이드 시작")

seed = 500000 # 5개를 돌리므로, X6 만큼 원화가 있어야함
seed_1Base = seed * 0.05 # 시드를 20개로 나눈다.
OrderMaxCount = 20 #최대 주문 수량을 설정한다.

coin1 = "BORA" #보라
coin2 = "ADA" #에이다
coin3 = "ONG" #온톨로지가스
coin4 = "PLA" #플레이댑
coin5 = "XRP" #리플
coin6 = "DOGE" #도지코인

# 매수 호가
coinBidPrice = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0, 'coin6': 0, 'coin7': 0, 'coin8': 0, 'coin9': 0, 'coin10': 0}
# 매도 호가
coinAskPrice = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0, 'coin6': 0, 'coin7': 0, 'coin8': 0, 'coin9': 0, 'coin10': 0}
# 주문 카운트
coinOrderCount = {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0, 'coin6': 0, 'coin7': 0, 'coin8': 0, 'coin9': 0, 'coin10': 0}
# 주문 매수 가격
coinOrderBidPrice = {'coin1': {}, 'coin2': {},'coin3': {}, 'coin4': {}, 'coin5': {}, 'coin6': {}, 'coin7': {}, 'coin8': {}, 'coin9': {}, 'coin10': {}}
# 주문 매수 수량
coinOrderBidVolume = {'coin1': {}, 'coin2': {},'coin3': {}, 'coin4': {}, 'coin5': {}, 'coin6': {}, 'coin7': {}, 'coin8': {}, 'coin9': {}, 'coin10': {}}
# 손절 쿨타임
coinCooldown =  {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0, 'coin6': 0, 'coin7': 0, 'coin8': 0, 'coin9': 0, 'coin10': 0}

while True:
    try:
        scalping_trade('coin1', coin1)
        scalping_trade('coin2', coin2)
        scalping_trade('coin3', coin3)
        scalping_trade('coin4', coin4)
        scalping_trade('coin5', coin5)
        scalping_trade('coin6', coin6)
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#coin", e)
        time.sleep(1)
