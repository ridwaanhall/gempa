/**
 * Tsunami alerts page — warning cards with zones + map + detail/narasi modals.
 */
const GempaTsunami = (() => {
    'use strict';

    const {
        fetchJSON, magBg, formatDatetime, parseCoords, tsunamiLevelColor,
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
                <div class="mb-4 px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
                    <p class="text-xs text-amber-400 font-medium">${info.potential}</p>
                </div>
            ` : ''}
            <p class="text-[10px] text-zinc-500 uppercase font-semibold mb-3 tracking-wider">Analisis BMKG</p>
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
                        <p class="text-[10px] text-zinc-500 uppercase font-semibold mb-2 tracking-wider">Zona Peringatan</p>
                        <div class="space-y-1.5">
                            ${wzAreas.map(wz => `
                                <div class="flex items-center justify-between px-3 py-2 rounded-xl border ${tsunamiLevelColor(wz.level)}">
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
                        <p class="text-[10px] text-zinc-500 uppercase font-semibold mb-2 tracking-wider">Observasi Tinggi Gelombang</p>
                        <div class="overflow-x-auto">
                            <table class="w-full text-xs">
                                <thead>
                                    <tr class="text-zinc-600 border-b border-zinc-800">
                                        <th class="px-2 py-1 text-left">Lokasi</th>
                                        <th class="px-2 py-1 text-center">Tinggi (m)</th>
                                        <th class="px-2 py-1 text-right">Waktu</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-zinc-800/40">
                                    ${obsAreas.map(obs => `
                                        <tr>
                                            <td class="px-2 py-1 text-zinc-300">${obs.location}</td>
                                            <td class="px-2 py-1 text-center font-semibold ${Number(obs.height) >= 0.1 ? 'text-amber-400' : 'text-zinc-400'}">${obs.height} m</td>
                                            <td class="px-2 py-1 text-right text-zinc-500">${obs.time}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ` : '';

                return `
                    <div class="rounded-xl border border-zinc-700/50 transition-all duration-300 hover:border-zinc-700 overflow-hidden backdrop-blur-sm">
                        <!-- Header -->
                        <div class="px-5 py-4 border-b border-zinc-800 flex items-start justify-between gap-3">
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
                                <h3 class="text-sm font-semibold text-zinc-200 leading-tight">${info.area}</h3>
                                <p class="text-xs text-zinc-500 mt-1.5">${formatDatetime(`${info.date}T${info.time}`)}</p>
                            </div>
                            <span class="shrink-0 inline-flex items-center px-2.5 py-1 rounded-full text-sm font-bold ${magBg(mag)}">
                                M ${mag}
                            </span>
                        </div>

                        <!-- Body -->
                        <div class="px-5 py-4">
                            <div class="grid grid-cols-3 gap-3 text-center mb-4">
                                <div class="bg-zinc-800/30 rounded-lg py-2.5">
                                    <p class="text-[9px] text-zinc-500 uppercase font-medium">Kedalaman</p>
                                    <p class="text-xs font-semibold text-zinc-300 mt-0.5">${info.depth}</p>
                                </div>
                                <div class="bg-zinc-800/30 rounded-lg py-2.5">
                                    <p class="text-[9px] text-zinc-500 uppercase font-medium">Lintang</p>
                                    <p class="text-xs font-semibold text-zinc-300 mt-0.5">${info.latitude}</p>
                                </div>
                                <div class="bg-zinc-800/30 rounded-lg py-2.5">
                                    <p class="text-[9px] text-zinc-500 uppercase font-medium">Bujur</p>
                                    <p class="text-xs font-semibold text-zinc-300 mt-0.5">${info.longitude}</p>
                                </div>
                            </div>

                            <p class="text-xs text-zinc-400 leading-relaxed">${info.description || ''}</p>

                            ${info.potential ? `
                                <div class="mt-3 px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
                                    <p class="text-xs text-amber-400 font-medium">${info.potential}</p>
                                </div>
                            ` : ''}

                            ${wzHTML}
                            ${obsHTML}

                            ${info.instruction ? `
                                <div class="mt-4 px-3 py-2 rounded-xl bg-amber-500/8 border border-amber-500/15">
                                    <p class="text-[11px] text-amber-400/80 leading-relaxed italic">${info.instruction}</p>
                                </div>
                            ` : ''}

                            <div class="mt-4 flex gap-2">
                                <button onclick="GempaTsunami.showDetail(${i})"
                                        class="flex-1 text-xs text-center py-2.5 rounded-lg border border-zinc-700/50 text-indigo-400 hover:bg-indigo-500/5 hover:border-indigo-500/30 transition-all duration-200 font-medium">
                                    Detail & Analisis
                                </button>
                                <button onclick="GempaTsunami.showNarasi(${i})"
                                        class="flex-1 text-xs text-center py-2.5 rounded-lg border border-zinc-700/50 text-sky-400 hover:bg-sky-500/5 hover:border-sky-500/30 transition-all duration-200 font-medium">
                                    Narasi BMKG
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            if (points.length) GempaMap.fitToPoints(map, points);
            if (!infos.length) container.innerHTML = '<div class="flex flex-col items-center justify-center py-16"><svg class="w-12 h-12 text-zinc-700 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg><p class="text-zinc-500 text-sm">Tidak ada peringatan tsunami aktif</p></div>';

        } catch (e) {
            document.getElementById('tsunami-cards').innerHTML =
                '<div class="flex flex-col items-center justify-center py-16"><svg class="w-12 h-12 text-red-500/40 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg><p class="text-red-400 text-sm">Gagal memuat data tsunami</p></div>';
            console.error('Tsunami:', e);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    return { showDetail, showNarasi };
})();
