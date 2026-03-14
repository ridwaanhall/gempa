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

        // ── Overlay layers ──────────────────────────────────────
        const layers = {
            seismicIndo:   L.layerGroup(),
            seismicGlobal: L.layerGroup(),
            faultsIndo:    L.layerGroup(),
            faultsGlobal:  L.layerGroup(),
        };

        // Default on: Sesar Indonesia
        layers.faultsIndo.addTo(map);

        // Overlay layer control (collapsed toggle, bottomright — avoids info card at topright)
        L.control.layers(null, {
            '📡 Sensor Indonesia': layers.seismicIndo,
            '📡 Sensor Global':    layers.seismicGlobal,
            '🟠 Sesar Indonesia':  layers.faultsIndo,
            '🟠 Sesar Global':     layers.faultsGlobal,
        }, { collapsed: true, position: 'bottomright' }).addTo(map);

        // Map legend (bottomleft)
        const legend = L.control({ position: 'bottomleft' });
        legend.onAdd = function () {
            const div = L.DomUtil.create('div');
            div.style.cssText = [
                'background:rgba(0,0,0,0.82)',
                'backdrop-filter:blur(8px)',
                '-webkit-backdrop-filter:blur(8px)',
                'border:1px solid rgba(63,63,70,0.6)',
                'border-radius:10px',
                'padding:10px 12px',
                'font-family:system-ui,-apple-system,sans-serif',
                'font-size:11px',
                'color:#d4d4d8',
                'min-width:148px',
                'pointer-events:none',
                'line-height:1.4',
            ].join(';');
            div.innerHTML = `
                <div style="font-weight:700;font-size:10px;color:#a1a1aa;text-transform:uppercase;letter-spacing:.07em;margin-bottom:8px;">Keterangan</div>
                <div style="display:flex;flex-direction:column;gap:6px;">
                    <div style="display:flex;align-items:center;gap:7px;">
                        <svg width="14" height="14" viewBox="0 0 12 12" style="flex-shrink:0;"><rect x="2" y="2" width="8" height="8" rx="1" fill="#38bdf8" fill-opacity="0.7" stroke="#0ea5e9" stroke-width="1"/></svg>
                        <span>Sensor Indonesia</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:7px;">
                        <svg width="14" height="14" viewBox="0 0 12 12" style="flex-shrink:0;"><polygon points="6,1 11,11 1,11" fill="#818cf8" fill-opacity="0.7" stroke="#6366f1" stroke-width="1"/></svg>
                        <span>Sensor Global</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:7px;">
                        <span style="display:inline-block;width:18px;height:2.5px;background:#fb923c;border-radius:2px;flex-shrink:0;"></span>
                        <span>Sesar Indonesia</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:7px;">
                        <span style="display:inline-block;width:18px;height:2.5px;background:#f97316;opacity:.8;border-radius:2px;flex-shrink:0;"></span>
                        <span>Sesar Global</span>
                    </div>
                </div>`;
            return div;
        };
        legend.addTo(map);

        // Fetch layer data concurrently
        await Promise.allSettled([
            fetchJSON('/api/seismic-indo/').then(data => {
                (data.features || []).forEach(f => {
                    const [lon, lat] = f.geometry?.coordinates || [];
                    if (lat == null || lon == null) return;
                    const p = f.properties || {};
                    GempaMap.addSensorMarkerIndo(layers.seismicIndo, lat, lon, {
                        id: p.id, stakeholder: p.stakeholder, uptbmkg: p.uptbmkg,
                    });
                });
            }).catch(e => console.error('Seismic Indo:', e)),

            fetchJSON('/api/seismic-global/').then(data => {
                (data.features || []).forEach(f => {
                    const [lon, lat] = f.geometry?.coordinates || [];
                    if (lat == null || lon == null) return;
                    const p = f.properties || {};
                    GempaMap.addSensorMarkerGlobal(layers.seismicGlobal, lat, lon, {
                        id: f.id, description: p.description, net: p.net, sta: p.sta,
                    });
                });
            }).catch(e => console.error('Seismic Global:', e)),

            fetchJSON('/api/faults-indo/').then(data => {
                GempaMap.addFaultLines(layers.faultsIndo, data.features || [], {
                    color: '#fb923c', weight: 2, opacity: 0.7,
                });
            }).catch(e => console.error('Faults Indo:', e)),

            fetchJSON('/api/faults-global/').then(data => {
                GempaMap.addFaultLines(layers.faultsGlobal, data.features || [], {
                    color: '#f97316', weight: 1.5, opacity: 0.5,
                });
            }).catch(e => console.error('Faults Global:', e)),
        ]);

    } catch (e) {
        setText('single-rt-area', 'Gagal memuat data');
        console.error('Single realtime:', e);
    }
})();
