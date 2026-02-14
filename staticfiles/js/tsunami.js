/**
 * Tsunami alerts page — warning cards with zones + map + detail modal.
 */
const GempaTsunami = (() => {
    'use strict';

    const { fetchJSON, magBg, formatDatetime, parseCoords, tsunamiLevelColor, bmkgImageUrls, bmkgImageLabels } = GempaUtils;

    let infosCache = [];

    function showDetail(idx) {
        const info = infosCache[idx];
        if (!info) return;
        const modal = document.getElementById('detail-modal');
        const title = document.getElementById('detail-title');
        const content = document.getElementById('detail-content');
        title.textContent = `M ${info.magnitude} — ${info.area}`;

        const imgs = bmkgImageUrls(info.eventid);
        const imgGrid = imgs ? Object.entries(imgs).map(([key, url]) => `
            <div class="group cursor-pointer" onclick="document.getElementById('img-modal-src').src='${url}';document.getElementById('img-modal-title').textContent='${bmkgImageLabels[key]}';document.getElementById('img-modal').classList.remove('hidden')">
                <div class="relative overflow-hidden rounded-lg border border-gray-800 bg-gray-950 aspect-video">
                    <img src="${url}" alt="${bmkgImageLabels[key]}" loading="lazy"
                         class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                         onerror="this.parentElement.parentElement.style.display='none'">
                </div>
                <p class="text-[10px] text-gray-500 mt-1 text-center group-hover:text-gray-300 transition-colors">${bmkgImageLabels[key]}</p>
            </div>
        `).join('') : '<p class="text-gray-500 text-sm">Tidak ada gambar tersedia</p>';

        content.innerHTML = `
            <div class="grid grid-cols-3 gap-3 text-center mb-4">
                <div class="bg-gray-800/50 rounded-lg py-2">
                    <p class="text-[9px] text-gray-600 uppercase">Kedalaman</p>
                    <p class="text-xs font-semibold text-gray-300">${info.depth}</p>
                </div>
                <div class="bg-gray-800/50 rounded-lg py-2">
                    <p class="text-[9px] text-gray-600 uppercase">Waktu</p>
                    <p class="text-xs font-semibold text-gray-300">${formatDatetime(`${info.date}T${info.time}`)}</p>
                </div>
                <div class="bg-gray-800/50 rounded-lg py-2">
                    <p class="text-[9px] text-gray-600 uppercase">Koordinat</p>
                    <p class="text-xs font-semibold text-gray-300">${info.latitude}, ${info.longitude}</p>
                </div>
            </div>
            ${info.potential ? `
                <div class="mb-4 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <p class="text-xs text-amber-400 font-medium">${info.potential}</p>
                </div>
            ` : ''}
            <p class="text-[10px] text-gray-600 uppercase font-semibold mb-2">Analisis BMKG</p>
            <div class="grid grid-cols-2 gap-3">${imgGrid}</div>
        `;
        modal.classList.remove('hidden');
    }

    async function init() {
        const map = GempaMap.create('tsunami-map');

        try {
            const data = await fetchJSON('/api/tsunami/');
            const infos = data.info || [];
            infosCache = infos;

            const container = document.getElementById('tsunami-cards');
            const points = [];

            container.innerHTML = infos.map((info, i) => {
                const mag = info.magnitude ?? '?';
                const coords = parseCoords(info.point?.coordinates);

                if (coords) {
                    points.push(coords);
                    const tTime = info.date && info.time ? `${info.date}T${info.time}` : '';
                    GempaMap.addQuakeMarker(map, coords[0], coords[1], mag, `
                        <div style="font-family:system-ui;font-size:13px;color:#e5e7eb;">
                            <div style="font-weight:700;font-size:14px;color:#fff;">M ${mag} — Tsunami</div>
                            <div style="color:#9ca3af;font-size:11px;margin-top:2px;">${info.area || '—'}</div>
                            <div style="color:#9ca3af;font-size:11px;margin-top:2px;">${formatDatetime(tTime)}</div>
                            <div style="margin-top:6px;display:flex;gap:12px;font-size:12px;color:#d1d5db;">
                                <span>Kedalaman: <b>${info.depth || '?'}</b></span>
                            </div>
                            <div style="color:#6b7280;font-size:10px;margin-top:4px;">${info.latitude || '?'}, ${info.longitude || '?'}</div>
                            ${info.potential ? `<div style="color:#fbbf24;font-size:11px;margin-top:4px;">${info.potential}</div>` : ''}
                        </div>
                    `);
                }

                // Warning zone areas
                const wzAreas = (info.wzarea || []);
                const obsAreas = (info.obsarea || []);

                const wzHTML = wzAreas.length ? `
                    <div class="mt-4">
                        <p class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Zona Peringatan</p>
                        <div class="space-y-1.5">
                            ${wzAreas.map(wz => `
                                <div class="flex items-center justify-between px-3 py-2 rounded-lg border ${tsunamiLevelColor(wz.level)}">
                                    <div>
                                        <span class="text-xs font-semibold">${wz.district || '—'}</span>
                                        <span class="text-[10px] opacity-60 ml-1">${wz.province || ''}</span>
                                    </div>
                                    <span class="text-[10px] font-bold uppercase">${wz.level}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : '';

                const obsHTML = obsAreas.length ? `
                    <div class="mt-4">
                        <p class="text-[10px] text-gray-500 uppercase font-semibold mb-2">Observasi Tinggi Gelombang</p>
                        <div class="overflow-x-auto">
                            <table class="w-full text-xs">
                                <thead>
                                    <tr class="text-gray-600 border-b border-gray-800">
                                        <th class="px-2 py-1 text-left">Lokasi</th>
                                        <th class="px-2 py-1 text-center">Tinggi (m)</th>
                                        <th class="px-2 py-1 text-right">Waktu</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-800/40">
                                    ${obsAreas.map(obs => `
                                        <tr>
                                            <td class="px-2 py-1 text-gray-300">${obs.location}</td>
                                            <td class="px-2 py-1 text-center font-semibold ${Number(obs.height) >= 0.1 ? 'text-amber-400' : 'text-gray-400'}">${obs.height} m</td>
                                            <td class="px-2 py-1 text-right text-gray-500">${obs.time}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ` : '';

                return `
                    <div class="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                        <!-- Header -->
                        <div class="px-5 py-4 border-b border-gray-800 flex items-start justify-between gap-3">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 mb-1">
                                    <svg class="w-4 h-4 text-amber-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                                    </svg>
                                    <span class="text-xs font-bold uppercase tracking-wider ${info.subject?.includes('PD-') ? 'text-red-400' : 'text-amber-400'}">
                                        ${info.subject || 'Peringatan Tsunami'}
                                    </span>
                                </div>
                                <h3 class="text-sm font-semibold text-white leading-tight">${info.area}</h3>
                                <p class="text-xs text-gray-500 mt-1">${formatDatetime(`${info.date}T${info.time}`)}</p>
                            </div>
                            <span class="shrink-0 inline-flex items-center px-2.5 py-1 rounded-full text-sm font-bold ${magBg(mag)}">
                                M ${mag}
                            </span>
                        </div>

                        <!-- Body -->
                        <div class="px-5 py-4">
                            <div class="grid grid-cols-3 gap-3 text-center mb-3">
                                <div class="bg-gray-800/50 rounded-lg py-2">
                                    <p class="text-[9px] text-gray-600 uppercase">Kedalaman</p>
                                    <p class="text-xs font-semibold text-gray-300">${info.depth}</p>
                                </div>
                                <div class="bg-gray-800/50 rounded-lg py-2">
                                    <p class="text-[9px] text-gray-600 uppercase">Lintang</p>
                                    <p class="text-xs font-semibold text-gray-300">${info.latitude}</p>
                                </div>
                                <div class="bg-gray-800/50 rounded-lg py-2">
                                    <p class="text-[9px] text-gray-600 uppercase">Bujur</p>
                                    <p class="text-xs font-semibold text-gray-300">${info.longitude}</p>
                                </div>
                            </div>

                            <p class="text-xs text-gray-400 leading-relaxed">${info.description || ''}</p>

                            ${info.potential ? `
                                <div class="mt-3 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                    <p class="text-xs text-amber-400 font-medium">${info.potential}</p>
                                </div>
                            ` : ''}

                            ${wzHTML}
                            ${obsHTML}

                            ${info.instruction ? `
                                <p class="mt-4 text-[11px] text-gray-500 leading-relaxed italic">${info.instruction}</p>
                            ` : ''}

                            <button onclick="GempaTsunami.showDetail(${i})"
                                    class="mt-4 w-full text-xs text-center py-2 rounded-lg border border-gray-700 text-emerald-400 hover:bg-gray-800 hover:border-emerald-500/30 transition-colors">
                                Detail & Analisis
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            if (points.length) GempaMap.fitToPoints(map, points);
            if (!infos.length) container.innerHTML = '<p class="text-gray-500 text-center py-12">Tidak ada peringatan tsunami aktif</p>';

        } catch (e) {
            document.getElementById('tsunami-cards').innerHTML =
                '<p class="text-red-400 text-center py-12">Gagal memuat data tsunami</p>';
            console.error('Tsunami:', e);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    return { showDetail };
})();
