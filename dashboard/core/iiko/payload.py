from datetime import datetime, timedelta


class BasePayload(dict):
    def __init__(self, filters: list[dict] = None):
        super(BasePayload, self).__init__()
        _filters = {
            "DeletedWithWriteoff": {
                "filterType": "IncludeValues",
                "values": ["NOT_DELETED"]
            },
            "OrderDeleted": {
                "filterType": "IncludeValues",
                "values": ["NOT_DELETED"]
            }
        }
        if filters:
            for _filter in filters:
                _filters.update(_filter)
        self.update({
            "reportType": "SALES",
            "groupByRowFields": [],
            "groupByColFields": [],
            "aggregateFields": [],
            "filters": _filters
        })


class TotalStatsPayload(BasePayload):
    def __init__(self, filters: list[dict] = None):
        super(TotalStatsPayload, self).__init__(filters)
        self.update({
            "aggregateFields": [
                "UniqOrderId.OrdersCount",  # Количество заказов
                "GuestNum",  # Количество гостей
                "ProductCostBase.Profit",  # Наценка
                "ProductCostBase.MarkUp",  # Наценка (%)
                "DiscountPercent",  # Процент скидки
                "ProductCostBase.ProductCost",  # Себестоимость
                "ProductCostBase.Percent",  # Себестоимость (%)
                "OrderTime.AveragePrechequeTime",  # Ср. время в пречеке (мин)
                "GuestNum.Avg",  # Ср. количество гостей на чек
                "DishDiscountSumInt.average",  # Средняя сумма заказа
                "DishReturnSum",  # Сумма возврата
                "DiscountSum",  # Сумма скидки
                "DishDiscountSumInt"  # Сумма со скидкой
            ]
        })


class OrdersPayload(BasePayload):
    def __init__(self, filters: list[dict] = None):
        super(OrdersPayload, self).__init__(filters)
        self.update({
            "groupByRowFields": ["PayTypes", "OrderType"],
            "aggregateFields": [
                "DishDiscountSumInt",  # Сумма со скидкой
                "UniqOrderId",
            ],
        })


class DishesCategoriesPayload(BasePayload):
    def __init__(self, filters: list[dict] = None):
        super(DishesCategoriesPayload, self).__init__(filters)
        self.update({
            "groupByRowFields": ["DishCategory"],
            "aggregateFields": [
                "DishAmountInt"
            ],
        })


class DishesPayload(BasePayload):
    def __init__(self, filters: list[dict] = None):
        super(DishesPayload, self).__init__(filters)
        self.update({
            "groupByRowFields": ["DishName"],
            "aggregateFields": [
                "DishAmountInt"
            ],
        })


class DepartmentsPayload(BasePayload):
    def __init__(self):
        super(DepartmentsPayload, self).__init__()
        self.update({
            "groupByRowFields": ["Department"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": str(datetime.now().date() - timedelta(7)),
                    "to": str(datetime.now().date() - timedelta(1)),
                    "includeLow": "true",
                    "includeHigh": "true"
                }
            }
        })


class CashboxesPayload(BasePayload):
    def __init__(self, filters: list[dict] = None):
        super(CashboxesPayload, self).__init__(filters)
        self.update({
            "groupByRowFields": ["CashRegisterName", "PayTypes"],
            "aggregateFields": [
                "DishDiscountSumInt"
            ]
        })


class ReportsPayload(BasePayload):
    def __init__(self, filters: list[dict] = None):
        super(ReportsPayload, self).__init__(filters)
        self.update({
            "groupByRowFields": [
                "DishId",
                "DishName",
                "Store.Name",
                "Department",
                "OpenDate.Typed"
            ],
            "aggregateFields": [
                "DishAmountInt",
                "ProductCostBase.ProductCost",
                "DishSumInt"
            ]
        })
