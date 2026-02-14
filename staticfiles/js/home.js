/**
 * Dashboard (home) page — shows latest earthquake + realtime overview.
 */
(async function () {
    'use strict';

    const { fetchJSON, magColor, magBg, formatDatetime, setText, setHTML, parseCoords } = GempaUtils;

    // ── Latest earthquake ───────────────────────────────────
    let latestMap;
    try {
        const data = await fetchJSON('/api/latest/');
        const info = data.info;
        const mag = info.magnitude;
        const coords = parseCoords(info.point?.coordinates);

        setText('latest-mag', mag);
        const magBadge = document.getElementById('latest-mag-badge');
        if (magBadge) magBadge.className = `shrink-0 w-16 h-16 rounded-2xl flex items-center justify-center ${magBg(mag).replace('text-', 'text-').split(' ')[0]}`;
        const magSpan = document.getElementById('latest-mag');
        if (magSpan) magSpan.className = `text-2xl font-black ${magColor(mag)}`;

        setText('latest-area', info.area);
        setText('latest-time', `${info.date} • ${info.time}`);
        setText('latest-depth', info.depth);
        setText('latest-coords', `${info.latitude}, ${info.longitude}`);
        setText('latest-potential', info.potential || '—');
        setText('latest-felt', info.felt || '—');

        const descEl = document.getElementById('latest-desc');
        if (descEl && info.description) {
            descEl.textContent = info.description;
            descEl.classList.remove('hidden');
        }

        // Map
        latestMap = GempaMap.create('latest-map', { zoom: 7 });
        if (coords) {
            latestMap.setView(coords, 8);
            GempaMap.addQuakeMarker(latestMap, coords[0], coords[1], mag,
                GempaMap.quakePopup({ mag, area: info.area, depth: info.depth, time: `${info.date}T${info.time}` }));
        }
    } catch (e) {
        setText('latest-area', 'Gagal memuat data');
        console.error('Latest:', e);
    }

    // ── Realtime events ─────────────────────────────────────
    try {
        const data = await fetchJSON('/api/realtime/');
        const events = data.events || [];

        // Stats
        setText('stat-total', events.length);
        if (events.length) {
            const mags = events.map(e => e.mag);
            const depths = events.map(e => e.depth);
            const avg = (mags.reduce((a, b) => a + b, 0) / mags.length).toFixed(1);
            setText('stat-avg-mag', avg);
            setText('stat-max-mag', Math.max(...mags).toFixed(1));
            setText('stat-max-depth', Math.max(...depths));
        }

        // Map markers
        const rtMap = GempaMap.create('realtime-map');
        const points = [];
        events.forEach(ev => {
            points.push([ev.latitude, ev.longitude]);
            GempaMap.addQuakeMarker(rtMap, ev.latitude, ev.longitude, ev.mag,
                GempaMap.quakePopup({ mag: ev.mag, area: ev.area, depth: ev.depth, time: ev.datetime }));
        });
        if (points.length) GempaMap.fitToPoints(rtMap, points);

        // Recent events list
        const container = document.getElementById('recent-events');
        if (container) {
            container.innerHTML = events.slice(0, 15).map(ev => `
                <div class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-gray-800/40 hover:bg-gray-800/70 transition-colors cursor-default">
                    <span class="shrink-0 w-10 h-10 rounded-lg ${magBg(ev.mag)} flex items-center justify-center text-sm font-bold">
                        ${ev.mag}
                    </span>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm text-gray-200 truncate">${ev.area}</p>
                        <p class="text-[11px] text-gray-600">${formatDatetime(ev.datetime)} · ${ev.depth} km</p>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        setHTML('recent-events', '<p class="text-sm text-red-400 text-center py-8">Gagal memuat data real-time</p>');
        console.error('Realtime:', e);
    }
})();
