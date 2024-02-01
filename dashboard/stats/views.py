import pandas as pd

from urllib.parse import urlencode

from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required, permission_required

from env import data_dir
from core.decorators import http_methods
from core.iiko import iiko_api
from core.iiko.filters import DateFilter, PayTypeFilter, DepartmentFilter
from core.iiko.decorators import hook_iiko_fail
from .config import hungry_dishes_data, primorsky_dishes_data
from .processors import process_stats, process_dishes


@http_methods(['GET'])
@login_required(login_url='/login')
@permission_required('authentication.can_view_dashboard')
@hook_iiko_fail
def total_stats_view(request: HttpRequest):
    department = request.GET.get('department', 'all')
    pay_type = request.GET.get('pay_type', 'all')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    date_filter = DateFilter(date_from, date_to)

    filters = [date_filter]
    if department != 'all':
        filters.append(DepartmentFilter(department))
    if pay_type != 'all':
        filters.append(PayTypeFilter(pay_type))

    total_stats = iiko_api.get_total_stats(filters)
    orders_stats = iiko_api.get_orders_stats(filters)

    filters_string = '' \
        if [department, pay_type] == ['all', 'all'] \
        else '&' + urlencode({
            'department': department,
            'pay_type': pay_type
        })

    return render(request, 'stats/index.html', context={
        'user': request.user,
        'stats': process_stats(total_stats, orders_stats),
        'departments': [
            department.get('Department')
            for department in iiko_api.get_stats_departments()
        ],
        'pay_types': [
            ('cash', 'Наличные'),
            ('card', 'Безнал')
        ],
        'current_department': department,
        'current_pay_type': pay_type,
        'filters_string': filters_string,
        'date_from': date_filter.date_from.strftime('%d.%m.%Y'),
        'date_to': date_filter.date_to.strftime('%d.%m.%Y'),
    })


@http_methods(['GET'])
@login_required(login_url="/login")
@permission_required('authentication.can_view_hungry')
@hook_iiko_fail
def hungry_dishes_view(request: HttpRequest):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    date_filter = DateFilter(date_from, date_to)

    filters = [
        date_filter,
        DepartmentFilter('ХАНГРИ')
    ]

    dishes_categories_stats = iiko_api.get_dishes_categories_stats(filters)
    dishes_stats = iiko_api.get_dishes_stats(filters)

    return render(
        request, 'stats/hungry.html',
        context={
            'user': request.user,
            'data': process_dishes(
                dishes_categories_stats,
                dishes_stats,
                hungry_dishes_data
            ),
            'date_from': date_filter.date_from.strftime('%d.%m.%Y'),
            'date_to': date_filter.date_to.strftime('%d.%m.%Y'),
        }
    )


@http_methods(['GET'])
@login_required(login_url="/login")
@permission_required('authentication.can_view_guests')
def guests_view(request: HttpRequest):
    guests = pd.read_excel(data_dir)
    guests_output = []
    for _, (num, name, row_type, deleted) in guests.iterrows():
        guests_output.append({
            'id': int(num),
            'name': name,
            'type': row_type,
            'deleted': deleted
        })
    return render(
        request,
        'stats/guests.html',
        context={'guests': guests_output, 'user': request.user}
    )


@http_methods(['GET'])
@login_required(login_url="/login")
@permission_required('authentication.can_view_hungry')
@hook_iiko_fail
def prim_dishes_view(request: HttpRequest):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    date_filter = DateFilter(date_from, date_to)

    filters = [
        date_filter,
        DepartmentFilter('Хангри Приморский')
    ]

    dishes_categories_stats = iiko_api.get_dishes_categories_stats(filters)
    dishes_stats = iiko_api.get_dishes_stats(filters)

    return render(
        request, 'hungry.html',
        context={
            'user': request.user,
            'data': process_dishes(
                dishes_categories_stats,
                dishes_stats,
                primorsky_dishes_data
            ),
            'date_from': date_filter.date_from.strftime('%d.%m.%Y'),
            'date_to': date_filter.date_to.strftime('%d.%m.%Y'),
        }
    )
