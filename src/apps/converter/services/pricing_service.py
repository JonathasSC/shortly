from apps.converter.enums import PricingRule


class PricingService:
    RULE_COSTS = {
        PricingRule.BASE: 1,
        PricingRule.DIRECT: 1,
        PricingRule.PERMANENT: 1,
    }

    @classmethod
    def calculate_cost(cls, *, is_direct: bool, is_permanent: bool) -> int:
        cost = cls.RULE_COSTS[PricingRule.BASE]

        if is_direct:
            cost += cls.RULE_COSTS[PricingRule.DIRECT]

        if is_permanent:
            cost += cls.RULE_COSTS[PricingRule.PERMANENT]

        return cost
