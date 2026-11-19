import asyncio
from decimal import ROUND_DOWN, Decimal

TIMEOUT = 2.0
OWN_SELLER = "myshop"
MAX_DELIVERY_DAYS = 6
UNDERCUT = Decimal("0.985")  # минус 1,5%
REVIEW_LIMIT = Decimal("0.30")  # ровно 30% допускается
CENT = Decimal("0.01")


def _result(price, decision, reason):
    return {"price": price, "decision": decision, "reason": reason}


def _is_suitable(offer):
    days = offer["delivery_days"]
    return (
        days is not None
        and days <= MAX_DELIVERY_DAYS
        and offer["seller"].casefold() != OWN_SELLER.casefold()
    )


async def recommend_price(fetch_offers, current_price, min_price, timeout_s=TIMEOUT):
    # Правило 1: ожидание ограничено, любой сбой источника -> HOLD.
    try:
        result = await asyncio.wait_for(fetch_offers(), timeout=timeout_s)
    except asyncio.TimeoutError:
        return _result(current_price, "HOLD", "Источник не ответил за отведённое время")
    except Exception:
        return _result(current_price, "HOLD", "Ошибка источника предложений")
    if result["status"] != "success":
        return _result(current_price, "HOLD", "Источник вернул неполные данные или ошибку")

    # Правила 2-3: подходящие предложения; если их нет -> HOLD.
    prices = [offer["price"] for offer in result["offers"] if _is_suitable(offer)]
    if not prices:
        return _result(current_price, "HOLD", "Нет подходящих предложений конкурентов")

    # Правило 4: минус 1,5% с округлением вниз до копейки, но не ниже min_price.
    undercut = (min(prices) * UNDERCUT).quantize(CENT, rounding=ROUND_DOWN)
    price = max(undercut, min_price)

    # Правило 5: отклонение больше 30% -> REVIEW (сравнение без деления).
    if abs(price - current_price) > current_price * REVIEW_LIMIT:
        return _result(price, "REVIEW", "Цена изменилась более чем на 30%, нужна ручная проверка")
    reason = (
        "Применена минимальная допустимая цена"
        if price == min_price and undercut < min_price
        else "Цена конкурента минус 1,5%"
    )
    return _result(price, "APPLY", reason)


async def sample_fetch_offers():
    return {
        "status": "success",
        "offers": [
            {"seller": "myshop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ],
    }


if __name__ == "__main__":
    print(asyncio.run(recommend_price(
        sample_fetch_offers,
        current_price=Decimal("4900.00"),
        min_price=Decimal("4500.00"),
    )))
