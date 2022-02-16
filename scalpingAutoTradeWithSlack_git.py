import time
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

def get_avg_buy_price(ticker):
    """매수 평균가 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0
    
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

def scalping_trade(coinString, coin):
    """스캘핑 트레이드"""
    # KRW-coin 현재 매수 호가 (원화 금액)
    coinBidPrice[coinString] = pyupbit.get_orderbook(ticker="KRW-" + coin)["orderbook_units"][0]["bid_price"]
    # KRW-coin 현재 매도 호가 (원화 금액)
    coinAskPrice[coinString] = pyupbit.get_orderbook(ticker="KRW-" + coin)["orderbook_units"][0]["ask_price"]
    
    cooldown = False
    # 쿨타임 체크
    if type(coinCooldown[coinString]) != int:
        if coinCooldown[coinString] + datetime.timedelta(seconds=60) <= datetime.datetime.now():
            coinCooldown[coinString] = 0
            cooldown = True
        else:
            cooldown = False
    else:
        cooldown = True
    
    maxPrice = 0
    minPrice = 0
    priceGap = 0

    if 20000 >= coinAskPrice[coinString] > 10000:
        maxPrice = 20000
        minPrice = 10000
        priceGap = 20
    elif 9600 >= coinAskPrice[coinString] > 6300:
        maxPrice = 9600
        minPrice = 6300
        priceGap = 15
    elif 6000 >= coinAskPrice[coinString] > 3200:
        maxPrice = 6000
        minPrice = 3200
        priceGap = 10
    elif 3000 >= coinAskPrice[coinString] > 1000:
        maxPrice = 3000
        minPrice = 1000
        priceGap = 5
    elif 900 >= coinAskPrice[coinString] > 400:
        maxPrice = 900
        minPrice = 400
        priceGap = 2
    elif 360 >= coinAskPrice[coinString] > 100:
        maxPrice = 360
        minPrice = 100
        priceGap = 1

    if priceGap > 0:
        # 아직 주문한게 없고, 매도 호가가 minPrice 초과 & maxPrice 이하 일 때
        if coinOrderCount[coinString] == 0 and maxPrice >= coinAskPrice[coinString] > minPrice and cooldown:
            # 개수 내림 계산 (소수점이 너무 많으면 에러가 나는 듯)
            volume = math.floor((seed_1Base *0.9995) / coinAskPrice[coinString]) # 매수 수량
            price = coinAskPrice[coinString] * volume # 매수 가격
            
            # 현재 매도 호가로 매수 ====================================================================================================================
            upbit.buy_market_order("KRW-" + coin, price) # 수수료 금액을 제외한 금액 만큼 매수한다.
            coinOrderBidPrice[coinString][1] = coinAskPrice[coinString] # 주문 매수 가격
            coinOrderBidVolume[coinString][1] = volume # 주문 매수 수량
            coinOrderCount[coinString] = 1
        # 주문한게 있고, 매도 호가가 minPrice 초과 & maxPrice 이하 일 때
        if coinOrderCount[coinString] > 0 and maxPrice >= coinAskPrice[coinString] > minPrice and cooldown:
            # 주문 개수만큼 for문을 돌린다.
            count = coinOrderCount[coinString]
            for i in range(count): # 0 ~ count -1 까지
                searchCount = count - i # 확인할 숫자(큰 수부터 확인한다. 0 ~ count -1까지 뺀 숫자.)
                
                buyLimitOrderState = ""
                sellLimitOrderState = ""
                
                if searchCount in coinBuyLimitOrder[coinString]:
                    # 매수 정보 확인 ("uuid" 확인)
                    if "uuid" in coinBuyLimitOrder[coinString][searchCount]:
                        buyLimitOrderState = upbit.get_order(coinBuyLimitOrder[coinString][searchCount]["uuid"])["state"]
                    else:
                        buyLimitOrderState = "done" # 1번은 매도 호가로 바로 매수하기 때문에 정보가 없다. (바로 완료됨)
                else:
                    coinBuyLimitOrder[coinString][searchCount] = {}
                
                if searchCount in coinSellLimitOrder[coinString]:
                    # 매도 정보 확인
                    if "uuid" in coinSellLimitOrder[coinString][searchCount]:
                        # 매도 정보가 있으면 매도주문 정보를 가져온다.
                        sellLimitOrderState = upbit.get_order(coinSellLimitOrder[coinString][searchCount]["uuid"])["state"]
                    else:
                        sellLimitOrderState = "None" # 매도 정보가 없으면 "None" 처리
                else:
                    coinSellLimitOrder[coinString][searchCount] = {}
                    
                # 매수가 되었는지 먼저 확인한다.
                if buyLimitOrderState == "done":
                    # 매수가 완료 되었으면, 매도 정보가 있는지 확인한다.
                    if sellLimitOrderState == "None": # 매도 정보가 없으면
                        # 주문 매수 가격 + priceGap 가격으로 매도 주문한다.
                        coinSellLimitOrder[coinString][searchCount] = upbit.sell_limit_order("KRW-" + coin, coinOrderBidPrice[coinString][searchCount] + priceGap, coinOrderBidVolume[coinString][searchCount])
                        # 매도 주문 시, 바로 한단계 아래로 매수주문이 없으면, 매수 주문한다.
                        # 바로 한단계 아래에 매수 정보가 있는지, 최대 주문 수량 이내인지 확인한다.
                        if searchCount + 1 in coinBuyLimitOrder[coinString] and coinOrderCount[coinString] < OrderMaxCount:
                            # "uuid"가 있으면 매수한 내역이 있는 것이므로, 매수 주문을 하지 않는다. "uuid"가 없는지 확인한다.
                            if "uuid" not in coinBuyLimitOrder[coinString][searchCount + 1]:
                                # 개수 내림 계산 (소수점이 너무 많으면 에러가 나는 듯)
                                volume = math.floor((seed_1Base *0.9995) / (coinAskPrice[coinString] - priceGap)) # 매수 수량
                                
                                # 매수 주문한다. 매수 주문 내용을 저장한다.
                                coinBuyLimitOrder[coinString][searchCount + 1] = upbit.buy_limit_order("KRW-" + coin, coinOrderBidPrice[coinString][searchCount] - priceGap, volume)
                                coinOrderBidPrice[coinString][searchCount + 1] = coinOrderBidPrice[coinString][searchCount] - priceGap # 주문 매수 가격
                                coinOrderBidVolume[coinString][searchCount + 1] = volume # 주문 매수 수량
                                coinOrderCount[coinString] = coinOrderCount[coinString] + 1
                        else:
                            # 개수 내림 계산 (소수점이 너무 많으면 에러가 나는 듯)
                            volume = math.floor((seed_1Base *0.9995) / (coinAskPrice[coinString] - priceGap)) # 매수 수량
                            
                            # 매수 주문한다. 매수 주문 내용을 저장한다.
                            coinBuyLimitOrder[coinString][searchCount + 1] = upbit.buy_limit_order("KRW-" + coin, coinOrderBidPrice[coinString][searchCount] - priceGap, volume)
                            coinOrderBidPrice[coinString][searchCount + 1] = coinOrderBidPrice[coinString][searchCount] - priceGap # 주문 매수 가격
                            coinOrderBidVolume[coinString][searchCount + 1] = volume # 주문 매수 수량
                            coinOrderCount[coinString] = coinOrderCount[coinString] + 1
                    # 매도 정보가 있으면, 매도가 완료되었는지 확인한다.
                    elif sellLimitOrderState == "done":
                        # 제일 상위 가격이 팔렸을 때
                        if searchCount == 1:
                            # 매도 완료 시, 매도 정보를 초기화 한다.
                            coinSellLimitOrder[coinString][searchCount] = {}
                            # 매수 카운트 초기화
                            coinOrderCount[coinString] = 0
                            if count >= 2: # 구매건수가 2개 이상일 때
                                for j in range(2, count + 1): # 2 ~ count 까지
                                    # 매수 대기 중일 때
                                    if j in coinBuyLimitOrder[coinString]:
                                        if "uuid" in coinBuyLimitOrder[coinString][j]:
                                            # 매수 주문을 취소한다. (매도 주문은 있을 수가 없음 제일 상위 가격이 팔렸으니..)
                                            upbit.cancel_order(coinBuyLimitOrder[coinString][j]["uuid"])
                                            # 매수 주문 내용 초기화
                                            coinBuyLimitOrder[coinString][j] = {}
                        # 제일 상위 가격이 팔리지 않았을 때
                        else:
                            # 매도 완료 시, 매도 정보를 초기화 한다.
                            coinSellLimitOrder[coinString][searchCount] = {}
                            # 재매수 한다.
                            coinBuyLimitOrder[coinString][searchCount] = upbit.buy_limit_order("KRW-" + coin, coinOrderBidPrice[coinString][searchCount], coinOrderBidVolume[coinString][searchCount])
                    # 매도 주문 중이고, 첫 주문 건일 때, 매수 가격 -priceGap * 20 보다 현재 매수 호가가 더 낮거나 같은지 비교한다.
                    elif sellLimitOrderState == "wait" and searchCount == 1 and coinOrderBidPrice[coinString][1] - (priceGap * 20) >= coinBidPrice[coinString]:
                        #슬랙 메시지
                        post_message(myToken,"#coin", "손절 라인으로 들어옴 searchCount:" + str(searchCount))
                        post_message(myToken,"#coin", "KRW-" + coin + ", 손절 매도가 : " + str(coinBidPrice[coinString]) + ", 매수 평균가 :" + str(get_avg_buy_price(coin)))
                        # 손절 쿨타임 설정
                        coinCooldown[coinString] = datetime.datetime.now()
                        for j in range(count): #  0 ~ count -1 까지
                            OrderCount = count - j # 확인할 숫자(큰 수부터 확인한다. 0 ~ count -1까지 뺀 숫자.)
                            # 매도 주문을 취소한다.
                            upbit.cancel_order(coinSellLimitOrder[coinString][OrderCount]["uuid"])
                            # 현재 매수 호가로 매도 ==================================================
                            upbit.sell_market_order("KRW-" + coin, coinOrderBidVolume[coinString][OrderCount]) # 주문 수량만큼 판매한다.
                            # 매도 정보를 초기화 한다.
                            coinSellLimitOrder[coinString][OrderCount] = {}

# 로그인
upbit = pyupbit.Upbit(access, secret)
# 시작 메세지 슬랙 전송
post_message(myToken,"#coin", "스캘핑 트레이드 시작")

seed = 800000 # 5개를 돌리므로, X10 만큼 원화가 있어야함
seed_1Base = seed * 0.0625 # 시드를 16개로 나눈다.
OrderMaxCount = 16 #최대 주문 수량을 설정한다.

coin1 = "XRP" #리플
coin2 = "BORA" #보라
coin3 = "ONG" #온톨로지가스
coin4 = "PLA" #플레이댑
coin5 = "ADA" #에이다
coin6 = "DOGE" #도지코인
coin7 = "SAND" #샌드박스
coin8 = "MANA" # 디센트럴랜드
coin9 = "WEMIX" # 위믹스
coin10 = "QTUM" # 퀀텀

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
# 지정가 매도 주문
coinSellLimitOrder = {'coin1': {}, 'coin2': {},'coin3': {}, 'coin4': {}, 'coin5': {}, 'coin6': {}, 'coin7': {}, 'coin8': {}, 'coin9': {}, 'coin10': {}}
# 지정가 매수 주문
coinBuyLimitOrder = {'coin1': {}, 'coin2': {},'coin3': {}, 'coin4': {}, 'coin5': {}, 'coin6': {}, 'coin7': {}, 'coin8': {}, 'coin9': {}, 'coin10': {}}
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
        scalping_trade('coin7', coin7)
        scalping_trade('coin8', coin8)
        scalping_trade('coin9', coin9)
        scalping_trade('coin10', coin10)
        time.sleep(1)
    except Exception as e:
        post_message(myToken,"#coin", e)
        time.sleep(1)
