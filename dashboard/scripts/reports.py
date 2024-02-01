import pandas as pd

from io import BytesIO
from contextlib import suppress
from collections import defaultdict
from datetime import datetime, timedelta

from telebot.types import InputFile

from core.telegram import telegram_bot
from core.iiko import iiko_api
from core.iiko.filters import DateFilter


chats = {
    'Чайка на пляже': -1001608641704,
    'Терияки': -1001628706792,
    'Гастро Двор': -1001651156709,
    'ХАНГРИ': -1001600129897,
    'Hungry birds': -1001739853628,
    'Симеиз': -1001736845172,
    'Чайка': -1001545548654,
    'Небо Пляж': -1001525541026,
    'PTIZZA': -1001697363455
}


def get_olap():
    date = (datetime.today() - timedelta(1)).date()
    filters = [DateFilter(date, date)]
    return iiko_api.get_reports_data(filters)


def get_nomenclature(olap_data: dict):
    request_data = {'ids': [item['DishId'] for item in olap_data]}
    return {
        item['id']: item
        for item in iiko_api.get_nomenclature_part(request_data)
    }


def update_color(item: dict, surcharge: int):
    if not item:
        return

    if surcharge < 100:
        r, g, b = 255, 69, 0
    elif 100 <= surcharge < 150:
        r, g, b = 255, 165, 0
    elif 150 <= surcharge < 200:
        r, g, b = 255, 215, 0
    else:
        r, g, b = 50, 205, 50

    if item['color']['red'] == r and \
       item['color']['green'] == g and \
       item['color']['blue'] == b:
        return

    item['color'] = {
        'red': r,
        'green': g,
        'blue': b
    }

    return iiko_api.update_product(item)


def get_reports(olap_data: dict, nomenclature: dict):
    reports = defaultdict(list)
    for item in olap_data:
        product_cost_base = item['ProductCostBase.ProductCost']
        if product_cost_base <= 1:
            continue
        dish_sum = item['DishSumInt']
        dish_amount = item['DishAmountInt']
        surcharge = round((
            int(dish_sum) - int(product_cost_base)
        ) / int(product_cost_base) * 100, 2)
        price = round(dish_sum / dish_amount, 2)
        cost = round(product_cost_base / dish_amount, 2)
        update_color(nomenclature.get(item['DishId']), surcharge)
        if surcharge < 150 and price > 0:
            reports[item['Department']].append((
                item.get('DishName'),
                surcharge,
                cost,
                price,
                item.get('DishAmountInt')
            ))
    return reports


def load_report(department: str, items: list):
    df = pd.DataFrame(
        items,
        columns=[
            'Наименование', 'Наценка', 'Себестоимость', 'Цена',
            'Количество'
        ]
    )
    buff = BytesIO()
    writer = pd.ExcelWriter(buff)
    df.to_excel(writer, sheet_name=department, index=False)
    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets[department].set_column(col_idx, col_idx, column_length)
    writer.close()
    buff.seek(0)
    return InputFile(buff)


def send_reports(report: dict[list]):
    for department, items in report.items():
        if department not in chats:
            continue
        date = (datetime.today() - timedelta(1)).strftime("%d %m")
        filename = f'Отчёт по наценкам «{date}».xlsx'
        with suppress(Exception):
            telegram_bot.send_document(
                chats.get(department),
                load_report(department, items),
                visible_file_name=filename
            )


def run():
    olap_data = get_olap()
    nomenclature = get_nomenclature(olap_data)
    reports = get_reports(olap_data, nomenclature)
    send_reports(reports)
