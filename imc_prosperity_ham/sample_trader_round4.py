import json
from typing import Any, Dict, List, Tuple
from datamodel import OrderDepth, TradingState, Order, Trade, ProsperityEncoder, Symbol

PEARLS = 'PEARLS'
BANANAS = 'BANANAS'
COCONUTS = 'COCONUTS'
PINA_COLADAS = 'PINA_COLADAS'
DIVING_GEAR = 'DIVING_GEAR'
DOLPHIN_SIGHTINGS = 'DOLPHIN_SIGHTINGS'
DIVING_GEAR = 'DIVING_GEAR'
BERRIES = 'BERRIES'
PICNIC_BASKET = 'PICNIC_BASKET'
BAGUETTE = 'BAGUETTE'
DIP = 'DIP'
UKULELE = 'UKULELE'
PICNIC_BASKET = 'PICNIC_BASKET'

MAX_BANANA = 20
MAX_PEARL = 20
MAX_COCONUT = 600
MAX_PINACOLADA = 300
MAX_DIVING_GEAR = 50
MAX_BERRIES = 250
MAX_BAGUETTE = 150
MAX_DIP = 300
MAX_UKULELE = 70
MAX_PICNIC_BASKET = 70

class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]]) -> None:
        print(json.dumps({
            "state": state,
            "orders": orders,
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True))

        self.logs = ""

logger = Logger()

class Trader:
    PEARLS_PRICE = 10000
    BANANA_PRICE = 5000
    PINACOLADA_PRICE = 15000
    COCONUT_PRICE = 8000
    DOLPHIN_PRICE = 3000
    DIVING_GEAR_PRICE = 100000
    BAGUETTE_PRICE = 12000
    DIP_PRICE = 7000
    UKULELE_PRICE = 20000
    PICNIC_BASKET_PRICE = 74000

    BANANA_SMA_BIG_SIZE = 200
    BANANA_SMA_LITTLE_SIZE = 50

    TOTAL_TIME = 1000
    current_time = 0

    banana_prices = [0]
    banana_sma_big = 0
    banana_sma_little = 0

    last_pina_price = PINACOLADA_PRICE
    last_coco_price = COCONUT_PRICE

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        # logger.print(state.own_trades)
        logger.print(state.position)

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

        # Process coconuts and pinacoladas together
        pina_order_depth: OrderDepth = state.order_depths[PINA_COLADAS]
        coco_order_depth: OrderDepth = state.order_depths[COCONUTS]

        pina_orders, coco_orders = self.process_coconuts_and_pinacoladas(pina_order_depth, coco_order_depth)
        result[PINA_COLADAS] = pina_orders
        result[COCONUTS] = coco_orders

        # Process dolphin sightings and diving gear
        dolphin_order_depth: OrderDepth = state.order_depths[DOLPHIN_SIGHTINGS]
        diving_order_depth: OrderDepth = state.order_depths[DIVING_GEAR]
        result[DIVING_GEAR] = self.process_diving_gear(diving_order_depth, dolphin_order_depth)

        # Process berries
        result[BERRIES] = self.process_berries(state.order_depths[BERRIES])

        # Process picnic baskets
        baguette_order_depth: OrderDepth = state.order_depths[BAGUETTE]
        dip_order_depth: OrderDepth = state.order_depths[DIP]
        ukulele_order_depth: OrderDepth = state.order_depths[UKULELE]
        picnic_order_depth: OrderDepth = state.order_depths[PICNIC_BASKET]
        result[PICNIC_BASKET] = self.process_picnic_baskets(baguette_order_depth, dip_order_depth, ukulele_order_depth, picnic_order_depth)

        logger.print(result)

        logger.flush(state, orders)

        return result
    
    def process_pearls(self, order_depth: OrderDepth) -> List[Order]:
        # Initialize the list of Orders to be sent as an empty list
        orders: list[Order] = []

        # If statement checks if there are any SELL orders in the PEARLS market
        for ask in sorted(order_depth.sell_orders.keys()):
            best_ask_volume = order_depth.sell_orders[ask]
            if ask < self.PEARLS_PRICE:
                logger.print("BUY", str(-best_ask_volume) + "x PEARL", ask)
                orders.append(Order(PEARLS, ask, -best_ask_volume))

        # The below code block is similar to the one above,
        # the difference is that it finds the highest bid (buy order)
        # If the price of the order is higher than the fair value
        # This is an opportunity to sell at a premium
        for bid in sorted(order_depth.buy_orders.keys(), reverse=True):
            best_bid_volume = order_depth.buy_orders[bid]
            if bid > self.PEARLS_PRICE:
                logger.print("SELL", str(best_bid_volume) + "x PEARL", bid)
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

            logger.print(f'BANANAS market price: {weighted_market_price}')
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
                    orders.append(self.sell_highest_bid(BANANAS, order_depth.buy_orders, 1))
            else:
                # buy
                if len(order_depth.sell_orders):
                    orders.append(self.buy_lowest_ask(BANANAS, order_depth.sell_orders, 1))
    
        return orders

    def process_coconuts_and_pinacoladas(self, pina_od: OrderDepth, coco_od: OrderDepth) -> Tuple[List[Order], List[Order]]:
        '''
        Very simple pair trading algorithm. Buy the cheaper product, sell the more expensive one.

        Parameters:
        pina_od: OrderDepth
            Order depth for Pina Coladas
        coco_od: OrderDepth
            Order depth for Coconuts

        Returns:
        List[Order] for Pina Coladas
        List[Order] for Coconuts
        '''
        pina_orders: list[Order] = []
        coco_orders: list[Order] = []

        standardized_pina_price = (max(pina_od.buy_orders.keys()) + min(pina_od.sell_orders.keys())) / 2 / self.PINACOLADA_PRICE
        standardized_coco_price = (max(coco_od.buy_orders.keys()) + min(coco_od.sell_orders.keys())) / 2 / self.COCONUT_PRICE

        logger.print(f'Pina Coladas Price: {standardized_pina_price:.4f}, Coco Price: {standardized_coco_price:.4f}, \
              {"Coconuts cheaper" if standardized_pina_price > standardized_coco_price else "Pina Coladas cheaper"}')
        
        trade_factor = 1/30

        if standardized_pina_price > standardized_coco_price:
            # short pina, long coco
            if len(pina_od.sell_orders):
                pina_orders.append(self.sell_highest_bid(PINA_COLADAS, pina_od.sell_orders, quantity=trade_factor*MAX_PINACOLADA))
            if len(coco_od.buy_orders):
                coco_orders.append(self.buy_lowest_ask(COCONUTS, coco_od.buy_orders, quantity=trade_factor*MAX_COCONUT))
        else:
            # long pina, short coco
            if len(pina_od.buy_orders):
                pina_orders.append(self.buy_lowest_ask(PINA_COLADAS, pina_od.buy_orders, quantity=trade_factor*MAX_PINACOLADA))
            if len(coco_od.sell_orders):
                coco_orders.append(self.sell_highest_bid(COCONUTS, coco_od.sell_orders, quantity=trade_factor*MAX_COCONUT))

        return pina_orders, coco_orders
    
    def process_diving_gear(self, diving_gear_od: OrderDepth, dolphins_od: OrderDepth):
        '''
        Very simple pair trading algorithm. Buy the cheaper product, sell the more expensive one.

        Parameters:
        diving_gear_od: OrderDepth
            Order depth for Diving Gear
        dolphins_od: OrderDepth
            Order depth for Dolphin Sightings

        Returns:
        List[Order] for Diving Gear
        '''
        diving_orders: list[Order] = []

        standardized_diving_price = (max(diving_gear_od.buy_orders.keys()) + min(diving_gear_od.sell_orders.keys())) / 2 / self.DIVING_GEAR_PRICE
        standardized_dolphin_price = (max(dolphins_od.buy_orders.keys()) + min(dolphins_od.sell_orders.keys())) / 2 / self.DOLPHIN_PRICE

        logger.print(f'Diving Price: {standardized_diving_price:.4f}, Dolphin Price: {standardized_dolphin_price:.4f}, \
              {"Dolphin cheaper" if standardized_diving_price > standardized_dolphin_price else "Diving cheaper"}')
        
        trade_factor = 1/30

        if standardized_diving_price > standardized_dolphin_price:
            if len(diving_gear_od.sell_orders):
                diving_orders.append(self.sell_highest_bid(DIVING_GEAR, diving_gear_od.sell_orders, quantity=trade_factor*MAX_DIVING_GEAR))
        else:
            if len(diving_gear_od.buy_orders):
                diving_orders.append(self.buy_lowest_ask(DIVING_GEAR, diving_gear_od.buy_orders, quantity=trade_factor*MAX_DIVING_GEAR))

        return diving_orders
    
    def process_berries(self, berries_od: OrderDepth):
        '''
        Buy up berries in the first part of round, sell at mid-point

        Parameters:
        berries_od : OrderDepth
            Order depth for berries

        Returns:
        List[Order] for berries
        '''
        self.current_time += 1

        berry_orders = []

        if self.current_time < self.TOTAL_TIME / 3 * 8:
            berry_orders.append(self.buy_lowest_ask(BERRIES, berries_od.sell_orders))
        elif self.current_time > self.TOTAL_TIME / 3 * 8:
            # sell when reaching top and always after that
            berry_orders.append(self.sell_highest_bid(BERRIES, berries_od.buy_orders))

        return berry_orders

    def process_picnic_baskets(self, baguette_od: OrderDepth, dip_od: OrderDepth, ukulele_od: OrderDepth, picnic_od: OrderDepth):
        '''
        Very simple pair trading algorithm. Buy the cheaper product, sell the more expensive one.

        Parameters:
        baguette_od: OrderDepth
            Order depth for baguettes
        dip_od: OrderDepth
            Order depth for dip
        ukulele_od: OrderDepth
            Order depth for ukuleles
        picnic_od: OrderDepth
            Order depth for picnic baskets

        Returns:
        List[Order] for picnic baskets
        '''
        picnic_orders: list[Order] = []

        standardized_baguette_price = (max(baguette_od.buy_orders.keys()) + min(baguette_od.sell_orders.keys())) / 2 / self.BAGUETTE_PRICE
        standardized_dip_price = (max(dip_od.buy_orders.keys()) + min(dip_od.sell_orders.keys())) / 2 / self.DIP_PRICE
        standardized_ukulele_price = (max(ukulele_od.buy_orders.keys()) + min(ukulele_od.sell_orders.keys())) / 2 / self.UKULELE_PRICE
        standardized_picnic_price = (max(picnic_od.buy_orders.keys()) + min(picnic_od.sell_orders.keys())) / 2 / self.PICNIC_BASKET_PRICE

        trade_factor = 1/30

        if standardized_picnic_price > (standardized_baguette_price + standardized_dip_price + standardized_ukulele_price)/ 3:
            # short pina, long coco
            if len(picnic_od.sell_orders):
                picnic_orders.append(self.sell_highest_bid(DIVING_GEAR, picnic_od.sell_orders, quantity=trade_factor*MAX_DIVING_GEAR))
        else:
            # long pina, short coco
            if len(picnic_od.buy_orders):
                picnic_orders.append(self.buy_lowest_ask(DIVING_GEAR, picnic_od.buy_orders, quantity=trade_factor*MAX_DIVING_GEAR))

        return picnic_orders
    
    def sell_highest_bid(self, product: str, buy_orders: Dict[int, int], quantity:int = None):
        """
        Parameters:
        product: str
            product to buy, i.e. "BANANAS"
        buy_orders: Dict[int, int]
            Dictionary mapping price to quantity
        quantity: int
            Positive number to sell. Defaults to None, which sells the quantity in the highest bid.
        """
        bid = max(buy_orders.keys())

        if quantity is None:
            quantity = buy_orders[bid]

        logger.print("SELL", str(quantity) + f"x {product} at ", bid)
        
        return Order(product, bid, -quantity)
    
    def buy_lowest_ask(self, product: str, sell_orders: Dict[int, int], quantity:int = None):
        """
        Parameters:
        product: str
            product to buy, i.e. "BANANAS"
        sell_orders: Dict[int, int]
            Dictionary mapping price to quantity
        quantity: int
            Positive number to buy. Defaults to None, which buys the quantity in the lowest ask.
        """
        ask = min(sell_orders.keys())

        if quantity is None:
            quantity = -sell_orders[ask] # make it negative because sell orders are negative

        logger.print("BUY", str(quantity) + f"x {product} at ", ask)
        
        return Order(product, ask, quantity)


