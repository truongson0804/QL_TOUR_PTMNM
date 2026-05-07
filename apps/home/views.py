from typing import Any
from django.shortcuts import render
from django.views.generic import TemplateView
from ..tours.models.categories import Category
from ..tours.models.continent import Continent
from ..tours.models.country import Country
from apps.tours.models.tours import Tour


class Home(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['tours'] = Tour.objects.all()
        context['categories'] = Category.objects.all()
        context['countries'] = Country.objects.all()
        context['continents'] = Continent.objects.all()
        return context


class About(TemplateView):
    template_name = 'about.html'
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Show up to 8 active tours on the about page (most recent first)
        try:
            context['featured_tours'] = Tour.objects.filter(status='ACTIVE').order_by('-create_at')[:8]
        except Exception:
            # If the Tour model or field is misconfigured, fall back to empty queryset
            context['featured_tours'] = Tour.objects.all()[:8]
        return context


class Contact(TemplateView):
    template_name = 'contact.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context