/**
 * Gempa Monitor — Leaflet map utilities.
 * Creates dark-themed maps, magnitude-scaled circle markers, and popups.
 */
const GempaMap = (() => {
    'use strict';

    const INDONESIA_CENTER = [-2.5, 118];
    const DEFAULT_ZOOM = 5;

    /** Initialise a Leaflet map with a dark tile layer. */
    function create(elementId, options = {}) {
        const map = L.map(elementId, {
            center: options.center || INDONESIA_CENTER,
            zoom: options.zoom || DEFAULT_ZOOM,
            zoomControl: true,
            attributionControl: true,
            ...options,
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 18,
        }).addTo(map);

        // Fix Leaflet rendering in hidden/resized containers
        setTimeout(() => map.invalidateSize(), 200);

        return map;
    }

    /** Calculate marker radius from magnitude. */
    function magRadius(mag) {
        if (mag >= 7) return 14;
        if (mag >= 6) return 11;
        if (mag >= 5) return 9;
        if (mag >= 4) return 7;
        if (mag >= 3) return 5;
        return 4;
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

    /** Build a standard popup HTML string for an earthquake event. */
    function quakePopup(data) {
        const mag = data.mag ?? data.magnitude ?? '?';
        const area = data.area || data.place || '—';
        const depth = data.depth ?? '?';
        const time = data.time || data.datetime || '';
        return `
            <div style="font-family:system-ui;font-size:13px;line-height:1.5;color:#e5e7eb;">
                <div style="font-weight:700;font-size:15px;color:#fff;margin-bottom:4px;">
                    M ${mag} — ${area}
                </div>
                <div style="color:#9ca3af;font-size:11px;">
                    ${GempaUtils.formatDatetime(time)}
                </div>
                <div style="margin-top:6px;display:flex;gap:12px;font-size:12px;color:#d1d5db;">
                    <span>Kedalaman: <b>${depth} km</b></span>
                </div>
            </div>
        `;
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

    return { create, addQuakeMarker, quakePopup, clearMarkers, fitToPoints, magRadius };
})();
