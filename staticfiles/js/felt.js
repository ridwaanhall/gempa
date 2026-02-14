/**
 * Felt earthquakes page — cards + map + detail/narasi modals.
 */
const GempaFelt = (() => {
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
            ${info.felt ? `<p class="text-xs text-gray-400 mb-4"><span class="text-gray-600">Dirasakan:</span> ${info.felt}</p>` : ''}
            <p class="text-[10px] text-gray-600 uppercase font-semibold mb-2">Analisis BMKG</p>
            <div class="grid grid-cols-2 gap-3">${bmkgImageGrid(info.eventid)}</div>
        `;
        modal.classList.remove('hidden');
    }

    function showNarasi(idx) {
        const info = infosCache[idx];
        if (!info) return;
        showNarasiModal(info.eventid, 'narasi-modal', 'narasi-title', 'narasi-content');
    }

    async function init() {
        const map = GempaMap.create('felt-map');

        try {
            const data = await fetchJSON('/api/felt/');
            const infos = data.info || [];
            infosCache = infos;

            const container = document.getElementById('felt-cards');
            const points = [];

            container.innerHTML = infos.map((info, i) => {
                const mag = info.magnitude ?? '?';
                const coords = parseCoords(info.point?.coordinates);

                if (coords) {
                    points.push(coords);
                    GempaMap.addQuakeMarker(map, coords[0], coords[1], mag,
                        GempaMap.quakePopup({ mag, area: info.area, depth: info.depth, time: `${info.date}T${info.time}` }));
                }

                const feltBadges = (info.felt || '').split(',')
                    .map(s => s.trim())
                    .filter(Boolean)
                    .slice(0, 5)
                    .map(s => `<span class="inline-block px-2 py-0.5 rounded-full text-[10px] bg-gray-800 text-gray-400">${s}</span>`)
                    .join(' ');

                return `
                    <div class="bg-gray-900 rounded-xl border border-gray-800 p-5 hover:border-gray-700 transition-colors">
                        <div class="flex items-start justify-between gap-3 mb-3">
                            <div class="flex-1 min-w-0">
                                <h3 class="font-semibold text-white text-sm leading-tight">${info.area}</h3>
                                <p class="text-xs text-gray-500 mt-1">${formatDatetime(`${info.date}T${info.time}`)}</p>
                            </div>
                            <span class="shrink-0 inline-flex items-center px-2.5 py-1 rounded-full text-sm font-bold ${magBg(mag)}">
                                M ${mag}
                            </span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 mb-3 text-center">
                            <div class="bg-gray-800/50 rounded-lg py-1.5">
                                <p class="text-[9px] text-gray-600 uppercase">Kedalaman</p>
                                <p class="text-xs font-semibold text-gray-300">${info.depth}</p>
                            </div>
                            <div class="bg-gray-800/50 rounded-lg py-1.5">
                                <p class="text-[9px] text-gray-600 uppercase">Lintang</p>
                                <p class="text-xs font-semibold text-gray-300">${info.latitude}</p>
                            </div>
                            <div class="bg-gray-800/50 rounded-lg py-1.5">
                                <p class="text-[9px] text-gray-600 uppercase">Bujur</p>
                                <p class="text-xs font-semibold text-gray-300">${info.longitude}</p>
                            </div>
                        </div>
                        ${feltBadges ? `
                            <div class="mb-3">
                                <p class="text-[10px] text-gray-600 uppercase mb-1.5">Dirasakan di</p>
                                <div class="flex flex-wrap gap-1">${feltBadges}</div>
                            </div>
                        ` : ''}
                        ${info.instruction ? `
                            <p class="mb-3 text-[11px] text-amber-400/80 leading-relaxed">
                                ⚠ ${info.instruction}
                            </p>
                        ` : ''}
                        <div class="flex gap-2">
                            <button onclick="GempaFelt.showDetail(${i})"
                                    class="flex-1 text-xs text-center py-2 rounded-lg border border-gray-700 text-emerald-400 hover:bg-gray-800 hover:border-emerald-500/30 transition-colors">
                                Detail & Analisis
                            </button>
                            <button onclick="GempaFelt.showNarasi(${i})"
                                    class="flex-1 text-xs text-center py-2 rounded-lg border border-gray-700 text-sky-400 hover:bg-gray-800 hover:border-sky-500/30 transition-colors">
                                Narasi BMKG
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            if (points.length) GempaMap.fitToPoints(map, points);
            if (!infos.length) container.innerHTML = '<p class="text-gray-500 col-span-full text-center py-12">Tidak ada data</p>';

        } catch (e) {
            document.getElementById('felt-cards').innerHTML =
                '<p class="text-red-400 col-span-full text-center py-12">Gagal memuat data gempa dirasakan</p>';
            console.error('Felt:', e);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    return { showDetail, showNarasi };
})();
