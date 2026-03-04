/**
 * Realtime earthquakes page — DataTable + map + history modal.
 */
const GempaApp = (() => {
    'use strict';

    const { fetchJSON, magBg, magColor, formatDatetime, datetimeSortKey, setHTML, dataTableLang } = GempaUtils;
    let rtMap;

    async function init() {
        rtMap = GempaMap.create('rt-map');

        try {
            const data = await fetchJSON('/api/realtime/');
            const events = data.events || [];

            document.getElementById('rt-count').textContent = `${events.length} event`;

            // Map markers
            const points = [];
            events.forEach(ev => {
                points.push([ev.latitude, ev.longitude]);
                GempaMap.addQuakeMarker(rtMap, ev.latitude, ev.longitude, ev.mag,
                    GempaMap.quakePopup({ mag: ev.mag, area: ev.area, depth: ev.depth, time: ev.datetime }));
            });
            if (points.length) GempaMap.fitToPoints(rtMap, points);

            // Populate table rows
            const tbody = document.getElementById('rt-tbody');
            tbody.innerHTML = events.map(ev => `
                <tr>
                    <td class="px-4 py-3 text-zinc-300 whitespace-nowrap" data-order="${datetimeSortKey(ev.datetime)}">${formatDatetime(ev.datetime)}</td>
                    <td class="px-4 py-3 text-zinc-200 max-w-xs truncate">${ev.area}</td>
                    <td class="px-4 py-3 text-center">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${magBg(ev.mag)}">${ev.mag}</span>
                    </td>
                    <td class="px-4 py-3 text-center text-zinc-400" data-order="${ev.depth}">${ev.depth} km</td>
                    <td class="px-4 py-3 text-center">
                        <span class="text-xs px-2 py-0.5 rounded-full ${ev.status === 'confirmed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-700 text-zinc-400'}">${ev.status}</span>
                    </td>
                    <td class="px-4 py-3 text-center">
                        <button onclick="GempaApp.showHistory('${ev.eventid}')"
                                class="text-xs text-indigo-400 hover:text-indigo-300 hover:underline transition-colors">
                            Riwayat
                        </button>
                    </td>
                </tr>
            `).join('');

            // Init DataTable
            $('#rt-table').DataTable({
                paging: true,
                pageLength: 15,
                ordering: true,
                order: [[0, 'desc']],
                info: true,
                searching: true,
                language: dataTableLang,
            });
        } catch (e) {
            document.getElementById('rt-tbody').innerHTML =
                '<tr><td colspan="6" class="px-4 py-12 text-center text-red-400">Gagal memuat data</td></tr>';
            console.error('Realtime:', e);
        }
    }

    async function showHistory(eventid) {
        GempaUtils.showModal('history-modal');
        document.getElementById('history-title').textContent = `Riwayat: ${eventid}`;
        setHTML('history-content', '<div class="flex justify-center py-8"><div class="animate-spin w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full"></div></div>');

        try {
            const data = await fetchJSON(`/api/realtime/${eventid}/history/`);
            const records = data.records || [];

            if (!records.length) {
                setHTML('history-content', '<p class="text-zinc-500 text-center py-8">Tidak ada data riwayat</p>');
                return;
            }

            setHTML('history-content', `
                <div class="overflow-x-auto">
                    <table class="w-full text-xs">
                        <thead>
                            <tr class="text-zinc-500 uppercase tracking-wider border-b border-zinc-800">
                                <th class="px-3 py-2 text-left">Waktu</th>
                                <th class="px-3 py-2 text-center">OT (min)</th>
                                <th class="px-3 py-2 text-center">Lat</th>
                                <th class="px-3 py-2 text-center">Lon</th>
                                <th class="px-3 py-2 text-center">Depth</th>
                                <th class="px-3 py-2 text-center">Mag</th>
                                <th class="px-3 py-2 text-center">Type</th>
                                <th class="px-3 py-2 text-center">Phase</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-zinc-800/40">
                            ${records.map(r => `
                                <tr class="hover:bg-zinc-800/40">
                                    <td class="px-3 py-2 text-zinc-300 whitespace-nowrap">${formatDatetime(r.timestamp)}</td>
                                    <td class="px-3 py-2 text-center text-zinc-400">${r.ot_minutes ?? '—'}</td>
                                    <td class="px-3 py-2 text-center text-zinc-400">${r.latitude ?? '—'}</td>
                                    <td class="px-3 py-2 text-center text-zinc-400">${r.longitude ?? '—'}</td>
                                    <td class="px-3 py-2 text-center text-zinc-400">${r.depth ?? '—'}</td>
                                    <td class="px-3 py-2 text-center ${r.magnitude ? magColor(r.magnitude) : 'text-zinc-600'} font-semibold">${r.magnitude ?? '—'}</td>
                                    <td class="px-3 py-2 text-center text-zinc-500">${r.mag_type || '—'}</td>
                                    <td class="px-3 py-2 text-center text-zinc-500">${r.phase_count ?? '—'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `);
        } catch (e) {
            setHTML('history-content', '<p class="text-red-400 text-center py-8">Gagal memuat riwayat</p>');
            console.error('History:', e);
        }
    }

    function closeModal() {
        GempaUtils.hideModal('history-modal');
    }

    document.addEventListener('DOMContentLoaded', init);
    return { showHistory, closeModal };
})();
