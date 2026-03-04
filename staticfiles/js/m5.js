/**
 * M5+ earthquakes page — significant earthquake cards + map + detail/narasi modals.
 */
const GempaM5 = (() => {
    'use strict';

    const {
        fetchJSON, magBg, magColor, formatDatetime, parseCoords,
        bmkgImageGrid, showNarasiModal, hideModal, detailInfoRow,
    } = GempaUtils;

    let infosCache = [];

    function showDetail(idx) {
        const info = infosCache[idx];
        if (!info) return;
        const modal = document.getElementById('detail-modal');
        const title = document.getElementById('detail-title');
        const content = document.getElementById('detail-content');
        title.textContent = `M ${info.magnitude} — ${info.area}`;

        content.innerHTML = `
            ${detailInfoRow(info.depth, `${info.date}T${info.time}`, info.latitude, info.longitude)}
            ${info.potential ? `
                <div class="mb-4 px-3 py-2 rounded-xl ${info.potential.toLowerCase().includes('tidak') ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-red-500/10 border border-red-500/20'}">
                    <p class="text-xs font-medium ${info.potential.toLowerCase().includes('tidak') ? 'text-emerald-400' : 'text-red-400'}">${info.potential}</p>
                </div>
            ` : ''}
            <p class="text-[10px] text-zinc-500 uppercase font-semibold mb-3 tracking-wider">Analisis BMKG</p>
            <div class="grid grid-cols-2 gap-3">${bmkgImageGrid(info.eventid)}</div>
        `;
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function showNarasi(idx) {
        const info = infosCache[idx];
        if (!info) return;
        showNarasiModal(info.eventid, 'narasi-modal', 'narasi-title', 'narasi-content');
    }

    async function init() {
        const map = GempaMap.create('m5-map');

        try {
            const data = await fetchJSON('/api/m5/');
            const infos = data.info || [];
            infosCache = infos;

            const container = document.getElementById('m5-cards');
            const points = [];

            container.innerHTML = infos.map((info, i) => {
                const mag = info.magnitude ?? '?';
                const coords = parseCoords(info.point?.coordinates);

                if (coords) {
                    points.push(coords);
                    GempaMap.addQuakeMarker(map, coords[0], coords[1], mag,
                        GempaMap.quakePopup({ mag, area: info.area, depth: info.depth, time: `${info.date}T${info.time}` }));
                }

                return `
                    <div class="rounded-xl border border-zinc-700/50 transition-all duration-300 hover:border-zinc-700 overflow-hidden backdrop-blur-sm p-5">
                        <div class="flex items-start justify-between gap-3 mb-4">
                            <div class="flex-1 min-w-0">
                                <h3 class="font-semibold text-zinc-200 text-sm leading-tight">${info.area}</h3>
                                <p class="text-xs text-zinc-500 mt-1.5">${formatDatetime(`${info.date}T${info.time}`)}</p>
                            </div>
                            <span class="shrink-0 inline-flex items-center px-2.5 py-1 rounded-full text-sm font-bold ${magBg(mag)}">
                                M ${mag}
                            </span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 mb-4 text-center">
                            <div class="bg-zinc-800/30 rounded-lg py-2">
                                <p class="text-[9px] text-zinc-500 uppercase font-medium">Kedalaman</p>
                                <p class="text-xs font-semibold text-zinc-300 mt-0.5">${info.depth}</p>
                            </div>
                            <div class="bg-zinc-800/30 rounded-lg py-2">
                                <p class="text-[9px] text-zinc-500 uppercase font-medium">Lintang</p>
                                <p class="text-xs font-semibold text-zinc-300 mt-0.5">${info.latitude}</p>
                            </div>
                            <div class="bg-zinc-800/30 rounded-lg py-2">
                                <p class="text-[9px] text-zinc-500 uppercase font-medium">Bujur</p>
                                <p class="text-xs font-semibold text-zinc-300 mt-0.5">${info.longitude}</p>
                            </div>
                        </div>
                        ${info.potential ? `
                            <div class="mb-4 px-3 py-2 rounded-xl ${info.potential.toLowerCase().includes('tsunami') ? 'bg-red-500/10 border border-red-500/20' : 'bg-emerald-500/10 border border-emerald-500/20'}">
                                <p class="text-xs font-medium ${info.potential.toLowerCase().includes('tidak') ? 'text-emerald-400' : 'text-red-400'}">${info.potential}</p>
                            </div>
                        ` : ''}
                        ${info.instruction ? `
                            <div class="mb-4 px-3 py-2 rounded-xl bg-amber-500/8 border border-amber-500/15">
                                <p class="text-[11px] text-amber-400/80 leading-relaxed">⚠ ${info.instruction}</p>
                            </div>
                        ` : ''}
                        <div class="flex gap-2">
                            <button onclick="GempaM5.showDetail(${i})"
                                    class="flex-1 text-xs text-center py-2.5 rounded-lg border border-zinc-700/50 text-indigo-400 hover:bg-indigo-500/5 hover:border-indigo-500/30 transition-all duration-200 font-medium">
                                Detail & Analisis
                            </button>
                            <button onclick="GempaM5.showNarasi(${i})"
                                    class="flex-1 text-xs text-center py-2.5 rounded-lg border border-zinc-700/50 text-sky-400 hover:bg-sky-500/5 hover:border-sky-500/30 transition-all duration-200 font-medium">
                                Narasi BMKG
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            if (points.length) GempaMap.fitToPoints(map, points);
            if (!infos.length) container.innerHTML = '<div class="col-span-full flex flex-col items-center justify-center py-16"><svg class="w-12 h-12 text-zinc-700 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/></svg><p class="text-zinc-500 text-sm">Tidak ada data gempa M5+</p></div>';

        } catch (e) {
            document.getElementById('m5-cards').innerHTML =
                '<div class="col-span-full flex flex-col items-center justify-center py-16"><svg class="w-12 h-12 text-red-500/40 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg><p class="text-red-400 text-sm">Gagal memuat data gempa M5+</p></div>';
            console.error('M5:', e);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    return { showDetail, showNarasi };
})();
