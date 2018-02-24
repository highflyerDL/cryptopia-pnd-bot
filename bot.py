import json
from api import Api
from time import sleep

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
    ask_price = success['AskPrice']*buy_safety_rate
    print('Trade for market {} has ask price {}'.format(market, ask_price))
    coin_amount = float(amount)/ask_price
    success, err=cryptopia.submit_trade(market, "Buy", ask_price, coin_amount)
    print('Set buy order at {} to buy {} of {} with {} BTC'.format(ask_price, coin_amount, market, amount))
    if err == None:
        return ask_price, coin_amount
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

def getBalance(coin):
    success, err = cryptopia.get_balance(coin)
    return success["Available"]

if __name__ == "__main__":
    # inputs
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
        print("Buy order is not filled.. wait 0.5s")
        sleep(0.5)
    print("Buy order FILLED! Bought {} of coins".format(AMOUNT_BOUGHT))

    setSellOrderWithRetry(MARKET, PRICE_BOUGHT*PROFIT_FINAL_RATE, AMOUNT_BOUGHT)

    while not isOrderFilled(MARKET):
        print("Sell order is not filled.. wait 0.5s")
        sleep(0.5)

    print("Sell order FILLED! Congrats! P&D succeeded")



