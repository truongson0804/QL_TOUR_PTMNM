from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class ToursConfig(AppConfig):
    name = 'apps.tours'
    
    def ready(self):
        """Signal handler to load initial data after migrations"""
        post_migrate.connect(load_initial_data, sender=self)


@receiver(post_migrate)
def load_initial_data(sender, **kwargs):
    """Automatically load ASEAN countries and continents after migrations"""
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
    
    # Chỉ chạy khi app là 'apps.tours'
    if sender.name != 'apps.tours':
        return
    
    # Kiểm tra xem đã có dữ liệu chưa
    if Continent.objects.exists():
        return  # Dữ liệu đã có, không cần thêm nữa
    
    try:
        # Tạo continent Châu Á
        continent, created = Continent.objects.get_or_create(
            code="AS", defaults={"name": "Châu Á"}
        )
        
        # Tạo các quốc gia ASEAN
        for item in ASEAN_COUNTRIES:
            Country.objects.get_or_create(
                code=item["code"],
                defaults={"name": item["name"], "continent": continent}
            )
        
        print("✅ ASEAN data loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading ASEAN data: {str(e)}")
