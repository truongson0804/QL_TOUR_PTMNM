from django.test.client import RequestFactory
from apps.tours.servers import TourMapAPI
from apps.tours.models.tours import Tour

rf = RequestFactory()
view = TourMapAPI.as_view()
for t in Tour.objects.all():
    req = rf.get(f'/tours/route-map/{t.id}', HTTP_HOST='localhost')
    resp = view(req, id=t.id)
    data = getattr(resp, 'data', None)
    features = data.get('features', []) if data else []
    print('Tour', t.id, t.title, '-> features', len(features))
    if features:
        print(' example:', features[0])
