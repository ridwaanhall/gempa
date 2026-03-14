/**
 * Real-Time page (single) — shows the single latest earthquake from /api/realtime/.
 * Full-screen map with animated pulse marker and a floating info card overlay.
 * Time format: "15 Mar 2026, 02:06:28 WIB" (includes seconds).
 */
(async function () {
    'use strict';

    const { fetchJSON, magColor, magBg, magHex, setText } = GempaUtils;

    /** Format ISO datetime as "15 Mar 2026, 02:06:28 WIB" (UTC+7). */
    function formatDatetimeFull(iso) {
        if (!iso) return '—';
        try {
            const d = new Date(iso);
            if (isNaN(d)) return iso;
            const wib = new Date(d.getTime() + 7 * 3600000);
            const months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
            const day  = wib.getUTCDate();
            const mon  = months[wib.getUTCMonth()];
            const year = wib.getUTCFullYear();
            const hh   = String(wib.getUTCHours()).padStart(2, '0');
            const mm   = String(wib.getUTCMinutes()).padStart(2, '0');
            const ss   = String(wib.getUTCSeconds()).padStart(2, '0');
            return `${day} ${mon} ${year}, ${hh}:${mm}:${ss} WIB`;
        } catch { return iso; }
    }

    try {
        const data = await fetchJSON('/api/realtime/');
        const events = data.events || [];

        if (!events.length) {
            setText('single-rt-area', 'Tidak ada data gempa');
            return;
        }

        const ev  = events[0]; // Latest earthquake (first in list)
        const mag = parseFloat(ev.mag);
        const lat = parseFloat(ev.latitude);
        const lon = parseFloat(ev.longitude);
        const hex = magHex(mag);

        // Accent bar — magnitude colour
        const accentEl = document.getElementById('single-rt-accent');
        if (accentEl) accentEl.style.background = hex;

        // Magnitude badge
        const magBadge = document.getElementById('single-rt-mag-badge');
        if (magBadge) {
            const [bgClass] = magBg(mag).split(' ');
            magBadge.className = `shrink-0 rounded-xl flex items-center justify-center backdrop-blur-sm ${bgClass}`;
            magBadge.style.cssText = 'width:3.5rem;height:3.5rem;';
        }
        const magSpan = document.getElementById('single-rt-mag');
        if (magSpan) {
            magSpan.textContent  = isNaN(mag) ? (ev.mag ?? '—') : mag.toFixed(1);
            magSpan.className    = `font-black ${magColor(mag)}`;
            magSpan.style.fontSize = '1.4rem';
            magSpan.style.lineHeight = '1';
        }

        // Text fields
        setText('single-rt-area',    ev.area  || '—');
        setText('single-rt-time',    formatDatetimeFull(ev.datetime));
        setText('single-rt-depth',   ev.depth != null ? `${ev.depth} km` : '—');
        setText('single-rt-coords',  (!isNaN(lat) && !isNaN(lon)) ? `${lat.toFixed(2)}°, ${lon.toFixed(2)}°` : '—');
        setText('single-rt-fokal',   ev.fokal   || '—');
        setText('single-rt-eventid', ev.eventid || '—');

        // Status badge
        const statusEl = document.getElementById('single-rt-status');
        if (statusEl && ev.status) {
            statusEl.textContent = ev.status;
            const confirmed      = ev.status === 'confirmed';
            statusEl.className   = `inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                confirmed
                    ? 'bg-emerald-900/30 text-emerald-400 border-emerald-800/50'
                    : 'bg-amber-900/30 text-amber-400 border-amber-800/50'
            }`;
        }

        // Leaflet map — all 5 base tile layers (Dark/Streets/Satellite/Topo/Light)
        const map = GempaMap.create('single-rt-map', { zoom: 6 });
        if (!isNaN(lat) && !isNaN(lon)) {
            map.setView([lat, lon], 6);
            // Animated pulse marker: outline rings, no fill, CSS keyframe animation
            GempaMap.addPulseMarker(
                map, lat, lon, mag,
                GempaMap.quakePopup({ mag, area: ev.area, depth: ev.depth, datetime: ev.datetime })
            );
        }
    } catch (e) {
        setText('single-rt-area', 'Gagal memuat data');
        console.error('Single realtime:', e);
    }
})();
