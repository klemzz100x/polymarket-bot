from decimal import Decimal


class FeeModel:
    def __init__(self, fee_bps: Decimal = Decimal("0")) -> None:
        self.fee_bps = fee_bps

    def calculate(self, notional: Decimal) -> Decimal:
        if self.fee_bps <= 0 or notional <= 0:
            return Decimal("0")
        return notional * self.fee_bps / Decimal("10000")

