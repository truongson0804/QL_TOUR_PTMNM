from apps.tours.models.tours import Tour
from apps.tours.models.route_stop import RouteStop

han_tour = Tour.objects.filter(title__icontains='Hội An').first()
bana_tour = Tour.objects.filter(title__icontains='Bà Nà').first()
print('Hội An tour', getattr(han_tour,'id',None))
print('Bà Nà tour', getattr(bana_tour,'id',None))
if han_tour:
    updated = RouteStop.objects.filter(stop__name__icontains='Hội An', tour__isnull=True).update(tour=han_tour)
    print('Updated Hội An:', updated)
if bana_tour:
    updated = RouteStop.objects.filter(stop__name__icontains='Bà Nà', tour__isnull=True).update(tour=bana_tour)
    print('Updated Bà Nà:', updated)
print('done')
