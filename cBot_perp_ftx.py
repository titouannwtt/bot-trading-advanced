import ccxt
import pandas as pd
import json
import time

class cBot_perp_ftx():
    def __init__(self, apiKey=None, secret=None, subAccountName=None):
        ftxAuthObject = {
            "apiKey": apiKey,
            "secret": secret,
            'headers': {
                'FTX-SUBACCOUNT': subAccountName
            }
        }
        if ftxAuthObject['secret'] == None:
            self._auth = False
            self._session = ccxt.ftx()
        else:
            self._auth = True
            self._session = ccxt.ftx(ftxAuthObject)
        self._session.load_markets()

    def authentication_required(fn):
        """Annotation for methods that require auth."""
        def wrapped(self, *args, **kwargs):
            if not self._auth:
                print("You must be authenticated to use this method", fn)
                exit()
            else:
                return fn(self, *args, **kwargs)
        return wrapped

    def get_historical_since(self, symbol, timeframe, startDate):
        try:
            tempData = self._session.fetch_ohlcv(symbol, timeframe, int(
                time.time()*1000)-1209600000, limit=1000)
            dtemp = pd.DataFrame(tempData)
            timeInter = int(dtemp.iloc[-1][0] - dtemp.iloc[-2][0])
        except:
            return None

        finished = False
        start = False
        allDf = []
        startDate = self._session.parse8601(startDate)
        while(start == False):
            try:
                tempData = self._session.fetch_ohlcv(
                    symbol, timeframe, startDate, limit=1000)
                dtemp = pd.DataFrame(tempData)
                timeInter = int(dtemp.iloc[-1][0] - dtemp.iloc[-2][0])
                nextTime = int(dtemp.iloc[-1][0] + timeInter)
                allDf.append(dtemp)
                start = True
            except:
                startDate = startDate + 1209600000*2

        if dtemp.shape[0] < 1:
            finished = True
        while(finished == False):
            try:
                tempData = self._session.fetch_ohlcv(
                    symbol, timeframe, nextTime, limit=1000)
                dtemp = pd.DataFrame(tempData)
                nextTime = int(dtemp.iloc[-1][0] + timeInter)
                allDf.append(dtemp)
                if dtemp.shape[0] < 1:
                    finished = True
            except:
                finished = True
        result = pd.concat(allDf, ignore_index=True, sort=False)
        result = result.rename(
            columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
        result = result.set_index(result['timestamp'])
        result.index = pd.to_datetime(result.index, unit='ms')
        del result['timestamp']
        return result

    def get_last_historical(self, symbol, timeframe, limit):
        result = pd.DataFrame(data=self._session.fetch_ohlcv(
            symbol, timeframe, None, limit=limit))
        result = result.rename(
            columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
        result = result.set_index(result['timestamp'])
        result.index = pd.to_datetime(result.index, unit='ms')
        del result['timestamp']
        return result

    def get_min_order_amount(self, symbol):
        return self._session.markets_by_id[symbol]['limits']['amount']['min']

    def convert_amount_to_precision(self, symbol, amount):
        return self._session.amount_to_precision(symbol, amount)

    def convert_price_to_precision(self, symbol, price):
        return self._session.price_to_precision(symbol, price)

    @authentication_required
    def get_all_balance(self):
        try:
            allBalance = self._session.fetchBalance()
        except BaseException as err:
            raise TypeError("An error occured in get_all_balance", err)
        return allBalance['total']

    @authentication_required
    def get_balance_of_one_coin(self, coin):
        try:
            allBalance = self._session.fetchBalance()
        except BaseException as err:
            raise TypeError("An error occured in get_balance_of_one_coin", err)
        try:
            return allBalance['total'][coin]
        except:
            return 0

    @authentication_required
    def place_market_order(self, symbol, side, amount, leverage=1):
        try:
            return self._session.createOrder(
                symbol,
                'market',
                side,
                self.convert_amount_to_precision(symbol, amount * leverage),
                None
            )
        except BaseException as err:
            raise TypeError("An error occured in place_market_order", err)

    @authentication_required
    def place_reduce_market_order(self, symbol, side, amount, leverage=1):
        params = {
            'reduceOnly':True
        }
        try:
            return self._session.createOrder(
                symbol,
                'market',
                side,
                self.convert_amount_to_precision(symbol, amount * leverage),
                None,
                params
            )
        except BaseException as err:
            raise TypeError("An error occured in place_reduce_market_order", err)

    @authentication_required
    def place_limit_order(self, symbol, side, amount, price, leverage=1):
        try:
            return self._session.createOrder(
                symbol,
                'limit',
                side,
                self.convert_amount_to_precision(symbol, amount * leverage),
                self.convert_price_to_precision(symbol, price)
                )
        except BaseException as err:
            raise TypeError("An error occured in place_limit_order", err)

    @authentication_required
    def place_reduce_limit_order(self, symbol, side, amount, price, leverage=1):
        params = {
            'reduceOnly':True
        }
        try:
            return self._session.createOrder(
                symbol,
                'limit',
                side,
                self.convert_amount_to_precision(symbol, amount * leverage),
                self.convert_price_to_precision(symbol, price),
                params
                )
        except BaseException as err:
            raise TypeError("An error occured in place_reduce_limit_order", err)

    @authentication_required
    def place_market_stop_loss(self, symbol, side, amount, price, leverage=1):
        params = {
        'stopPrice': self.convert_price_to_precision(symbol, price),  # your stop price
        'reduceOnly':True
        }
        try:
            return self._session.createOrder(
                symbol,
                'stop',
                side,
                self.convert_amount_to_precision(symbol, amount * leverage),
                None,
                params
                )
        except BaseException as err:
            raise TypeError("An error occured in place_market_stop_loss", err)

    @authentication_required
    def place_market_take_profit(self, symbol, side, amount, price, leverage=1):
        params = {
        'stopPrice': self.convert_price_to_precision(symbol, price),  # your stop price
        'reduceOnly':True
        }
        try:
            return self._session.createOrder(
                symbol,
                'takeProfit',
                side,
                self.convert_amount_to_precision(symbol, amount * leverage),
                None,
                params
                )
        except BaseException as err:
            raise TypeError("An error occured in place_market_take_profit", err)


    @authentication_required
    def cancel_all_open_order(self, symbol):
        try:
            return self._session.cancel_all_orders(symbol)
        except BaseException as err:
            raise TypeError("An error occured in cancel_all_open_order", err)

    @authentication_required
    def cancel_order_by_id(self, id):
        try:
            return self._session.cancel_order(id)
        except BaseException as err:
            raise TypeError("An error occured in cancel_order_by_id", err)

    @authentication_required
    def get_open_order(self, symbol=None):
        try:
            return self._session.fetchOpenOrders(symbol, None, None)
        except BaseException as err:
            raise TypeError("An error occured in get_open_order", err)

    @authentication_required
    def get_open_conditionnal_order(self, symbol=None):
        params = {
            'type':'stop'
        }
        try:
            return self._session.fetchOpenOrders(symbol,None,None,params)
        except BaseException as err:
            raise TypeError("An error occured in get_open_conditionnal_order", err)

    @authentication_required
    def get_my_trades(self, symbol=None, since=None, limit=1):
        try:
            return self._session.fetch_my_trades(symbol, since, limit)
        except BaseException as err:
            raise TypeError("An error occured in get_my_trades", err)

    @authentication_required
    def get_open_position(self,symbol=None):
        try:
            positions = self._session.fetchPositions(symbol)
            truePositions = []
            for position in positions:
                if float(position['contracts']) > 0:
                    truePositions.append(position)
            return truePositions
        except BaseException as err:
            raise TypeError("An error occured in get_open_position", err)

    @authentication_required
    def close_all_open_position(self,symbol=None):
        try:
            positions = self._session.fetchPositions(symbol)
            for position in positions:
                if position['side'] == 'long' and position['contracts'] > 0:
                    self.place_reduce_market_order(position['symbol'], 'sell', position['contracts'])
                elif position['side'] == 'short' and position['contracts'] > 0:
                    self.place_reduce_market_order(position['symbol'], 'buy', position['contracts'])
            return 'Close all positions done'
        except BaseException as err:
            raise TypeError("An error occured in close_all_open_position", err)
