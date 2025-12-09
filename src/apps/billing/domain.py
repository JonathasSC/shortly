class Pricing:
    def __init__(self):
        self.prices = {
            10: 5.99,
            20: 10.99,
            50: 24.99,
            100: 39.99,
        }
        
    def get_package_price(self, amount):
        return self.prices.get(amount)
