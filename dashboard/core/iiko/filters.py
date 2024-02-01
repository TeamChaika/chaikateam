from typing import Union
from datetime import datetime, timedelta


class DateFilter(dict):
    def __init__(
        self,
        date_from: Union[datetime, str],
        date_to: Union[datetime, str]
    ):
        super(DateFilter, self).__init__()
        if date_from and date_to and isinstance(date_from, str) \
           and isinstance(date_to, str):
            date_from = datetime.strptime(date_from, '%d.%m.%Y').date()
            date_to = datetime.strptime(date_to, '%d.%m.%Y').date()

        if not any([date_from, date_to]) or date_from > date_to:
            date_from = date_to = datetime.now().date() \
                if datetime.now().hour >= 8 \
                else datetime.now().date() - timedelta(1)

        self.date_from: datetime = date_from
        self.date_to: datetime = date_to
        self.update({
            "OpenDate.Typed": {
                "filterType": "DateRange",
                "periodType": "CUSTOM",
                "from": str(date_from),
                "to": str(date_to),
                "includeLow": "true",
                "includeHigh": "true"
            }
        })


class PayTypeFilter(dict):
    def __init__(self, pay_type: str):
        super(PayTypeFilter, self).__init__()
        values = ['Наличные'] if pay_type == 'cash' else [
            'Банковские карты', 'Картой  курьеру'
        ]
        self.update({
            "PayTypes": {
                "filterType": "IncludeValues",
                "values": values
            }
        })


class DepartmentFilter(dict):
    def __init__(self, department: str):
        super(DepartmentFilter, self).__init__()
        self.update({
            "Department": {
                "filterType": "IncludeValues",
                "values": [department]
            }
        })
