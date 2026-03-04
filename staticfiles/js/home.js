/**
 * Dashboard (home) page —
 *   • Latest earthquake hero card
 *   • Layer-controlled Leaflet map: mon3, yr5, seismic-indo, seismic-global, faults-indo, faults-global
 *   • Default layers on: faults-global + mon3
 */
(async function () {
    'use strict';

    const { fetchJSON, magColor, magBg, formatDatetime, setText, setHTML, parseCoords, bmkgImageUrls, bmkgImageLabels, showNarasiModal, hideModal } = GempaUtils;

    let latestEventId = null;
    let analisisSlides = [];
    let analisisIndex = 0;

    // ── Latest earthquake ───────────────────────────────────
    try {
        const data = await fetchJSON('/api/latest/');
        const info = data.info;
        const mag = info.magnitude;
        const coords = parseCoords(info.point?.coordinates);

        setText('latest-mag', mag);
        const magBadge = document.getElementById('latest-mag-badge');
        if (magBadge) magBadge.className = `shrink-0 w-16 h-16 rounded-2xl flex items-center justify-center ${magBg(mag).split(' ')[0]} backdrop-blur-sm`;
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

        // BMKG analysis images + narasi
        const eventid = info.eventid;
        if (eventid) {
            latestEventId = eventid;

            // Build slides array from BMKG image URLs
            const imgs = bmkgImageUrls(eventid);
            if (imgs) {
                analisisSlides = Object.entries(imgs).map(([key, url]) => ({
                    url,
                    label: bmkgImageLabels[key],
                }));
            }

            // Show buttons
            const narasiBtn = document.getElementById('latest-narasi-btn');
            if (narasiBtn) narasiBtn.classList.remove('hidden');
            const analisisBtn = document.getElementById('latest-analisis-btn');
            if (analisisBtn && analisisSlides.length) analisisBtn.classList.remove('hidden');
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

    // ── Narasi handler (exposed globally for onclick) ────
    window.showLatestNarasi = function () {
        if (latestEventId) {
            showNarasiModal(latestEventId, 'narasi-modal', 'narasi-title', 'narasi-content');
        }
    };

    // ── Analisis slider handlers ────────────────────────────
    function renderAnalisisSlide() {
        if (!analisisSlides.length) return;
        const slide = analisisSlides[analisisIndex];
        const img = document.getElementById('analisis-slide-img');
        const label = document.getElementById('analisis-slide-label');
        const noImg = document.getElementById('analisis-no-img');
        if (img) {
            img.style.display = '';
            img.src = slide.url;
            img.alt = slide.label;
        }
        if (noImg) noImg.classList.add('hidden');
        if (label) label.textContent = `${analisisIndex + 1} / ${analisisSlides.length} — ${slide.label}`;

        // Render dots
        const dots = document.getElementById('analisis-dots');
        if (dots) {
            dots.innerHTML = analisisSlides.map((_, i) =>
                `<button onclick="slideAnalisis(${i - analisisIndex})" class="w-2 h-2 rounded-full transition-colors duration-200 ${i === analisisIndex ? 'bg-indigo-400' : 'bg-zinc-600 hover:bg-zinc-500'}"></button>`
            ).join('');
        }
    }

    window.showLatestAnalisis = function () {
        if (!analisisSlides.length) return;
        analisisIndex = 0;
        renderAnalisisSlide();
        document.getElementById('analisis-modal').classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    };

    window.slideAnalisis = function (dir) {
        if (!analisisSlides.length) return;
        analisisIndex = (analisisIndex + dir + analisisSlides.length) % analisisSlides.length;
        renderAnalisisSlide();
    };

    // Keyboard navigation for analisis slider
    document.addEventListener('keydown', function (e) {
        const modal = document.getElementById('analisis-modal');
        if (!modal || modal.classList.contains('hidden')) return;
        if (e.key === 'ArrowLeft') slideAnalisis(-1);
        else if (e.key === 'ArrowRight') slideAnalisis(1);
        else if (e.key === 'Escape') {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    });
})();
