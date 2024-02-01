from django.http import HttpResponse
from django.views import View
from django.db.models import Model

from .iiko import iiko_api
from .types import HttpRequest


class DocumentView(View):
    model: Model
    item_model: Model
    rel: str

    def render(self, request: HttpRequest) -> HttpResponse:
        pass

    def before_dispatch(self, request: HttpRequest):
        pass

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not request.user.stores.all():
            self.context = {'have_store': False}
            return self.render(request)
        self.nomenclature = iiko_api.get_nomenclature()
        self.before_dispatch(request)
        return super(DocumentView, self).dispatch(
            request, *args, **kwargs
        )

    def get(self, request: HttpRequest, *args, **kwargs):
        return self.render(request)

    def collect_items(self, request: HttpRequest):
        names = request.POST.getlist('products_names[]', [])
        amounts = request.POST.getlist('products_counts[]', [])
        if len(names) == 0 or len(amounts) == 0 or len(names) != len(amounts):
            self.context['error_message'] = \
                'Пожалуйста, заполните поля корректно!'
            return self.render(request)
        return zip(names, amounts)

    def create_items(self, request: HttpRequest, items: list[tuple]):
        created = []
        for name, amount in items:
            if not name or len(name) == 0 or not amount or float(amount) == 0:
                self.context['error_message'] = \
                    'Пожалуйста, заполните поля корректно!'
                return self.render(request)
            if name not in self.nomenclature['name']:
                self.context['error_message'] = \
                    'Пожалуйста, используйте предлагаемые наименования!'
                return self.render(request)
            created.append(self.item_model(
                product_id=self.nomenclature['name'].get(name),
                amount=float(amount)
            ))
        return created

    def create_document(self, request: HttpRequest, *args, **kwargs):
        document = self.model(*args, **kwargs)
        collected = self.collect_items(request)
        if isinstance(collected, HttpResponse):
            return collected
        created = self.create_items(request, collected)
        if isinstance(created, HttpResponse):
            return created
        document.save()
        for item in created:
            setattr(item, self.rel, document)
        self.item_model.objects.bulk_create(created)
        return document, created
