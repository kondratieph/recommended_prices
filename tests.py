"""Тесты для recommend_price. Запуск: python -m unittest -v"""

import asyncio
import time
import unittest
from decimal import Decimal as D

from starter import recommend_price, sample_fetch_offers


def offers(*items, status="success"):
    """Строит fetch_offers из кортежей (seller, price, delivery_days)."""

    async def fetch():
        return {
            "status": status,
            "offers": [
                {"seller": s, "price": D(p), "delivery_days": d} for s, p, d in items
            ],
        }

    return fetch


class RecommendPriceTests(unittest.IsolatedAsyncioTestCase):

    async def test_rounds_down_not_half_up(self):
        # 100.01 * 0.985 = 98.50985 -> 98.50, а не 98.51
        r = await recommend_price(offers(("A", "100.01", 1)), D("100.00"), D("50.00"))
        self.assertEqual((r["price"], r["decision"]), (D("98.50"), "APPLY"))

    async def test_no_suitable_offers_holds_even_below_min_price(self):
        r = await recommend_price(offers(("MYSHOP", "10.00", 1)), D("90.00"), D("100.00"))
        self.assertEqual((r["price"], r["decision"]), (D("90.00"), "HOLD"))

    async def test_exactly_30_percent_is_allowed_above_is_review(self):
        # min_price задаёт рекомендацию: 130.00 при текущей 100.00
        fetch = offers(("A", "50.00", 1))
        r = await recommend_price(fetch, D("100.00"), D("130.00"))
        self.assertEqual((r["price"], r["decision"]), (D("130.00"), "APPLY"))
        r = await recommend_price(fetch, D("100.00"), D("130.01"))
        self.assertEqual((r["price"], r["decision"]), (D("130.01"), "REVIEW"))


if __name__ == "__main__":
    unittest.main()
