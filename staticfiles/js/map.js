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
            <div class="min-w-[180px] text-[13px] text-zinc-200">
                <div class="text-sm font-bold text-sky-400">📡 ${id}</div>
                ${stakeholder ? `<div class="mt-0.5 text-xs text-zinc-300">${stakeholder}</div>` : ''}
                ${uptbmkg ? `<div class="mt-0.5 text-[11px] text-zinc-400">UPT BMKG: ${uptbmkg}</div>` : ''}
                <div class="mt-1 text-[10px] text-zinc-500">${lat.toFixed(4)}, ${lon.toFixed(4)}</div>
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
            <div class="min-w-[190px] text-[13px] text-zinc-200">
                <div class="text-sm font-bold text-indigo-300">📡 ${sta || id}</div>
                ${desc ? `<div class="mt-0.5 text-xs text-zinc-300">${desc}</div>` : ''}
                <div class="mt-0.5 text-[11px] text-zinc-400">${net ? `Network: <b>${net}</b>` : ''}${net && sta ? ' · ' : ''}${sta ? `Station: <b>${sta}</b>` : ''}</div>
                <div class="mt-1 text-[10px] text-zinc-500">${lat.toFixed(4)}, ${lon.toFixed(4)}</div>
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
        const magClass = GempaUtils.magColor(magNum);
        const timeStr = time ? GempaUtils.formatDatetime(time) : '';
        return `
            <div class="min-w-[210px] leading-relaxed text-zinc-200">
                <div class="mb-2.5 flex items-start gap-2.5 border-b border-zinc-700 pb-2.5">
                    <div class="shrink-0 rounded-lg border border-zinc-700 bg-zinc-800 px-2.5 py-1">
                        <div class="text-lg font-black tracking-tight ${magClass}">M${Number(mag).toFixed(1)}</div>
                    </div>
                    <div class="min-w-0 pt-0.5 text-sm font-semibold text-zinc-100">${area}</div>
                </div>
                <div class="grid gap-1.5 text-[11px]">
                    ${timeStr ? `<div class="flex gap-2"><span class="min-w-16 shrink-0 text-zinc-400">Waktu</span><span class="text-zinc-200">${timeStr}</span></div>` : ''}
                    <div class="flex gap-2"><span class="min-w-16 shrink-0 text-zinc-400">Kedalaman</span><span class="text-zinc-200">${depth} km</span></div>
                </div>
            </div>`;
    }

    /**
     * Pulse-like marker using stacked circles (no custom CSS required).
     */
    function addPulseMarker(map, lat, lon, mag, popupHTML) {
        const hex  = GempaUtils.magHex(mag);
        const baseRadius = Math.max(8, magRadius(mag));
        const outer = L.circleMarker([lat, lon], {
            radius: baseRadius + 8,
            color: hex,
            weight: 1,
            opacity: 0.35,
            fillOpacity: 0,
        }).addTo(map);

        const middle = L.circleMarker([lat, lon], {
            radius: baseRadius + 4,
            color: hex,
            weight: 1,
            opacity: 0.55,
            fillOpacity: 0,
        }).addTo(map);

        const marker = L.circleMarker([lat, lon], {
            radius: baseRadius,
            fillColor: hex,
            color: hex,
            weight: 1.5,
            opacity: 0.9,
            fillOpacity: 0.35,
        }).addTo(map);

        if (popupHTML) {
            marker.bindPopup(popupHTML, { className: 'gempa-popup', maxWidth: 300 });
            outer.bindPopup(popupHTML, { className: 'gempa-popup', maxWidth: 300 });
            middle.bindPopup(popupHTML, { className: 'gempa-popup', maxWidth: 300 });
        }
        return marker;
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
