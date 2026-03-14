/**
 * Real-Time page (single) — shows the single latest earthquake from /api/realtime/.
 * Displays magnitude, area, time, depth, coordinates, focal mechanism, event ID,
 * and a Leaflet map with multiple base tile layers.
 */
(async function () {
    'use strict';

    const { fetchJSON, magColor, magBg, formatDatetime, setText } = GempaUtils;

    try {
        const data = await fetchJSON('/api/realtime/');
        const events = data.events || [];

        if (!events.length) {
            setText('single-rt-area', 'Tidak ada data gempa');
            return;
        }

        const ev = events[0]; // Latest earthquake (first in list)
        const mag = parseFloat(ev.mag);
        const lat = parseFloat(ev.latitude);
        const lon = parseFloat(ev.longitude);

        // Magnitude badge coloring
        const magBadge = document.getElementById('single-rt-mag-badge');
        if (magBadge) {
            const bgClass = magBg(mag).split(' ')[0];
            magBadge.className = `shrink-0 rounded-xl flex items-center justify-center backdrop-blur-sm ${bgClass}`;
            magBadge.style.width = '4.5rem';
            magBadge.style.height = '4.5rem';
        }
        const magSpan = document.getElementById('single-rt-mag');
        if (magSpan) {
            magSpan.textContent = isNaN(mag) ? ev.mag : mag.toFixed(1);
            magSpan.className = `text-3xl font-black ${magColor(mag)}`;
        }

        // Text fields
        setText('single-rt-area', ev.area || '—');
        setText('single-rt-time', formatDatetime(ev.datetime));
        setText('single-rt-depth', ev.depth != null ? `${ev.depth} km` : '—');
        setText('single-rt-coords', (!isNaN(lat) && !isNaN(lon)) ? `${lat.toFixed(2)}, ${lon.toFixed(2)}` : '—');
        setText('single-rt-fokal', ev.fokal || '—');
        setText('single-rt-eventid', ev.eventid || '—');

        // Status badge
        const statusEl = document.getElementById('single-rt-status');
        if (statusEl && ev.status) {
            statusEl.textContent = ev.status;
            const isConfirmed = ev.status === 'confirmed';
            statusEl.className = `inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                isConfirmed
                    ? 'bg-emerald-900/30 text-emerald-400 border-emerald-800/50'
                    : 'bg-amber-900/30 text-amber-400 border-amber-800/50'
            }`;
        }

        // Leaflet map — GempaMap.create adds all base tile layers (Dark, Streets, Satellite, Topo, Light)
        const map = GempaMap.create('single-rt-map', { zoom: 6 });
        if (!isNaN(lat) && !isNaN(lon)) {
            map.setView([lat, lon], 6);
            GempaMap.addQuakeMarker(
                map, lat, lon, mag,
                GempaMap.quakePopup({ mag, area: ev.area, depth: ev.depth, datetime: ev.datetime })
            );
        }
    } catch (e) {
        setText('single-rt-area', 'Gagal memuat data');
        console.error('Single realtime:', e);
    }
})();
