import time
import pyupbit
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

def scalping_trade(coinString, coin):
    """스캘핑 트레이드"""
    coinBidPrice[coinString] = pyupbit.get_orderbook(ticker="KRW-" + coin)["orderbook_units"][0]["bid_price"]     # KRW-coin1 현재 매수 호과 (원화 금액)
    if coinOrderCount[coinString] == 0 and 4500 > coinBidPrice[coinString] > 1000: # 아직 주문한게 없고, 매수 호과가 1,000원 초과 & 4500 미만 일 때
        # 지정가 매수
        # 원화 시장에 coin1을 현재 매수 호과에 seed_1Base 만큼 주문
        coinOrderDic[coinString + 'Order_1'] = upbit.buy_limit_order("KRW-" + coin, coinBidPrice[coinString], seed_1Base / coinBidPrice[coinString])
        coinOrderCount[coinString] = 1
        coinScaleTradingCount[coinString] = 0
        # 손절라인 계산
        coinCheckPrice[coinString] = coinBidPrice[coinString] - 30
    if coinOrderCount[coinString] == 1: # 주문 한것이 1개 있을 때
        #슬랙 메시지
        post_message(myToken,"#coin", "주문 한것이 1개 있을 때 체크 중")
        post_message(myToken,"#coin", upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['side'] == "bid" and upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['state'] == "wait")
        # 'side' 확인 = (bid : 매수, ask : 매도)
        # 'state' 확인 = (cancel : 취소, wait : 대기, done : 거래 완료)
        if upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['side'] == "bid" and upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['state'] == "wait":
            #슬랙 메시지
            post_message("매수 대기중")
            # 매수 대기 중인 가격 보다 현재 호가가 높으면, 매수 대기 중인 것을 취소하고 새로 매수 대기한다.
            if coinBidPrice[coinString] > upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['price']:
                #슬랙 메시지
                post_message("매수 대기 중인 가격 보다 현재 호가가 높으면, 매수 대기 중인 것을 취소하고 새로 매수 대기한다.")
                upbit.cancel_order(coinOrderDic[coinString + 'Order_1']['uuid'])
                # 지정가 매수
                # 원화 시장에 coin1을 현재 매수 호과에 seed_1Base 만큼 주문
                coinOrderDic[coinString + 'Order_1'] = upbit.buy_limit_order("KRW-" + coin, coinBidPrice[coinString], seed_1Base / coinBidPrice[coinString])
                coinOrderCount[coinString] = 1
                # 손절라인 계산
                coinCheckPrice[coinString] = coinBidPrice[coinString] - 30
        # 매수가 완료 되었는지 체크
        if upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['side'] == "bid" and upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['state'] == "done":
            #슬랙 메시지
            post_message(myToken,"#coin", "매수가 완료되었으면, 매수가 보다 5원 높게 판매")
            post_message(myToken,"#coin", upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['price'] + 5)
            post_message(myToken,"#coin", type(upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['price'] + 5))
            post_message(myToken,"#coin", upbit.get_balance("KRW-" + coin))
            post_message(myToken,"#coin", type(upbit.get_balance("KRW-" + coin)))
            # 매수가 완료되었으면, 매수가 보다 5원 높게 판매 (보유 수량만큼 판매)
            result = upbit.sell_limit_order("KRW-" + coin, upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['price'] + 5, upbit.get_balance("KRW-" + coin))
            coinOrderDic[coinString + 'Order_1'] = result
            #슬랙 메시지
            post_message(myToken,"#coin", "여기까지는 온다.")
        # 매도 상태 체크
        if upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['side'] == "ask":
            #매도가 완료되었는지 체크
            if upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['state'] == "done":
                # 매도가 완료되었으면 초기화
                coinOrderCount[coinString] = 0
            else:
                # 현재 매수 호과가 지금 매도 중인 가격보다 -15 보다 적을 때
                if coinBidPrice[coinString] < upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['price'] - 15:
                    # 매수 호과가 -10보다 작거나 같고, 물타기를 하지 않았을 때
                    if coinCheckPrice[coinString] + 20 >= coinBidPrice[coinString] and coinScaleTradingCount[coinString] == 0:
                        coinScaleTradingCount[coinString] = 1
                        # 원화 시장에 coin1을 현재 매수 호과에 seed_1Base 만큼 주문
                        coinOrderDic[coinString + 'Order_2'] = upbit.buy_limit_order("KRW-" + coin, coinBidPrice[coinString], seed_1Base / coinBidPrice[coinString])
                        coinOrderCount[coinString] = 2
                    # 매수 호과가 -20보다 작거나 같고, 물타기를 1회 했을 때
                    if coinCheckPrice[coinString] + 10 >= coinBidPrice[coinString] and coinScaleTradingCount[coinString] == 1:
                        coinScaleTradingCount[coinString] = 2
                        # 원화 시장에 coin1을 현재 매수 호과에 seed_1Base * 2 만큼 주문
                        coinOrderDic[coinString + 'Order_2'] = upbit.buy_limit_order("KRW-" + coin, coinBidPrice[coinString], seed_1Base * 2 / coinBidPrice[coinString])
                        coinOrderCount[coinString] = 2
                    # 매수 호과가 -30보다 작거나 같고, 물타기를 2회 했을 때
                    if coinCheckPrice[coinString] >= coinBidPrice[coinString] and coinScaleTradingCount[coinString] == 2:
                        coinScaleTradingCount[coinString] = 3
                        # 손절한다.
                        # 기존 주문을 취소하고
                        upbit.cancel_order(coinOrderDic[coinString + 'Order_1']['uuid'])
                        # 현재 보유 개수만큼 매도 한다. (현재 매수 호과로 전량 매도)
                        result = upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin))
                        coinOrderDic[coinString + 'Order_1'] = result

    if coinOrderCount[coinString] == 2: # 주문 한것이 2개 있을 때
        # 'coin1Order_1'이 매도되었는지 체크
        if upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['side'] == "ask" and upbit.get_order(coinOrderDic[coinString + 'Order_1']['uuid'])['state'] == "done":
            # 'coin1Order_1'이 매도되었는데, 'coin1Order_2'가 매수 주문 중이면, 해당 주문을 취소한다.
            if upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['side'] == "bid" and upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['state'] == "wait":
                upbit.cancel_order(coinOrderDic[coinString + 'Order_2']['uuid'])
                # 매도가 모두 완료되었으므로 초기화
                coinOrderCount[coinString] = 0
            # 'coin1Order_1'이 매도되었는데, 'coin1Order_2'가 매수 완료 되었으면 'coin1Order_2' 매도 처리하면서 'coin1Order_1'에 값을 넣어준다.
            if upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['side'] == "bid" and upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['state'] == "done":
                # 원래 판매하려는 매도 호과보다 현재 매수 호과가 높은지 체크
                if upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['price'] + 5  <= coinBidPrice[coinString]:
                    result = upbit.sell_market_order("KRW-" + coin, upbit.get_balance("KRW-" + coin)) # 현재 보유 개수만큼 매도 한다. (현재 매수 호과로 매도)
                    coinOrderDic[coinString + 'Order_1'] = result
                    coinOrderCount[coinString] = 1
                else:
                    # 매수가 보다 5원 높게 판매 (보유 수량만큼 판매)
                    result = upbit.sell_limit_order("KRW-" + coin, upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['price'] + 5, upbit.get_balance("KRW-" + coin))
                    coinOrderDic[coinString + 'Order_1'] = result
                    coinOrderCount[coinString] = 1
        # 'coin1Order_1'이 매도가 안되었으면
        else:
            #'coin1Order_2'가 매수가 완료 되었는지 체크
            if upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['side'] == "bid" and upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['state'] == "done":
                # 매수가 완료되었으면, 'coin1Order_1'의 매도를 취소
                upbit.cancel_order(coinOrderDic[coinString + 'Order_1']['uuid'])
                # 'coin1Order_2' 매수가 보다 5원 높게 판매 (보유 수량만큼 판매)
                result = upbit.sell_limit_order("KRW-" + coin, upbit.get_order(coinOrderDic[coinString + 'Order_2']['uuid'])['price'] + 5, upbit.get_balance("KRW-" + coin))
                coinOrderDic[coinString + 'Order_1'] = result
                coinOrderCount[coinString] = 1

