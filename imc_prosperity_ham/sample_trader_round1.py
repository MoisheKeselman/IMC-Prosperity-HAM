from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order, Trade

PEARLS = 'PEARLS'
BANANAS = 'BANANAS'

MAX_BANANA = 20
MAX_PEARL = 20
MAX_COCONUT = 600
MAX_PINACOLADA = 300

class Trader:
    PEARLS_PRICE = 10000
    BANANA_PRICE = 5000
    PINACOLADA_PRICE = 15000
    COCONUT_PRICE = 8000

    BANANA_SMA_BIG_SIZE = 200
    BANANA_SMA_LITTLE_SIZE = 50

    banana_prices = [0]
    banana_sma_big = 0
    banana_sma_little = 0

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        # print(state.own_trades)
        print(state.position)

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():

            # Check if the current product is the PEARLS product, only then run the order logic
            if product == PEARLS:

                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Add all the above orders to the result dict
                result[PEARLS] = self.process_pearls(order_depth)
                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above

            if product == BANANAS:
                order_depth: OrderDepth = state.order_depths[product]
                market_trades: List[Trade] = state.market_trades.get(product, [])

                orders = self.process_bananas(order_depth, market_trades)

                result[BANANAS] = orders

        return result
    
    def process_pearls(self, order_depth: OrderDepth) -> List[Order]:
        # Initialize the list of Orders to be sent as an empty list
        orders: list[Order] = []

        # If statement checks if there are any SELL orders in the PEARLS market
        for ask in sorted(order_depth.sell_orders.keys()):
            best_ask_volume = order_depth.sell_orders[ask]
            if ask < self.PEARLS_PRICE:
                print("BUY", str(-best_ask_volume) + "x PEARL", ask)
                orders.append(Order(PEARLS, ask, -best_ask_volume))

        # The below code block is similar to the one above,
        # the difference is that it finds the highest bid (buy order)
        # If the price of the order is higher than the fair value
        # This is an opportunity to sell at a premium
        for bid in sorted(order_depth.buy_orders.keys(), reverse=True):
            best_bid_volume = order_depth.buy_orders[bid]
            if bid > self.PEARLS_PRICE:
                print("SELL", str(best_bid_volume) + "x PEARL", bid)
                orders.append(Order(PEARLS, bid, -best_bid_volume))

        return orders
    
    def process_bananas(self, order_depth: OrderDepth, market_trades: List[Trade]) -> List[Order]:
        orders: list[Order] = []

        if len(market_trades):
            total = 0
            quantity = 0

            for trade in market_trades:
                total += trade.price * trade.quantity
                quantity += trade.quantity
            
            weighted_market_price = total / quantity

            print(f'BANANAS market price: {weighted_market_price}')
            self.banana_prices.append(weighted_market_price)
        else:
            self.banana_prices.append(self.banana_prices[-1])

        if len(self.banana_prices) > self.BANANA_SMA_BIG_SIZE:
            # Make sure we have warmed up
            self.banana_sma_big = sum(self.banana_prices[-self.BANANA_SMA_BIG_SIZE:]) / self.BANANA_SMA_BIG_SIZE
            self.banana_sma_little = sum(self.banana_prices[-self.BANANA_SMA_LITTLE_SIZE:]) / self.BANANA_SMA_LITTLE_SIZE

            if self.banana_sma_big > self.banana_sma_little:
                # sell
                if len(order_depth.buy_orders):
                    bid = max(order_depth.buy_orders.keys())
                    # best_bid_volume = order_depth.buy_orders[bid]
                    best_bid_volume = 1
                    print("SELL", str(best_bid_volume) + "x BANANA", bid)
                    orders.append(Order(BANANAS, bid, -best_bid_volume))
            else:
                # buy
                if len(order_depth.sell_orders):
                    ask = min(order_depth.sell_orders.keys())
                    # best_ask_volume = order_depth.sell_orders[ask]
                    best_ask_volume = -1
                    print("BUY", str(-best_ask_volume) + "x BANANA", ask)
                    orders.append(Order(BANANAS, ask, -best_ask_volume))
    
        return orders

