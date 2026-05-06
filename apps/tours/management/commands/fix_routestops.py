from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Heuristically assign RouteStop.tour for RouteStop rows where tour is null'

    def handle(self, *args, **options):
        from apps.tours.models.route_stop import RouteStop
        from apps.tours.models.tours import Tour

        route_stops = RouteStop.objects.select_related('stop').filter(tour__isnull=True)
        tours = list(Tour.objects.all())

        if not route_stops.exists():
            self.stdout.write(self.style.SUCCESS('No unassigned RouteStop rows found.'))
            return

        def score_match(tour, stop_name):
            t = (tour.title or '').lower()
            s = (stop_name or '').lower()
            score = 0
            if s in t:
                score += 5
            # match words
            for w in s.split():
                if len(w) > 3 and w in t:
                    score += 1
            return score

        changed = 0
        for r in route_stops:
            stop = r.stop
            best = None
            best_score = 0
            for tour in tours:
                sc = score_match(tour, stop.name)
                if sc > best_score:
                    best_score = sc
                    best = tour

            if best and best_score > 0:
                r.tour = best
                r.save(update_fields=['tour'])
                changed += 1
                self.stdout.write(self.style.SUCCESS(f'Assigned RouteStop {r.id} -> Tour {best.id} (score {best_score})'))
            else:
                self.stdout.write(self.style.WARNING(f'No good match for RouteStop {r.id} stop="{stop.name}"'))

        self.stdout.write(self.style.SUCCESS(f'Done. Updated {changed} RouteStop rows.'))