# 로그인
upbit = pyupbit.Upbit(access, secret)
# 시작 메세지 슬랙 전송
post_message(myToken,"#coin", "스캘핑 트레이드 시작")

seed = 800000 # 3개를 돌리므로, X3 만큼 원화가 있어야함
seed_1Base = seed * 0.25 # 시드를 4개로 나눈다.

coin1 = "BORA" #보라
coin2 = "PUNDIX" #펀디엑스
coin3 = "MANA" #디센트럴랜드

# coinList = {'coin1': coin1, 'coin2': coin2, 'coin3': coin3}

coinOrderCount = {'coin1': 0, 'coin2': 0, 'coin3': 0}
coinBidPrice = {'coin1': 0, 'coin2': 0, 'coin3': 0}
coinCheckPrice = {'coin1': 0, 'coin2': 0, 'coin3': 0}
coinScaleTradingCount = {'coin1': 0, 'coin2': 0, 'coin3': 0}

coin1Order_1 = {} # 딕셔너리 선언
coin1Order_2 = {}
coin2Order_1 = {} # 딕셔너리 선언
coin2Order_2 = {}
coin3Order_1 = {} # 딕셔너리 선언
coin3Order_2 = {}

coinOrderDic = {'coin1Order_1': coin1Order_1, 'coin1Order_2': coin1Order_2,
                'coin2Order_1': coin2Order_1, 'coin2Order_2': coin2Order_2,
                'coin3Order_1': coin3Order_1, 'coin3Order_2': coin3Order_2}

while True:
    try:
        scalping_trade('coin1', coin1)
        #scalping_trade('coin2', coin2)
        #scalping_trade('coin3', coin3)
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#coin", e)
        time.sleep(1)
