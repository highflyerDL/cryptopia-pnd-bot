import json
from api import Api
from time import sleep
import sys

# Get these from (link here)
def get_secret(secret_file):
    """Grabs API key and secret from file and returns them"""

    with open(secret_file) as secrets:
        secrets_json = json.load(secrets)
        secrets.close()

    return str(secrets_json['key']), str(secrets_json['secret'])

KEY, SECRET=get_secret("secrets.json")
cryptopia = Api(KEY, SECRET)

def isOrderFilled(market):
    success, err = cryptopia.get_openorders(market)
    return len(success)==0

def setBuyOrder(market, amount, buy_safety_rate):
    success, err=cryptopia.get_market(market)
    ask_price = success['AskPrice']
    buy_price = ask_price*buy_safety_rate
    print('Trade for market {} has ask price {}'.format(market, ask_price))
    coin_amount = float(amount)/buy_price
    success, err=cryptopia.submit_trade(market, "Buy", buy_price, coin_amount)
    print('With safety rate {}, set buy order at {} to buy {} of {} with {} BTC'.format(buy_safety_rate, buy_price, coin_amount, market, amount))
    if err == None:
        return buy_price, coin_amount
    else:
        raise ValueError(err)

def setBuyOrderWithRetry(market, amount, buy_safety_rate):
    count = 0
    while count != 3:
        try:
            return setBuyOrder(market, amount, buy_safety_rate)
        except ValueError as e:
            print("Failed to set buy order with {}".format(e))
            count+=1
    raise SystemError("Failed to set buy orders {} times".format(count))

def setSellOrderWithRetry(market, price, amount):
    count = 0
    while count != 3:
        try:
            return setSellOrder(market, price, amount)
        except ValueError as e:
            print("Failed to set sell order with {}".format(e))
            count+=1
    raise SystemError("Failed to set sell orders {} times".format(count))


def setSellOrder(market, price, amount):
    success, err = cryptopia.submit_trade(market, "Sell", price, amount)
    print('Set sell order at {} of {} with {} amount of coin'.format(price, market, amount))
    if err == None:
        return True
    else:
        raise ValueError(err)

def cancelAllOrders():
    success, err = cryptopia.cancel_trade("All", None, None)
    if err == None:
        print('Cancelled all orders')
        return True
    else:
        raise ValueError(err)

def getBalance(coin):
    success, err = cryptopia.get_balance(coin)
    return success["Available"]

if __name__ == "__main__":
    # inputs
    MARKET=''
    COIN=''
    AMOUNT_BOUGHT=0
    try:
        BTC_BALANCE = getBalance("BTC")
        print('BTC available balance is {}'.format(BTC_BALANCE))
        BTC_TRADE = input("How much BTC to trade ?")
        PROFIT_RATE = input("How much profit do u want ? E.g: 40, 30,..")
        PROFIT_FINAL_RATE = 1+int(PROFIT_RATE)/100
        INPUT_BUY_SAFETY_RATE = input("Bot will buy with askPrice*(1+X/100) to make sure buy order gets filled immediately. How much should that rate be ?Eg 0,10,15..")
        BUY_SAFETY_RATE = 1+int(INPUT_BUY_SAFETY_RATE)/100
        COIN = input("What coin to trade ?")
        MARKET = "{}_BTC".format(COIN)

        PRICE_BOUGHT, AMOUNT_BOUGHT=setBuyOrderWithRetry(MARKET, BTC_TRADE, BUY_SAFETY_RATE)
        while not isOrderFilled(MARKET):
            print('Buy order not filled.. Will cancel and try to buy again')
            cancelAllOrders()
            PRICE_BOUGHT, AMOUNT_BOUGHT=setBuyOrderWithRetry(MARKET, BTC_TRADE, BUY_SAFETY_RATE)

        print("Buy order FILLED! Bought {} of coins".format(AMOUNT_BOUGHT))

        setSellOrderWithRetry(MARKET, PRICE_BOUGHT*PROFIT_FINAL_RATE, AMOUNT_BOUGHT)

        while not isOrderFilled(MARKET):
            print("Sell order is not filled.. wait 0.5s")
            sleep(0.5)

        print("Sell order FILLED! Congrats! P&D succeeded")
    except KeyboardInterrupt:
        activated=input('Want to activate stop loss ? BOT will try to sell continuously. (y/n)')
        if activated == 'y':
            while True:
                cancelAllOrders()
                balance = getBalance(COIN)
                if balance > 0.0005:
                    success, err=cryptopia.get_market(MARKET)
                    ask_price = success['BidPrice']
                    setSellOrderWithRetry(MARKET, ask_price, balance)
                    sleep(0.5)
                else:
                    break
            print("Sell order FILLED!")
        sys.exit()

