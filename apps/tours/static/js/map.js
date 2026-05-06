const map = L.map("map").setView([10.76, 106.66], 10);

L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  subdomains: 'abcd',
  maxZoom: 19
}).addTo(map);

// Add geocoder/search control if plugin is available.
if (typeof L.Control.Geocoder !== 'undefined' || typeof L.Control.geocoder !== 'undefined') {
  L.Control.geocoder({
    defaultMarkGeocode: true,
    position: 'topright',
    placeholder: 'Tìm kiếm địa chỉ...'
  }).addTo(map);
}

// Shared stop icon for tour detail map
const stopIcon = L.icon({
  iconUrl: '/static/leaflet/images/marker-icon.png',
  iconRetinaUrl: '/static/leaflet/images/marker-icon-2x.png',
  shadowUrl: '/static/leaflet/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const pathSegments = window.location.pathname.split("/");
// Robustly extract the last numeric segment as tourId (handles trailing slash).
const numericSegments = pathSegments.filter((s) => /^\d+$/.test(s));
const tourId = numericSegments.length ? numericSegments[numericSegments.length - 1] : null;

if (!tourId) {
  console.error("Could not detect tourId from URL:", window.location.pathname);
}

fetch(`../route-map/${tourId}`)
  .then((res) => res.json())
  .then((data) => {
    console.log(data);
    const geojsonLayer = L.geoJSON(data, {
      // Style cho LineString
      style: function (feature) {
        if (feature.properties.type === "route") {
          return {
            color: "red",
            weight: 5,
            opacity: 0.7,
          };
        }
      },

      // BẮT BUỘC cho Point
      pointToLayer: function (feature, latlng) {
        return L.marker(latlng, { icon: stopIcon });
      },

      // Popup
      onEachFeature: function (feature, layer) {
        if (feature.geometry.type === "Point") {
          const props = feature.properties || {};
          const title = props.name || 'Stop';
          const order = props.order ? `<br>Order: ${props.order}` : '';
          const desc = props.description ? `<br>${props.description}` : '';
          const img = props.image ? `<div style="margin-top:6px"><img src="${props.image}" alt="${title}" style="max-width:160px;max-height:120px;border-radius:6px;display:block;margin-bottom:6px;"/></div>` : '';
          const coords = (layer.getLatLng) ? layer.getLatLng() : (feature.geometry && feature.geometry.coordinates ? L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]) : null);
          const routeBtn = coords ? `<div style="margin-top:6px"><a href="#" class="start-route" data-lat="${coords.lat}" data-lng="${coords.lng}" style="display:inline-block;background:#0b7dda;color:#fff;padding:6px 8px;border-radius:4px;text-decoration:none;">Chỉ đường</a></div>` : '';
          const popupHtml = `<b>${title}</b>${order}${desc}${img}${routeBtn}`;
          layer.bindPopup(popupHtml);
        }

        if (feature.geometry.type === "LineString") {
          const distanceKm = feature.properties.distance_km ?? 0;
          layer.bindPopup(`
            <b>${feature.properties.name}</b><br>
            Distance: ${Number(distanceKm).toFixed(2)} km
          `);
        }
      },
    }).addTo(map);

    const bounds = geojsonLayer.getBounds();
    if (bounds && bounds.isValid && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  });

  // Routing control and clear button for detail map
  let routeControl = null;
  let altRouteLayers = [];
  let altControl = null;
  let previousMapState = null; // store previous map view to restore on cancel
  var lastRoutingPoints = null;
  var perturbationAttempted = false;
  function selectAlternative(viaLatLng) {
    if (!lastRoutingPoints || !viaLatLng) return;
    if (routeControl) { map.removeControl(routeControl); routeControl = null; }
    if (altRouteLayers && altRouteLayers.length) { altRouteLayers.forEach(function(o){ if (o && o.layer) map.removeLayer(o.layer); else if (o) map.removeLayer(o); }); altRouteLayers = []; }
    if (altControl) { try{ map.removeControl(altControl); }catch(e){} altControl = null; }
    routeControl = L.Routing.control({
      waypoints: [ lastRoutingPoints.start, viaLatLng, lastRoutingPoints.dest ],
      router: L.Routing.osrmv1({ serviceUrl: 'https://router.project-osrm.org/route/v1', alternatives: false, geometries: 'geojson', steps: true }),
      lineOptions: { styles: [{ color: 'blue', opacity: 0.95, weight: 6 }] },
      showAlternatives: false,
      fitSelectedRoute: true,
      createMarker: function(i, wp) { if (i === 0) return L.marker(wp.latLng, { icon: L.icon({ iconUrl: '/static/leaflet/images/marker-icon.png', iconSize: [25,41], iconAnchor: [12,41] }) }); return L.marker(wp.latLng, { icon: stopIcon }); }
    }).addTo(map);
    routeControl.on('routesfound', function(e){ console.log('selected alternative route', e); });
  }

  const ClearControl = L.Control.extend({
    onAdd: function(map) {
      const container = L.DomUtil.create('div', 'leaflet-bar');
      container.style.background = 'white';
      container.style.padding = '2px';
      container.style.margin = '4px';
      container.innerHTML = '<a href="#" id="clear-route" title="Hủy chỉ đường" style="display:none;padding:6px;text-decoration:none;color:#333;">✖ Hủy</a>';
      return container;
    }
  });
  const clearControl = new ClearControl({ position: 'topright' });
  clearControl.addTo(map);

  // Handle click on directions button inside popup
  document.getElementById('map').addEventListener('click', function(e) {
    const target = e.target;
    if (target && target.classList && target.classList.contains('start-route')) {
      const lat = parseFloat(target.dataset.lat);
      const lng = parseFloat(target.dataset.lng);
      if (isNaN(lat) || isNaN(lng)) return alert('Toạ độ không hợp lệ');
      if (typeof L.Routing === 'undefined') return alert('Chức năng chỉ đường không khả dụng.');

      if (!navigator.geolocation) return alert('Trình duyệt không hỗ trợ định vị.');
      navigator.geolocation.getCurrentPosition(
        function(pos) {
          const start = L.latLng(pos.coords.latitude, pos.coords.longitude);
          const dest = L.latLng(lat, lng);

          // Save previous map view so we can restore when user cancels
          if (!previousMapState) {
            try { var b = map.getBounds && map.getBounds(); previousMapState = { bounds: (b && b.isValid && b.isValid()) ? b : null, center: map.getCenter && map.getCenter(), zoom: map.getZoom && map.getZoom() }; }
            catch(err) { previousMapState = { center: map.getCenter && map.getCenter(), zoom: map.getZoom && map.getZoom() }; }
          }

          if (routeControl) {
            map.removeControl(routeControl);
            routeControl = null;
          }
          if (altRouteLayers && altRouteLayers.length) { altRouteLayers.forEach(function(o){ if (o && o.layer) map.removeLayer(o.layer); else if (o) map.removeLayer(o); }); altRouteLayers = []; }

          lastRoutingPoints = { start: start, dest: dest };

          routeControl = L.Routing.control({
            waypoints: [start, dest],
            // Request alternatives from OSRM and display them (ask for geojson geometry + steps)
            router: L.Routing.osrmv1({ serviceUrl: 'https://router.project-osrm.org/route/v1', alternatives: true, geometries: 'geojson', steps: true }),
            lineOptions: { styles: [{ color: 'blue', opacity: 0.6, weight: 5 }] },
            fitSelectedRoute: true,
            // show alternative routes in the routing UI (we'll present alternatives via control)
            showAlternatives: false,
            createMarker: function(i, wp) {
              if (i === 0) {
                return L.marker(wp.latLng, { icon: L.icon({ iconUrl: '/static/leaflet/images/marker-icon.png', iconSize: [25,41], iconAnchor: [12,41] }) });
              }
              return L.marker(wp.latLng, { icon: stopIcon });
            }
          }).addTo(map);

          routeControl.on('routesfound', function(e){
            try {
              if (altRouteLayers && altRouteLayers.length) { altRouteLayers.forEach(function(o){ if (o && o.layer) map.removeLayer(o.layer); else if (o) map.removeLayer(o); }); altRouteLayers = []; }
              if (altControl) { try{ map.removeControl(altControl); }catch(e){} altControl = null; }
              var routes = e.routes || [];
              if (routes && routes.length > 1) {
                const AltControl = L.Control.extend({
                  onAdd: function(map) {
                    const container = L.DomUtil.create('div', 'leaflet-bar alt-routes-control');
                    container.style.background = 'white';
                    container.style.padding = '6px';
                    container.style.margin = '4px';
                    container.style.maxWidth = '220px';
                    container.style.maxHeight = '220px';
                    container.style.overflow = 'auto';
                    const title = document.createElement('div');
                    title.style.fontSize = '12px';
                    title.style.fontWeight = '600';
                    title.style.marginBottom = '6px';
                    title.textContent = 'Tùy chọn đường';
                    container.appendChild(title);
                    for (var i = 1; i < routes.length; i++) {
                      try {
                        (function(route, idx){
                          var coords = (route && route.geometry && route.geometry.coordinates) || [];
                          var viaLatLng = null;
                          if (coords && coords.length) {
                            var mid = coords[Math.floor(coords.length/2)];
                            viaLatLng = L.latLng(mid[1], mid[0]);
                          }
                          const btn = document.createElement('button');
                          btn.className = 'btn btn-sm btn-light';
                          btn.style.display = 'block';
                          btn.style.width = '100%';
                          btn.style.textAlign = 'left';
                          btn.style.marginBottom = '4px';
                          btn.textContent = 'Lựa chọn ' + (idx+1);
                          btn.addEventListener('click', function(){ if (viaLatLng) selectAlternative(viaLatLng); });
                          container.appendChild(btn);
                        })(routes[i], i);
                      } catch (err) { console.error('build alt UI err', err); }
                    }
                    return container;
                  }
                });
                altControl = new AltControl({ position: 'topright' });
                altControl.addTo(map);
              }
              if (!routes || routes.length <= 1) console.log('No alternatives returned from OSRM');
            } catch(err){ console.error(err); }
          });

          const clearBtn = document.getElementById('clear-route');
          if (clearBtn) clearBtn.style.display = 'inline-block';
        },
        function(err) {
          alert('Không thể lấy vị trí hiện tại: ' + (err.message || err.code));
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }
  });

  // Clear route button handler
  document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'clear-route') {
      e.preventDefault();
      if (routeControl) {
        map.removeControl(routeControl);
        routeControl = null;
      }
      if (altRouteLayers && altRouteLayers.length) { altRouteLayers.forEach(function(o){ if (o && o.layer) map.removeLayer(o.layer); else if (o) map.removeLayer(o); }); altRouteLayers = []; }
      if (altControl) { try{ map.removeControl(altControl); }catch(e){} altControl = null; }
      // Restore previous map view if available
      try {
        if (previousMapState) {
          if (previousMapState.bounds && previousMapState.bounds.isValid && previousMapState.bounds.isValid()) {
            try { map.fitBounds(previousMapState.bounds, { padding: [20, 20] }); }
            catch(e) { if (previousMapState.center && previousMapState.zoom) map.setView(previousMapState.center, previousMapState.zoom); }
          } else if (previousMapState.center && previousMapState.zoom) {
            map.setView(previousMapState.center, previousMapState.zoom);
          }
        }
      } catch(err) { console.error('restore previous view err', err); }
      previousMapState = null;
      const clearBtn = document.getElementById('clear-route');
      if (clearBtn) clearBtn.style.display = 'none';
    }
  });
