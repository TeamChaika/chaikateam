from collections import defaultdict

from .config import stats_list


def process_stats(
    total_stats: list[dict],
    orders_stats: list[dict]
):
    processed = defaultdict(int)
    process_total_stats(total_stats, processed)
    process_orders_stats(orders_stats, processed)

    return [
        (name, '{0:,}'.format(
            round(processed.get(key, 0), 2)
        ).replace(',', ' ').replace('.', ','))
        for key, name in stats_list
    ]


def process_total_stats(
    data: list[dict],
    result: dict
):
    data = data[0] if data else {}
    for key, value in data.items():
        if not isinstance(value, int) and not isinstance(value, float):
            continue
        if key in [
            'ProductCostBase.MarkUp',
            'DiscountPercent',
            'ProductCostBase.Percent'
        ]:
            result[key] = value * 100
        elif key != 'Department':
            result[key] = value


def process_orders_stats(
    data: list[dict],
    result: dict
):
    for item in data:
        pay_type = item.get('PayTypes')
        dish_discount_sum = item.get('DishDiscountSumInt', 0)
        if pay_type in [
            'Наличные ФИСКАЛКА', 'Наличные ВФР'
        ]:
            result['CashSum'] += dish_discount_sum
        elif pay_type not in ['(без оплаты)', 'Оплата бон']:
            result['CashLessSum'] += dish_discount_sum

        order_type = item.get('OrderType')
        orders_count = item.get('UniqOrderId', 0)
        if order_type == 'Доставка курьером':
            result['CourierOrders'] += orders_count
        elif order_type == 'Доставка самовывоз':
            result['PickupOrders'] += orders_count


def process_dishes(
    categories: list[dict],
    dishes: list[dict],
    dishes_data: list[tuple]
):
    categories = {
        category['DishCategory']: category['DishAmountInt']
        for category in categories
    }
    dishes = {
        dish['DishName']: dish['DishAmountInt']
        for dish in dishes
    }
    results = []
    for category, dish, name, gift in dishes_data:
        result = {'name': name}
        if category:
            result['amount'] = categories.get(category, 0)
        elif dish:
            result['amount'] = dishes.get(dish, 0)
        if gift:
            gift_category, gift_dish = gift
            if gift_category:
                result['gift'] = categories.get(gift_category, 0)
            else:
                result['gift'] = dishes.get(gift_dish, 0)
        results.append(result)
    return results
