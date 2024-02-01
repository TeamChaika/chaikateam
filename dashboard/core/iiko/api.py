import json

import requests
import xmltodict

from hashlib import sha1
from urllib.parse import urlencode

from dicttoxml import dicttoxml

from core.cache.base import BaseCache
from env import iiko_host, iiko_username, iiko_password
from .payload import (
    TotalStatsPayload,
    OrdersPayload,
    DishesCategoriesPayload,
    DishesPayload,
    CashboxesPayload,
    DepartmentsPayload,
    ReportsPayload
)
from .exceptions import RequestFailed


class IikoApi:
    def __init__(
        self,
        host: str = iiko_host,
        username: str = iiko_username,
        password: str = iiko_password,
        cache: BaseCache = None
    ):
        self._host = host
        self._username = username
        self._password = password
        self._cache = cache

    def _authorize(self):
        headers = {
            'content-type': 'application/json;charset=utf-8'
        }
        params = {
            'login': self._username,
            'pass': self._password
        }

        url = self._host + '/resto/api/auth?' + urlencode(params)

        r = requests.get(url=url, headers=headers, timeout=5)
        if r.status_code != 200:
            print(r.status_code, r.text)
            raise RequestFailed()
        self._cache.set(
            f'api_key:{sha1(self._host.encode()).hexdigest()}',
            r.text, 900
        )

        return r.text

    def _get_api_key(self):
        api_key = None
        if self._cache:
            api_key = self._cache.get(
                f'api_key:{sha1(self._host.encode()).hexdigest()}'
            )
        if not api_key:
            api_key = self._authorize()
        return api_key

    def _make_request(
        self,
        endpoint: str,
        method: str = 'POST',
        params: dict = None,
        data: dict = None,
        content_type: str = 'json',
    ):
        if not params:
            params = {}
        params['key'] = self._get_api_key()
        headers = {
            'content-type': f'application/{content_type};charset=utf-8'
        }
        if data:
            if content_type == 'json':
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif content_type == 'xml':
                data = dicttoxml(data, custom_root='document', attr_type=False)
        send = requests.post if method == 'POST' else requests.get
        response = send(
            url=self._host+endpoint,
            headers=headers,
            params=params,
            data=data
        )
        if response.status_code != 200:
            print(response.status_code, response.text)
            raise RequestFailed()
        response_content = response.headers.get('Content-Type')
        if response_content.startswith('application/json'):
            loaded = json.loads(response.text)
            if isinstance(loaded, dict) and 'data' in loaded:
                return loaded.get('data')
            return loaded
        elif response_content.startswith('application/xml'):
            return xmltodict.parse(response.text)
        else:
            return response.text

    def _request_nomenclature(self):
        response = self._make_request(
            '/resto/api/products',
            method='GET',
            content_type='xml'
        ).get('productDtoes').get(
            'productDto'
        )
        nomenclature = {
            'id': {
                product.get('id'): product.get('name')
                for product in response
                if product.get('productType') in {'GOODS', 'PREPARED'}
            }, 'name': {
                product.get('name'): product.get('id')
                for product in response
                if product.get('productType') in {'GOODS', 'PREPARED'}
            }
        }
        if self._cache:
            self._cache.set(
                f'nomenclature:{sha1(self._host.encode()).hexdigest()}',
                json.dumps(nomenclature),
                86400
            )
        return nomenclature

    def get_nomenclature(self):
        nomenclature = None
        if self._cache:
            cached = self._cache.get(
                f'nomenclature:{sha1(self._host.encode()).hexdigest()}'
            )
            if cached:
                nomenclature = json.loads(cached)
        if not nomenclature:
            nomenclature = self._request_nomenclature()
        return nomenclature

    def get_nomenclature_part(self, data: dict):
        return self._make_request(
            '/resto/api/v2/entities/products/list?',
            method='GET',
            data=data
        )

    def update_product(self, product: dict):
        return self._make_request(
            '/resto/api/v2/entities/products/update',
            data=product,
            params={'overrideFastCode': 'true'}
        )

    def get_departments(self):
        return self._make_request(
            '/resto/api/corporation/departments/',
            method='GET',
            content_type='xml'
        ).get('corporateItemDtoes').get(
            'corporateItemDto'
        )

    def get_stats_departments(self):
        payload = DepartmentsPayload()
        return self._make_request(
            '/resto/api/v2/reports/olap',
            data=payload
        )

    def get_stores(self):
        return self._make_request(
            '/resto/api/corporation/stores/',
            method='GET',
            content_type='xml'
        ).get('corporateItemDtoes').get(
            'corporateItemDto'
        )

    def get_total_stats(self, filters: list[dict] = None):
        payload = TotalStatsPayload(filters)
        return self._make_request(
            '/resto/api/v2/reports/olap',
            data=payload
        )

    def get_orders_stats(self, filters: list[dict] = None):
        payload = OrdersPayload(filters)
        return self._make_request(
            '/resto/api/v2/reports/olap',
            data=payload
        )

    def get_dishes_categories_stats(self, filters: list[dict] = None):
        payload = DishesCategoriesPayload(filters)
        return self._make_request(
            '/resto/api/v2/reports/olap',
            data=payload
        )

    def get_dishes_stats(self, filters: list[dict] = None):
        payload = DishesPayload(filters)
        return self._make_request(
            '/resto/api/v2/reports/olap',
            data=payload
        )

    def get_cashboxes_stats(self, filters: list[dict] = None):
        payload = CashboxesPayload(filters)
        return self._make_request(
            '/resto/api/v2/reports/olap',
            data=payload
        )

    def get_reports_data(self, filters: list[dict] = None):
        payload = ReportsPayload(filters)
        return self._make_request(
            '/resto/api/v2/reports/olap',
            data=payload
        )

    def load_waybill(self, waybill: dict):
        return self._make_request(
            '/resto/api/documents/import/outgoingInvoice?',
            data=waybill
        ).get(
            'documentValidationResult'
        )

    def load_writeoff(self, writeoff: dict):
        return self._make_request(
            '/resto/api/v2/documents/writeoff',
            data=writeoff
        ).get('result')
