from django.core.management.base import BaseCommand

from apps.tours.models.continent import Continent
from apps.tours.models.country import Country


ASEAN_COUNTRIES = [
    {"code": "BN", "name": "Brunei"},
    {"code": "KH", "name": "Campuchia"},
    {"code": "ID", "name": "Indonesia"},
    {"code": "LA", "name": "Lào"},
    {"code": "MY", "name": "Malaysia"},
    {"code": "MM", "name": "Myanmar"},
    {"code": "PH", "name": "Philippines"},
    {"code": "SG", "name": "Singapore"},
    {"code": "TH", "name": "Thái Lan"},
    {"code": "TL", "name": "Đông Timor"},
    {"code": "VN", "name": "Việt Nam"},
]


class Command(BaseCommand):
    help = "Load ASEAN countries (and create Asia continent)"

    def handle(self, *args, **options):
        continent, created = Continent.objects.update_or_create(
            code="AS", defaults={"name": "Châu Á"}
        )
        self.stdout.write(self.style.SUCCESS(f"Continent: {continent} (created={created})"))

        for item in ASEAN_COUNTRIES:
            country, c_created = Country.objects.update_or_create(
                code=item["code"], defaults={"name": item["name"], "continent": continent}
            )
            self.stdout.write(self.style.SUCCESS(f"Country: {country} (created={c_created})"))

        self.stdout.write(self.style.SUCCESS("ASEAN data import finished."))
