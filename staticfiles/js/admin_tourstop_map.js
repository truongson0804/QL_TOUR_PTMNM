document.addEventListener('DOMContentLoaded', function () {
  const latEl = document.getElementById('id_lat_input');
  const lonEl = document.getElementById('id_lon_input');

  // Parse existing coordinates if present
  const latVal = latEl ? parseFloat(latEl.value) : NaN;
  const lonVal = lonEl ? parseFloat(lonEl.value) : NaN;
  const hasCoords = !isNaN(latVal) && !isNaN(lonVal);

  const defaultCenter = hasCoords ? [latVal, lonVal] : [21.0285, 105.8542];
  const defaultZoom = hasCoords ? 13 : 6;

  // Create map
  const map = L.map('admin-map').setView(defaultCenter, defaultZoom);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  let marker = null;
  function setMarker(latlng) {
    if (!marker) {
      marker = L.marker(latlng, { draggable: true }).addTo(map);
      marker.on('dragend', function () {
        const p = marker.getLatLng();
        if (latEl) latEl.value = p.lat.toFixed(6);
        if (lonEl) lonEl.value = p.lng.toFixed(6);
      });
    } else {
      marker.setLatLng(latlng);
    }
    if (latEl) latEl.value = latlng.lat.toFixed(6);
    if (lonEl) lonEl.value = latlng.lng.toFixed(6);
  }

  if (hasCoords) {
    setMarker([latVal, lonVal]);
    map.setView([latVal, lonVal], 13);
  }

  map.on('click', function (e) {
    setMarker(e.latlng);
  });
  
  // Update marker when lat/lon inputs are changed manually
  function updateMarkerFromInputs() {
    if (!latEl || !lonEl) return;
    const lat = parseFloat(latEl.value);
    const lon = parseFloat(lonEl.value);
    if (!isNaN(lat) && !isNaN(lon)) {
      const latlng = { lat: lat, lng: lon };
      if (marker) {
        marker.setLatLng(latlng);
      } else {
        setMarker(latlng);
      }
      // center map a bit closer to the marker when user inputs coordinates
      try {
        map.setView(latlng, Math.max(map.getZoom(), 13));
      } catch (e) {}
    }
  }

  ['change', 'blur'].forEach(function (ev) {
    if (latEl) latEl.addEventListener(ev, updateMarkerFromInputs);
    if (lonEl) lonEl.addEventListener(ev, updateMarkerFromInputs);
  });
  // Ensure geocoder is loaded then attach search control.
  function ensureGeocoderLoaded(cb) {
    if (typeof L.Control.Geocoder !== 'undefined' || typeof L.Control.geocoder !== 'undefined') {
      return cb();
    }
    // Inject CSS if missing
    if (!document.querySelector('link[href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css"]')) {
      const l = document.createElement('link');
      l.rel = 'stylesheet';
      l.href = 'https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css';
      document.head.appendChild(l);
    }
    const s = document.createElement('script');
    s.src = 'https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js';
    s.async = true;
    s.onload = function () {
      cb();
    };
    document.head.appendChild(s);
  }

  ensureGeocoderLoaded(function () {
    if (typeof L.Control.geocoder === 'undefined' && typeof L.Control.Geocoder === 'undefined') return;
    const geocoder = L.Control.geocoder({
      defaultMarkGeocode: false,
      placeholder: 'Tìm kiếm địa chỉ...'
    }).addTo(map);

    geocoder.on('markgeocode', function (e) {
      const latlng = e.geocode.center;
      map.setView(latlng, 15);
      setMarker(latlng);
    });
  });
});
