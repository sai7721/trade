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

# 취소 = "cancel", 대기 = "wait", 완료 = "done"

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
    
    # 아직 주문한게 없고, 매도 호가가 1,000원 초과 & 3000원 이하 일 때
    if coinOrderCount[coinString] == 0 and 3000 >= coinAskPrice[coinString] > 1000 and cooldown:
        #슬랙 메시지
        post_message(myToken,"#coin", "현재 매도 호가로 매수" + str(coinAskPrice[coinString]))
        # 현재 매도 호가로 매수 ====================================================================================================================
        upbit.buy_market_order("KRW-" + coin, seed_1Base *0.9995) # 수수료 금액을 제외한 금액 만큼 매수한다.
        coinOrderBidPrice[coinString][1] = coinAskPrice[coinString] # 주문 매수 가격
        coinOrderBidVolume[coinString][1] = (seed_1Base *0.9995) / coinAskPrice[coinString] # 주문 매수 수량
        coinOrderCount[coinString] = 1
    # 주문한게 있고, 매도 호가가 1,000원 초과 & 3000원 이하 일 때
    if coinOrderCount[coinString] > 0 and 3000 >= coinAskPrice[coinString] > 1000 and cooldown:
        # 주문 개수만큼 for문을 돌린다.
        count = coinOrderCount[coinString]
        for i in range(count): # 0 ~ count -1 까지
            searchCount = count - i # 확인할 숫자(큰 수부터 확인한다. 0 ~ count -1까지 뺀 숫자.)
            
            buyLimitOrderState = ""
            sellLimitOrderState = ""
            # 매수 정보 확인
            if "uuid" in coinBuyLimitOrder[coinString][searchCount]:
                buyLimitOrderState = upbit.get_order(coinBuyLimitOrder[coinString][searchCount]["uuid"])["state"]
            else:
                # 매수 정보가 없다는 건, 최초 1번 주문밖에 없음.
                buyLimitOrderState = "done" # 1번은 매도 호가로 바로 매수하기 때문에 정보가 없다. (바로 완료됨)
            
            # 매도 정보 확인
            if "uuid" in coinSellLimitOrder[coinString][searchCount]:
                # 매도 정보가 있으면 매도주문 정보를 가져온다.
                sellLimitOrderState = upbit.get_order(coinSellLimitOrder[coinString][searchCount]["uuid"])["state"]
            else:
                sellLimitOrderState = "None" # 매도 정보가 없으면 "None" 처리
                
            # 매수가 되었는지 먼저 확인한다.
            if buyLimitOrderState == "done":
                #슬랙 메시지
                post_message(myToken,"#coin", "매수 완료" + str(searchCount))
                # 매수가 완료 되었으면, 매도 정보가 있는지 확인한다.
                if sellLimitOrderState == "None": # 매도 정보가 없으면
                    #슬랙 메시지
                    post_message(myToken,"#coin", "매도 정보가 없어서 매도 설정" + str(searchCount))
                    # 주문 매수 가격 + 5 가격으로 매도 주문한다.
                    coinSellLimitOrder[coinString][searchCount] = upbit.sell_limit_order("KRW-" + coin, coinOrderBidPrice[coinString][searchCount] + 5, coinOrderBidVolume[coinString][searchCount])
                    # 매도 주문 시, 바로 한단계 아래로 매수주문이 없으면, 매수 주문한다.
                    # 바로 한단계 아래에 매수 정보가 있는지, 최대 주문 수량 이내인지 확인한다.
                    if "uuid" in coinBuyLimitOrder[coinString][searchCount + 1] and coinOrderCount[coinString] < OrderMaxCount:
                        #슬랙 메시지
                        post_message(myToken,"#coin", "한단계 아래에 매수 정보가 없어서 매수 설정" + str(searchCount))
                        # 매수 주문한다. 매수 주문 내용을 저장한다.
                        coinBuyLimitOrder[coinString][searchCount + 1] = upbit.buy_limit_order("KRW-" + coin, coinOrderBidPrice[coinString][searchCount] - 5, (seed_1Base *0.9995) / (coinOrderBidPrice[coinString][searchCount] - 5))
                        coinOrderBidPrice[coinString][searchCount + 1] = coinOrderBidPrice[coinString][searchCount] - 5 # 주문 매수 가격
                        coinOrderBidVolume[coinString][searchCount + 1] = (seed_1Base *0.9995) / (coinOrderBidPrice[coinString][searchCount] - 5) # 주문 매수 수량
                        coinOrderCount[coinString] = coinOrderCount[coinString] + 1
                # 매도 정보가 있으면, 매도가 완료되었는지 확인한다.
                elif sellLimitOrderState == "done":
                    # 제일 상위 가격이 팔렸을 때
                    if searchCount == 1:
                        #슬랙 메시지
                        post_message(myToken,"#coin", "제일 상위 가격이 팔림" + str(searchCount))
                        # 매도 완료 시, 매도 정보를 초기화 한다.
                        coinSellLimitOrder[coinString][searchCount] = 0
                        # 매수 카운트 초기화
                        coinOrderCount[coinString] = 0
                        for j in range(2, count + 1): # 2 ~ count 까지
                            # 매수 주문을 취소한다. (매도 주문은 있을 수가 없음 제일 상위 가격이 팔렸으니..)
                            upbit.cancel_order(coinBuyLimitOrder[coinString][j]["uuid"])
                    # 제일 상위 가격이 팔리지 않았을 때
                    else:
                        #슬랙 메시지
                        post_message(myToken,"#coin", "일반 위치의 가격이 팔림" + str(searchCount))
                        # 매도 완료 시, 매도 정보를 초기화 한다.
                        coinSellLimitOrder[coinString][searchCount] = 0
                        # 재매수 한다.
                        coinBuyLimitOrder[coinString][searchCount] = upbit.buy_limit_order("KRW-" + coin, coinOrderBidPrice[coinString][searchCount], (seed_1Base *0.9995) / coinOrderBidPrice[coinString][searchCount])
                # 매도 주문 중이고, 첫 주문 건일 때, 매수 가격 -150보다 현재 매수 호가가 더 낮거나 같은지 비교한다.
                elif sellLimitOrderState == "wait" and searchCount == 1 and coinOrderBidPrice[coinString][1] - 150 >= coinBidPrice[coinString]:
                    #슬랙 메시지
                    post_message(myToken,"#coin", "손절 라인으로 들어옴 searchCount:" + str(searchCount))
                    post_message(myToken,"#coin", "KRW-" + coin + ", 손절 매도가 : " + str(coinBidPrice[coinString]) + ", 매수 평균가 :" + str(get_balance(coin)))
                    # 손절 쿨타임 설정
                    coinCooldown[coinString] = datetime.datetime.now()
                    OrderVolume = 0
                    for j in range(count): #  0 ~ count -1 까지
                        OrderCount = count - i # 확인할 숫자(큰 수부터 확인한다. 0 ~ count -1까지 뺀 숫자.)
                        # 매도 주문을 취소한다.
                        upbit.cancel_order(coinSellLimitOrder[coinString][OrderCount]["uuid"])
                        # 매도 수량 합치기
                        OrderVolume = OrderVolume + coinOrderBidVolume[coinString][OrderCount]
                    # 현재 매수 호가로 매도 ====================================================================================================================
                    upbit.sell_market_order("KRW-" + coin, OrderVolume) # 주문 수량만큼 판매한다.

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
# 지정가 매도 주문
coinSellLimitOrder = {'coin1': {}, 'coin2': {},'coin3': {}, 'coin4': {}, 'coin5': {}, 'coin6': {}, 'coin7': {}, 'coin8': {}, 'coin9': {}, 'coin10': {}}
# 지정가 매수 주문
coinBuyLimitOrder = {'coin1': {}, 'coin2': {},'coin3': {}, 'coin4': {}, 'coin5': {}, 'coin6': {}, 'coin7': {}, 'coin8': {}, 'coin9': {}, 'coin10': {}}
# 손절 쿨타임
coinCooldown =  {'coin1': 0, 'coin2': 0, 'coin3': 0, 'coin4': 0, 'coin5': 0, 'coin6': 0, 'coin7': 0, 'coin8': 0, 'coin9': 0, 'coin10': 0}

while True:
    try:
        scalping_trade('coin1', coin1)
        # scalping_trade('coin2', coin2)
        # scalping_trade('coin3', coin3)
        # scalping_trade('coin4', coin4)
        # scalping_trade('coin5', coin5)
        # scalping_trade('coin6', coin6)
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#coin", e)
        time.sleep(1)
