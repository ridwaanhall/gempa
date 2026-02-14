/**
 * Damage (gempa merusak) page — historical damaging earthquakes DataTable + map.
 */
(async function () {
    'use strict';

    const { fetchJSON, magBg, magColor, formatDatetime, datetimeSortKey, setText } = GempaUtils;

    const map = GempaMap.create('dmg-map');

    try {
        const data = await fetchJSON('/api/damage/');
        const features = data.features || [];

        // Stats
        setText('dmg-total', features.length);
        const tsunamiCount = features.filter(f => f.properties.tsunami).length;
        setText('dmg-tsunami', tsunamiCount);
        if (features.length) {
            const mags = features.map(f => f.properties.mag);
            setText('dmg-max', Math.max(...mags).toFixed(1));
            const dates = features.map(f => f.properties.date).sort();
            setText('dmg-period', `${dates[0]} — ${dates[dates.length - 1]}`);
        }

        // Map markers
        const points = [];
        features.forEach(f => {
            const [lon, lat] = f.geometry.coordinates;
            const p = f.properties;
            const iso = p.ot_utc ? `${p.date}T${p.ot_utc}Z` : p.date;
            points.push([lat, lon]);
            GempaMap.addQuakeMarker(map, lat, lon, p.mag, `
                <div style="font-family:system-ui;font-size:13px;color:#e5e7eb;">
                    <div style="font-weight:700;font-size:14px;color:#fff;">M ${p.mag}</div>
                    <div style="color:#9ca3af;font-size:11px;">${p.lokasi}</div>
                    <div style="color:#d1d5db;font-size:12px;margin-top:4px;">${p.pusat_gempa}</div>
                    <div style="color:#9ca3af;font-size:11px;margin-top:2px;">${formatDatetime(iso)}</div>
                    <div style="color:#d1d5db;font-size:12px;margin-top:4px;">Kedalaman: <b>${p.depth} km</b></div>
                    ${p.tsunami ? '<div style="color:#fbbf24;font-size:11px;margin-top:2px;">⚠ Tsunami</div>' : ''}
                </div>
            `);
        });
        if (points.length) GempaMap.fitToPoints(map, points);

        // Table rows
        const tbody = document.getElementById('dmg-tbody');
        tbody.innerHTML = features.map(f => {
            const p = f.properties;
            const iso = p.ot_utc ? `${p.date}T${p.ot_utc}Z` : p.date;
            const feltShort = (p.dirasakan || '').split(';').slice(0, 5).filter(Boolean).join('; ');
            return `
                <tr>
                    <td class="px-4 py-3 text-gray-300 whitespace-nowrap" data-order="${datetimeSortKey(iso)}">${formatDatetime(iso)}</td>
                    <td class="px-4 py-3 text-gray-200">
                        <div class="max-w-xs">
                            <p class="font-medium truncate">${p.lokasi}</p>
                            <p class="text-[11px] text-gray-500 truncate">${p.pusat_gempa}</p>
                        </div>
                    </td>
                    <td class="px-4 py-3 text-center">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${magBg(p.mag)}">${p.mag}</span>
                    </td>
                    <td class="px-4 py-3 text-center text-gray-400" data-order="${p.depth}">${p.depth} km</td>
                    <td class="px-4 py-3 text-center">
                        ${p.tsunami
                            ? '<span class="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400">Ya</span>'
                            : '<span class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-500">Tidak</span>'}
                    </td>
                    <td class="px-4 py-3 text-xs text-gray-500 max-w-[180px] truncate">${feltShort || '—'}</td>
                </tr>
            `;
        }).join('');

        // Init DataTable
        $('#dmg-table').DataTable({
            paging: true,
            pageLength: 15,
            ordering: true,
            order: [[0, 'desc']],
            info: true,
            searching: true,
            language: {
                search: 'Cari:',
                lengthMenu: 'Tampilkan _MENU_ data',
                info: '_START_–_END_ dari _TOTAL_',
                paginate: { previous: '‹', next: '›' },
                zeroRecords: 'Tidak ada data',
            },
        });

    } catch (e) {
        document.getElementById('dmg-tbody').innerHTML =
            '<tr><td colspan="6" class="px-4 py-12 text-center text-red-400">Gagal memuat data</td></tr>';
        console.error('Damage:', e);
    }
})();
