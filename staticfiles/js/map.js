/**
 * Gempa Monitor — Leaflet map utilities.
 * Creates dark-themed maps with base layer switching, magnitude-scaled circle markers,
 * popups, sensor markers, fault lines, and layer-group helpers.
 */
const GempaMap = (() => {
    'use strict';

    const INDONESIA_CENTER = [-2.5, 118];
    const DEFAULT_ZOOM = 5;

    /** Available base tile layers. */
    function baseLayers() {
        const attr_osm = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>';
        const attr_carto = `${attr_osm} &copy; <a href="https://carto.com/">CARTO</a>`;
        return {
            'Dark': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: attr_carto, subdomains: 'abcd', maxZoom: 20,
            }),
            'Streets': L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: attr_osm, maxZoom: 19,
            }),
            'Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: '&copy; Esri, Maxar, Earthstar Geographics', maxZoom: 18,
            }),
            'Topo': L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                attribution: `${attr_osm} &copy; <a href="https://opentopomap.org">OpenTopoMap</a>`, maxZoom: 17,
            }),
            'Light': L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: attr_carto, subdomains: 'abcd', maxZoom: 20,
            }),
        };
    }

    /** Initialise a Leaflet map with dark tile default + base layer switcher. */
    function create(elementId, options = {}) {
        const bases = baseLayers();
        const defaultBase = bases['Dark'];

        const map = L.map(elementId, {
            center: options.center || INDONESIA_CENTER,
            zoom: options.zoom || DEFAULT_ZOOM,
            zoomControl: true,
            attributionControl: true,
            layers: [defaultBase],
            ...options,
        });

        // Add base-layer radio control (top-left)
        L.control.layers(bases, null, { collapsed: true, position: 'topleft' }).addTo(map);

        // Fix Leaflet rendering in hidden/resized containers
        setTimeout(() => map.invalidateSize(), 200);

        return map;
    }

    /** Calculate marker radius from magnitude (per-integer M1–M9+). */
    function magRadius(mag) {
        if (mag >= 9) return 18;
        if (mag >= 8) return 16;
        if (mag >= 7) return 14;
        if (mag >= 6) return 11;
        if (mag >= 5) return 9;
        if (mag >= 4) return 7;
        if (mag >= 3) return 5;
        if (mag >= 2) return 4;
        if (mag >= 1) return 3;
        return 2;
    }

    /** Strip trailing unit (Km, km, KM) from a depth value and return a clean number string. */
    function normalizeDepth(d) {
        if (d == null) return '?';
        const s = String(d).trim().replace(/\s*[Kk][Mm]\s*$/i, '');
        return s || '?';
    }

    /** Add a circle marker for an earthquake. Returns the marker. */
    function addQuakeMarker(map, lat, lon, mag, popupHTML, options = {}) {
        const color = GempaUtils.magHex(mag);
        const marker = L.circleMarker([lat, lon], {
            radius: magRadius(mag),
            fillColor: color,
            color: color,
            weight: 1,
            opacity: 0.8,
            fillOpacity: 0.5,
            ...options,
        }).addTo(map);

        if (popupHTML) {
            marker.bindPopup(popupHTML, {
                className: 'gempa-popup',
                maxWidth: 280,
            });
        }

        return marker;
    }

    /**
     * Add a seismic-sensor marker (Indo) — shows id, stakeholder, uptbmkg.
     */
    function addSensorMarkerIndo(layerGroup, lat, lon, data) {
        const size = 12;
        const icon = L.divIcon({
            className: '',
            iconSize: [size, size],
            iconAnchor: [size / 2, size / 2],
            html: `<svg width="${size}" height="${size}" viewBox="0 0 12 12">
                     <rect x="2" y="2" width="8" height="8" rx="1" fill="#38bdf8" fill-opacity="0.7" stroke="#0ea5e9" stroke-width="1"/>
                   </svg>`,
        });

        const id = data.id || '—';
        const stakeholder = data.stakeholder || '';
        const uptbmkg = data.uptbmkg || '';
        const popup = `
            <div style="font-family:system-ui;font-size:13px;color:#e5e7eb;">
                <div style="font-weight:700;font-size:14px;color:#38bdf8;">📡 ${id}</div>
                ${stakeholder ? `<div style="color:#d1d5db;font-size:12px;margin-top:2px;">${stakeholder}</div>` : ''}
                ${uptbmkg ? `<div style="color:#9ca3af;font-size:11px;margin-top:2px;">UPT BMKG: ${uptbmkg}</div>` : ''}
                <div style="color:#6b7280;font-size:10px;margin-top:4px;">
                    ${lat.toFixed(4)}, ${lon.toFixed(4)}
                </div>
            </div>`;

        const marker = L.marker([lat, lon], { icon })
            .bindPopup(popup, { className: 'gempa-popup', maxWidth: 280 });
        layerGroup.addLayer(marker);
        return marker;
    }

    /**
     * Add a seismic-sensor marker (Global) — shows id, description, net, sta.
     */
    function addSensorMarkerGlobal(layerGroup, lat, lon, data) {
        const size = 12;
        const icon = L.divIcon({
            className: '',
            iconSize: [size, size],
            iconAnchor: [size / 2, size / 2],
            html: `<svg width="${size}" height="${size}" viewBox="0 0 12 12">
                     <polygon points="6,1 11,11 1,11" fill="#818cf8" fill-opacity="0.7" stroke="#6366f1" stroke-width="1"/>
                   </svg>`,
        });

        const id = data.id || '—';
        const desc = data.description || '';
        const net = data.net || '';
        const sta = data.sta || '';
        const popup = `
            <div style="font-family:system-ui;font-size:13px;color:#e5e7eb;">
                <div style="font-weight:700;font-size:14px;color:#818cf8;">📡 ${sta || id}</div>
                ${desc ? `<div style="color:#d1d5db;font-size:12px;margin-top:2px;">${desc}</div>` : ''}
                <div style="color:#9ca3af;font-size:11px;margin-top:2px;">
                    ${net ? `Network: <b>${net}</b>` : ''}${net && sta ? ' · ' : ''}${sta ? `Station: <b>${sta}</b>` : ''}
                </div>
                <div style="color:#6b7280;font-size:10px;margin-top:4px;">
                    ${lat.toFixed(4)}, ${lon.toFixed(4)}
                </div>
            </div>`;

        const marker = L.marker([lat, lon], { icon })
            .bindPopup(popup, { className: 'gempa-popup', maxWidth: 300 });
        layerGroup.addLayer(marker);
        return marker;
    }

    /**
     * Add an earthquake marker to a layer group (instead of directly to map).
     */
    function addQuakeMarkerToLayer(layerGroup, lat, lon, mag, popupHTML, options = {}) {
        const color = GempaUtils.magHex(mag);
        const marker = L.circleMarker([lat, lon], {
            radius: magRadius(mag),
            fillColor: color,
            color: color,
            weight: 1,
            opacity: 0.8,
            fillOpacity: 0.5,
            ...options,
        });

        if (popupHTML) {
            marker.bindPopup(popupHTML, { className: 'gempa-popup', maxWidth: 280 });
        }

        layerGroup.addLayer(marker);
        return marker;
    }

    /**
     * Add fault / plate-boundary linestrings from GeoJSON features onto a layer group.
     */
    function addFaultLines(layerGroup, features, style = {}) {
        const defaultStyle = {
            color: '#f97316',
            weight: 1.5,
            opacity: 0.6,
            dashArray: '4 3',
            ...style,
        };

        features.forEach(f => {
            if (!f.geometry) return;
            try {
                const layer = L.geoJSON(f, { style: () => defaultStyle });
                layerGroup.addLayer(layer);
            } catch { /* skip malformed */ }
        });
    }

    /** Build a standard popup HTML string for an earthquake event. */
    function quakePopup(data) {
        const mag    = data.mag ?? data.magnitude ?? '?';
        const area   = data.area || data.place || '—';
        const depth  = normalizeDepth(data.depth);
        const time   = data.time || data.datetime || '';
        const magNum = parseFloat(mag) || 0;
        const hex    = GempaUtils.magHex(magNum);
        const timeStr = time ? GempaUtils.formatDatetime(time) : '';
        return `
            <div style="min-width:210px;font-family:system-ui,-apple-system,sans-serif;line-height:1.5;">
                <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(63,63,70,0.5);">
                    <div style="flex-shrink:0;padding:5px 10px;border-radius:8px;background:${hex}22;border:1px solid ${hex}55;">
                        <div style="font-weight:900;font-size:18px;letter-spacing:-0.5px;color:${hex};">M${Number(mag).toFixed(1)}</div>
                    </div>
                    <div style="padding-top:3px;min-width:0;">
                        <div style="font-weight:600;font-size:13px;color:#f4f4f5;line-height:1.35;">${area}</div>
                    </div>
                </div>
                <div style="display:grid;gap:5px;font-size:11.5px;">
                    ${timeStr ? `<div style="display:flex;gap:8px;"><span style="color:#71717a;min-width:64px;flex-shrink:0;">Waktu</span><span style="color:#e4e4e7;">${timeStr}</span></div>` : ''}
                    <div style="display:flex;gap:8px;"><span style="color:#71717a;min-width:64px;flex-shrink:0;">Kedalaman</span><span style="color:#e4e4e7;">${depth} km</span></div>
                </div>
            </div>`;
    }

    /**
     * Animated pulse marker — expanding outline rings, no fill.
     * Uses @keyframes gempa-ring-pulse defined in core.html <style> block.
     * Ideal for single-event maps where the location needs visual emphasis.
     */
    function addPulseMarker(map, lat, lon, mag, popupHTML) {
        const hex  = GempaUtils.magHex(mag);
        const r    = Math.max(12, magRadius(mag) * 2.4);
        const size = r * 2;
        const dot  = Math.max(5, Math.round(r * 0.38));

        const icon = L.divIcon({
            className:   '',
            iconSize:    [size, size],
            iconAnchor:  [r, r],
            popupAnchor: [0, -(r + 4)],
            html: `<div style="position:relative;width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center;">
                <div style="position:absolute;inset:0;border-radius:50%;border:2px solid ${hex};animation:gempa-ring-pulse 2s ease-out infinite;"></div>
                <div style="position:absolute;inset:0;border-radius:50%;border:1.5px solid ${hex};animation:gempa-ring-pulse 2s ease-out 0.8s infinite;"></div>
                <div style="width:${dot}px;height:${dot}px;border-radius:50%;border:2px solid ${hex};background:transparent;"></div>
            </div>`,
        });

        const marker = L.marker([lat, lon], { icon });
        if (popupHTML) {
            marker.bindPopup(popupHTML, { className: 'gempa-popup', maxWidth: 300 });
        }
        return marker.addTo(map);
    }

    /** Clear all layers except the tile layer. */
    function clearMarkers(map) {
        map.eachLayer(layer => {
            if (layer instanceof L.CircleMarker || layer instanceof L.Marker) {
                map.removeLayer(layer);
            }
        });
    }

    /** Fit map to an array of [lat, lon] points. */
    function fitToPoints(map, points) {
        if (!points.length) return;
        const bounds = L.latLngBounds(points.map(p => L.latLng(p[0], p[1])));
        map.fitBounds(bounds, { padding: [30, 30], maxZoom: 8 });
    }

    return {
        create, baseLayers,
        addPulseMarker, addQuakeMarker, addQuakeMarkerToLayer,
        addSensorMarkerIndo, addSensorMarkerGlobal,
        addFaultLines, quakePopup, clearMarkers, fitToPoints,
        magRadius, normalizeDepth,
    };
})();
