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

// Function to create custom numbered markers
function createNumberedMarker(number, isStart = false, isEnd = false) {
  let bgColor = '#0d6efd'; // Blue for normal stops
  if (isStart) bgColor = '#198754'; // Green for start
  if (isEnd) bgColor = '#dc3545'; // Red for end

  const svg = `
    <svg width="40" height="50" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="shadow">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.3"/>
        </filter>
      </defs>
      <path d="M 20 0 C 10 0, 2 8, 2 18 C 2 30, 20 50, 20 50 C 20 50, 38 30, 38 18 C 38 8, 30 0, 20 0 Z" 
            fill="${bgColor}" stroke="white" stroke-width="2" filter="url(#shadow)"/>
      <circle cx="20" cy="18" r="14" fill="white" stroke="${bgColor}" stroke-width="2"/>
      <text x="20" y="24" font-size="16" font-weight="bold" text-anchor="middle" fill="${bgColor}">${number}</text>
    </svg>
  `;

  const iconUrl = 'data:image/svg+xml;base64,' + btoa(svg);

  return L.icon({
    iconUrl: iconUrl,
    iconSize: [40, 50],
    iconAnchor: [20, 50],
    popupAnchor: [0, -50],
    className: 'custom-marker'
  });
}

// Shared stop icon for tour detail map
const stopIcon = createNumberedMarker(1);

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
    
    // Đếm số lượng stops để xác định start/end
    const allStops = data.features.filter(f => f.geometry.type === "Point");
    const stopCount = allStops.length;
    
    const geojsonLayer = L.geoJSON(data, {
      // Style cho LineString
      style: function (feature) {
        if (feature.properties.type === "route") {
          return {
            color: "#ff6b6b",
            weight: 4,
            opacity: 0.8,
            lineCap: 'round',
            lineJoin: 'round'
          };
        }
      },

      // BẮT BUỘC cho Point
      pointToLayer: function (feature, latlng) {
        const props = feature.properties || {};
        const order = props.order || 0;
        const isStart = (order === 1);
        const isEnd = (order === stopCount);
        
        const markerIcon = createNumberedMarker(order, isStart, isEnd);
        const marker = L.marker(latlng, { icon: markerIcon });
        
        // Thêm animation khi hover
        marker.on('mouseover', function() {
          this.setZIndexOffset(1000);
          this.getElement().style.filter = 'drop-shadow(0 0 8px rgba(13, 110, 253, 0.6))';
        });
        marker.on('mouseout', function() {
          this.setZIndexOffset(0);
          this.getElement().style.filter = 'drop-shadow(0 2px 3px rgba(0, 0, 0, 0.3))';
        });
        
        return marker;
      },

      // Popup
      onEachFeature: function (feature, layer) {
        if (feature.geometry.type === "Point") {
          const props = feature.properties || {};
          const title = props.name || 'Điểm dừng';
          const order = props.order ? props.order : '';
          const desc = props.description ? props.description : '';
          const img = props.image ? `<img src="${props.image}" alt="${title}" style="max-width:200px;max-height:150px;border-radius:8px;display:block;margin:8px 0;box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>` : '';
          const coords = (layer.getLatLng) ? layer.getLatLng() : (feature.geometry && feature.geometry.coordinates ? L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]) : null);
          const routeBtn = coords ? `<a href="#" class="start-route" data-lat="${coords.lat}" data-lng="${coords.lng}" style="display:inline-block;background:#0d6efd;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none;margin-top:8px;font-weight:500;transition:all 0.3s;">📍 Chỉ đường</a>` : '';
          
          const popupHtml = `
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 260px;">
              <div style="display:flex;align-items:center;margin-bottom:8px;">
                <span style="background:#0d6efd;color:white;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;margin-right:10px;">${order}</span>
                <h4 style="margin:0;color:#1e293b;font-size:1rem;">${title}</h4>
              </div>
              ${img}
              ${desc ? `<p style="margin:8px 0;color:#475569;font-size:0.9rem;line-height:1.4;">${desc}</p>` : ''}
              ${routeBtn}
            </div>
          `;
          
          layer.bindPopup(popupHtml, { maxWidth: 280, className: 'custom-popup' });
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

    // Cache point markers for radius filtering on detail map
    var stopMarkers = [];
    geojsonLayer.eachLayer(function(layer){
      try {
        if (layer.feature && layer.feature.geometry && layer.feature.geometry.type === 'Point') stopMarkers.push(layer);
      } catch(e) {}
    });

    // Add a compact radius control to allow filtering stops around user's location
    const RadiusControl = L.Control.extend({
      onAdd: function(map) {
        const container = L.DomUtil.create('div', 'leaflet-bar');
        container.style.background = 'white';
        container.style.padding = '6px';
        container.style.margin = '4px';
        container.style.minWidth = '160px';
        container.innerHTML = '<div style="display:flex;gap:6px;align-items:center;">'
          + '<input id="radius-km-input" type="number" min="0.1" step="0.1" placeholder="km" style="width:70px;padding:4px;font-size:12px">'
          + '<button id="apply-radius-btn" title="Lọc quanh vị trí của bạn" style="padding:4px 6px;font-size:12px">Lọc</button>'
          + '<button id="clear-radius-btn" title="Xóa bộ lọc" style="padding:4px 6px;margin-left:4px;font-size:12px">X</button>'
          + '</div>';
        L.DomEvent.disableClickPropagation(container);
        return container;
      }
    });
    map.addControl(new RadiusControl({ position: 'topright' }));

    // apply/clear handlers
    function applyRadius(centerLatLng, radiusKm) {
      var radiusMeters = parseFloat(radiusKm) * 1000;
      if (isNaN(radiusMeters) || radiusMeters <= 0) return;
      if (!stopMarkers || !stopMarkers.length) return;

      // hide all then re-add those within radius
      stopMarkers.forEach(function(m){ try { map.removeLayer(m); } catch(e) {} });
      var count = 0;
      stopMarkers.forEach(function(m){
        try {
          var d = map.distance(centerLatLng, m.getLatLng());
          if (d <= radiusMeters) { m.addTo(map); count++; }
        } catch(e) {}
      });

      // draw circle (keep single global circle for detail map)
      try { if (window._detailUserCircle) { map.removeLayer(window._detailUserCircle); window._detailUserCircle = null; } } catch(e) {}
      window._detailUserCircle = L.circle(centerLatLng, { radius: radiusMeters, color: '#0d6efd', fillOpacity: 0.06 }).addTo(map);

      if (count > 0) {
        try { var fg = L.featureGroup(stopMarkers.filter(function(m){ return map.hasLayer(m); })); if (fg && fg.getBounds && fg.getBounds().isValid()) map.fitBounds(fg.getBounds(), { padding: [20,20] }); } catch(e) {}
      } else {
        map.setView(centerLatLng, Math.max(map.getZoom(), 13));
      }
    }

    function clearRadius() {
      try { if (window._detailUserCircle) { map.removeLayer(window._detailUserCircle); window._detailUserCircle = null; } } catch(e) {}
      stopMarkers.forEach(function(m){ if (!map.hasLayer(m)) m.addTo(map); });
      try { var fg = L.featureGroup(stopMarkers); if (fg && fg.getBounds && fg.getBounds().isValid()) map.fitBounds(fg.getBounds(), { padding: [20,20] }); } catch(e) {}
    }

    // attach event handlers (defer until control elements are in DOM)
    setTimeout(function(){
      var applyBtn = document.getElementById('apply-radius-btn');
      var clearBtn = document.getElementById('clear-radius-btn');
      var radiusInput = document.getElementById('radius-km-input');
      if (applyBtn) applyBtn.addEventListener('click', function(){
        var r = radiusInput ? parseFloat(radiusInput.value) : NaN;
        if (isNaN(r) || r <= 0) { alert('Nhập bán kính hợp lệ (km)'); return; }
        if (!navigator.geolocation) return alert('Trình duyệt không hỗ trợ định vị.');
        navigator.geolocation.getCurrentPosition(function(pos){ applyRadius(L.latLng(pos.coords.latitude, pos.coords.longitude), r); }, function(err){ alert('Không thể lấy vị trí hiện tại: ' + (err.message || err.code)); }, { enableHighAccuracy: true, timeout: 10000 });
      });
      if (clearBtn) clearBtn.addEventListener('click', function(){ clearRadius(); if (radiusInput) radiusInput.value = ''; });
    }, 200);
  });

  // Routing control and clear button for detail map
  let routeControl = null;
  let altRouteLayers = [];
   let altControl = null;
   let previousMapState = null; // saved map view/bounds to restore on cancel
  var lastRoutingPoints = null;
  var perturbationAttempted = false;
  function selectAlternative(viaLatLng) {
    if (!lastRoutingPoints || !viaLatLng) return;
    if (routeControl) { map.removeControl(routeControl); routeControl = null; }
              // Save previous map view (bounds/center/zoom) so we can restore when user cancels
              if (!previousMapState) {
                try { var b = map.getBounds && map.getBounds(); previousMapState = { bounds: (b && b.isValid && b.isValid()) ? b : null, center: map.getCenter && map.getCenter(), zoom: map.getZoom && map.getZoom() }; }
                catch(err) { previousMapState = { center: map.getCenter && map.getCenter(), zoom: map.getZoom && map.getZoom() }; }
              }

              if (routeControl) {
                map.removeControl(routeControl);
                routeControl = null;
              }
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
            // show alternative routes in the routing UI (we'll present them via control)
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
        // Restore previous map view if present
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
