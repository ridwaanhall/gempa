/**
 * Dashboard (home) page —
 *   • Latest earthquake hero card
 *   • Layer-controlled Leaflet map: mon3, yr5, seismic-indo, seismic-global, faults-indo, faults-global
 *   • Default layers on: faults-global + mon3
 */
(async function () {
    'use strict';

    const { fetchJSON, magColor, magBg, formatDatetime, setText, setHTML, parseCoords, bmkgImageUrls, bmkgImageLabels } = GempaUtils;

    // ── Latest earthquake ───────────────────────────────────
    try {
        const data = await fetchJSON('/api/latest/');
        const info = data.info;
        const mag = info.magnitude;
        const coords = parseCoords(info.point?.coordinates);

        setText('latest-mag', mag);
        const magBadge = document.getElementById('latest-mag-badge');
        if (magBadge) magBadge.className = `shrink-0 w-16 h-16 rounded-2xl flex items-center justify-center ${magBg(mag).split(' ')[0]}`;
        const magSpan = document.getElementById('latest-mag');
        if (magSpan) magSpan.className = `text-2xl font-black ${magColor(mag)}`;

        setText('latest-area', info.area);
        setText('latest-time', formatDatetime(`${info.date}T${info.time}`));
        setText('latest-depth', info.depth);
        setText('latest-coords', `${info.latitude}, ${info.longitude}`);
        setText('latest-potential', info.potential || '—');
        setText('latest-felt', info.felt || '—');

        const descEl = document.getElementById('latest-desc');
        if (descEl && info.description) {
            descEl.textContent = info.description;
            descEl.classList.remove('hidden');
        }

        // Latest map
        const latestMap = GempaMap.create('latest-map', { zoom: 7 });
        if (coords) {
            latestMap.setView(coords, 5);
            GempaMap.addQuakeMarker(latestMap, coords[0], coords[1], mag,
                GempaMap.quakePopup({ mag, area: info.area, depth: info.depth, time: `${info.date}T${info.time}` }));
        }

        // BMKG analysis images
        const eventid = info.eventid;
        if (eventid) {
            const imgs = bmkgImageUrls(eventid);
            const grid = document.getElementById('latest-images-grid');
            const container = document.getElementById('latest-images');
            if (grid && container) {
                grid.innerHTML = Object.entries(imgs).map(([key, url]) => `
                    <div class="group cursor-pointer" onclick="document.getElementById('img-modal-src').src='${url}';document.getElementById('img-modal-title').textContent='${bmkgImageLabels[key]}';document.getElementById('img-modal').classList.remove('hidden')">
                        <div class="relative overflow-hidden rounded-lg border border-gray-800 bg-gray-900 aspect-video">
                            <img src="${url}" alt="${bmkgImageLabels[key]}" loading="lazy"
                                 class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                                 onerror="this.parentElement.parentElement.style.display='none'">
                        </div>
                        <p class="text-[10px] text-gray-500 mt-1 text-center group-hover:text-gray-300 transition-colors">${bmkgImageLabels[key]}</p>
                    </div>
                `).join('');
                container.classList.remove('hidden');
            }
        }
    } catch (e) {
        setText('latest-area', 'Gagal memuat data');
        console.error('Latest:', e);
    }

    // ── Layer-controlled map ────────────────────────────────
    const layerMap = GempaMap.create('home-layer-map');

    // Create layer groups
    const layers = {
        mon3:          L.layerGroup(),
        yr5:           L.layerGroup(),
        seismicIndo:   L.layerGroup(),
        seismicGlobal: L.layerGroup(),
        faultsIndo:    L.layerGroup(),
        faultsGlobal:  L.layerGroup(),
    };

    // Default layers: faults-global + mon3
    layers.faultsGlobal.addTo(layerMap);
    layers.mon3.addTo(layerMap);

    // Layer control (overlay checkboxes)
    const overlays = {
        '🟢 Gempa 3 Bulan (Mon3)':  layers.mon3,
        '🔵 Gempa 5 Tahun (Yr5)':   layers.yr5,
        '📡 Sensor Indonesia':       layers.seismicIndo,
        '📡 Sensor Global':          layers.seismicGlobal,
        '🟠 Sesar Indonesia':        layers.faultsIndo,
        '🟠 Sesar Global':           layers.faultsGlobal,
    };
    L.control.layers(null, overlays, { collapsed: false, position: 'topright' }).addTo(layerMap);

    let loaded = 0;
    const total = 6;
    const statusEl = document.getElementById('layer-status');

    function tick(name) {
        loaded++;
        if (statusEl) statusEl.textContent = `${loaded}/${total} layer dimuat`;
    }

    /** Popup for GeoJSON earthquake feature (mon3/yr5). */
    function geoPopup(p) {
        const mag = p.mag ?? '?';
        const place = p.place || '—';
        const depth = p.depth != null ? Number(p.depth).toFixed(1) : '?';
        const time = p.time ? new Date(p.time).toISOString() : '';
        return `
            <div style="font-family:system-ui;font-size:13px;color:#e5e7eb;">
                <div style="font-weight:700;font-size:14px;color:#fff;">M ${Number(mag).toFixed(1)} — ${place}</div>
                <div style="color:#9ca3af;font-size:11px;">${GempaUtils.formatDatetime(time)}</div>
                <div style="color:#d1d5db;font-size:12px;margin-top:4px;">
                    Kedalaman: <b>${depth} km</b>
                </div>
            </div>`;
    }

    // ── Fetch all layers concurrently ───────────────────────
    const fetches = [
        // Mon3
        fetchJSON('/api/mon3/').then(data => {
            const features = data.features || [];
            setText('stat-mon3', features.length);
            features.forEach(f => {
                const [lon, lat, depth] = f.geometry?.coordinates || [];
                if (lat == null || lon == null) return;
                const p = f.properties || {};
                GempaMap.addQuakeMarkerToLayer(layers.mon3, lat, lon, p.mag ?? 3,
                    geoPopup(p));
            });
            tick('mon3');
        }).catch(e => { console.error('Mon3:', e); tick('mon3'); }),

        // Yr5
        fetchJSON('/api/yr5/').then(data => {
            const features = data.features || [];
            setText('stat-yr5', features.length);
            features.forEach(f => {
                const [lon, lat, depth] = f.geometry?.coordinates || [];
                if (lat == null || lon == null) return;
                const p = f.properties || {};
                GempaMap.addQuakeMarkerToLayer(layers.yr5, lat, lon, p.mag ?? 3,
                    geoPopup(p), { fillOpacity: 0.35, opacity: 0.6 });
            });
            tick('yr5');
        }).catch(e => { console.error('Yr5:', e); tick('yr5'); }),

        // Seismic Indonesia
        fetchJSON('/api/seismic-indo/').then(data => {
            const features = data.features || [];
            setText('stat-sensor-indo', features.length);
            features.forEach(f => {
                const [lon, lat] = f.geometry?.coordinates || [];
                if (lat == null || lon == null) return;
                const p = f.properties || {};
                GempaMap.addSensorMarkerIndo(layers.seismicIndo, lat, lon, {
                    id: p.id, stakeholder: p.stakeholder, uptbmkg: p.uptbmkg,
                });
            });
            tick('seismic-indo');
        }).catch(e => { console.error('Seismic Indo:', e); tick('seismic-indo'); }),

        // Seismic Global
        fetchJSON('/api/seismic-global/').then(data => {
            const features = data.features || [];
            setText('stat-sensor-global', features.length);
            features.forEach(f => {
                const [lon, lat] = f.geometry?.coordinates || [];
                if (lat == null || lon == null) return;
                const p = f.properties || {};
                GempaMap.addSensorMarkerGlobal(layers.seismicGlobal, lat, lon, {
                    id: f.id, description: p.description, net: p.net, sta: p.sta,
                });
            });
            tick('seismic-global');
        }).catch(e => { console.error('Seismic Global:', e); tick('seismic-global'); }),

        // Faults Indonesia
        fetchJSON('/api/faults-indo/').then(data => {
            const features = data.features || [];
            GempaMap.addFaultLines(layers.faultsIndo, features, {
                color: '#fb923c', weight: 2, opacity: 0.7,
            });
            tick('faults-indo');
        }).catch(e => { console.error('Faults Indo:', e); tick('faults-indo'); }),

        // Faults Global
        fetchJSON('/api/faults-global/').then(data => {
            const features = data.features || [];
            GempaMap.addFaultLines(layers.faultsGlobal, features, {
                color: '#f97316', weight: 1.5, opacity: 0.5,
            });
            tick('faults-global');
        }).catch(e => { console.error('Faults Global:', e); tick('faults-global'); }),
    ];

    await Promise.allSettled(fetches);
    if (statusEl) statusEl.textContent = `${loaded}/${total} layer dimuat ✓`;
})();
