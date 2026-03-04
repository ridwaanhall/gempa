/**
 * Gempa Monitor — shared utility functions.
 * Provides fetch wrappers, date formatting, magnitude color coding, and DOM helpers.
 */
const GempaUtils = (() => {
    'use strict';

    const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

    /**
     * Fetch JSON with sessionStorage caching.
     * Cached responses are reused within CACHE_TTL to avoid redundant network calls.
     */
    async function fetchJSON(url) {
        const cacheKey = `gempa_cache:${url}`;
        try {
            const cached = sessionStorage.getItem(cacheKey);
            if (cached) {
                const { ts, data } = JSON.parse(cached);
                if (Date.now() - ts < CACHE_TTL) return data;
            }
        } catch { /* ignore corrupt cache */ }

        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        try {
            sessionStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), data }));
        } catch { /* storage full — silently ignore */ }

        return data;
    }

    /** Return a Tailwind text-color class based on magnitude (per-integer M1–M9+). */
    function magColor(mag) {
        if (mag >= 9)   return 'text-fuchsia-400';
        if (mag >= 8)   return 'text-rose-500';
        if (mag >= 7)   return 'text-red-500';
        if (mag >= 6)   return 'text-red-400';
        if (mag >= 5)   return 'text-orange-400';
        if (mag >= 4)   return 'text-yellow-400';
        if (mag >= 3)   return 'text-green-400';
        if (mag >= 2)   return 'text-emerald-400';
        if (mag >= 1)   return 'text-teal-400';
        return 'text-zinc-400';
    }

    /** Return a Tailwind bg-color class for magnitude badges (per-integer M1–M9+). */
    function magBg(mag) {
        if (mag >= 9)   return 'bg-fuchsia-500/20 text-fuchsia-300';
        if (mag >= 8)   return 'bg-rose-500/20 text-rose-400';
        if (mag >= 7)   return 'bg-red-500/20 text-red-400';
        if (mag >= 6)   return 'bg-red-400/20 text-red-300';
        if (mag >= 5)   return 'bg-orange-400/20 text-orange-300';
        if (mag >= 4)   return 'bg-yellow-400/20 text-yellow-300';
        if (mag >= 3)   return 'bg-green-400/20 text-green-300';
        if (mag >= 2)   return 'bg-emerald-400/20 text-emerald-300';
        if (mag >= 1)   return 'bg-teal-400/20 text-teal-300';
        return 'bg-zinc-700/40 text-zinc-400';
    }

    /** Return a hex colour for Leaflet markers by magnitude (per-integer M1–M9+). */
    function magHex(mag) {
        if (mag >= 9)   return '#e879f9';  // fuchsia-400
        if (mag >= 8)   return '#f43f5e';  // rose-500
        if (mag >= 7)   return '#ef4444';  // red-500
        if (mag >= 6)   return '#f87171';  // red-400
        if (mag >= 5)   return '#fb923c';  // orange-400
        if (mag >= 4)   return '#facc15';  // yellow-400
        if (mag >= 3)   return '#4ade80';  // green-400
        if (mag >= 2)   return '#34d399';  // emerald-400
        if (mag >= 1)   return '#2dd4bf';  // teal-400
        return '#9ca3af';                  // gray-400
    }

    /** Format an ISO datetime string to "DD MMM YYYY HH:MM" in WIB (UTC+7). */
    function formatDatetime(iso) {
        if (!iso) return '—';
        try {
            const d = new Date(iso);
            if (isNaN(d)) return iso;
            const wib = new Date(d.getTime() + 7 * 60 * 60 * 1000);
            const months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
            const dd = String(wib.getUTCDate()).padStart(2, '0');
            const mm = months[wib.getUTCMonth()];
            const yy = wib.getUTCFullYear();
            const hh = String(wib.getUTCHours()).padStart(2, '0');
            const mi = String(wib.getUTCMinutes()).padStart(2, '0');
            return `${dd} ${mm} ${yy} ${hh}:${mi} WIB`;
        } catch {
            return iso;
        }
    }

    /** Short date: "DD/MM/YYYY" */
    function formatDate(dateStr) {
        if (!dateStr) return '—';
        try {
            const d = new Date(dateStr);
            if (isNaN(d)) return dateStr;
            return d.toLocaleDateString('id-ID', { day: '2-digit', month: '2-digit', year: 'numeric' });
        } catch {
            return dateStr;
        }
    }

    /**
     * Return a yyyymmddhhmmss numeric string suitable for DataTable sorting.
     * Converts the datetime to WIB (UTC+7) to match the display value.
     */
    function datetimeSortKey(iso) {
        if (!iso) return '0';
        try {
            const d = new Date(iso);
            if (isNaN(d)) return '0';
            const wib = new Date(d.getTime() + 7 * 60 * 60 * 1000);
            const yy = wib.getUTCFullYear();
            const mo = String(wib.getUTCMonth() + 1).padStart(2, '0');
            const dd = String(wib.getUTCDate()).padStart(2, '0');
            const hh = String(wib.getUTCHours()).padStart(2, '0');
            const mi = String(wib.getUTCMinutes()).padStart(2, '0');
            const ss = String(wib.getUTCSeconds()).padStart(2, '0');
            return `${yy}${mo}${dd}${hh}${mi}${ss}`;
        } catch {
            return '0';
        }
    }

    /** Set textContent on element by id. */
    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text ?? '—';
    }

    /** Set innerHTML on element by id. */
    function setHTML(id, html) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    }

    /** Parse coordinate string "lon,lat" → [lat, lon]. */
    function parseCoords(coordStr) {
        if (!coordStr) return null;
        const parts = coordStr.split(',').map(Number);
        if (parts.length < 2 || parts.some(isNaN)) return null;
        return [parts[1], parts[0]]; // [lat, lon]
    }

    /** Tsunami level → Tailwind color classes. */
    function tsunamiLevelColor(level) {
        const l = (level || '').toLowerCase();
        if (l.includes('awas'))    return 'bg-red-500/20 text-red-400 border-red-500/30';
        if (l.includes('siaga'))   return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
        if (l.includes('waspada')) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
        return 'bg-zinc-700/20 text-zinc-400 border-zinc-600';
    }

    /** Build BMKG image URLs for an event by its eventid. */
    const BMKG_STORAGE = 'https://bmkg-content-inatews.storage.googleapis.com';
    function bmkgImageUrls(eventid) {
        if (!eventid) return null;
        const base = `${BMKG_STORAGE}/${eventid}_rev`;
        return {
            locMap:       `${base}/loc_map.png`,
            stationMMI:   `${base}/stationlist_MMI.jpg`,
            impactList:   `${base}/impact_list.jpg`,
            intensityLogo:`${base}/intensity_logo.jpg`,
        };
    }

    /** Labels for each BMKG image type. */
    const bmkgImageLabels = {
        locMap:        'Sebaran Acelerometer',
        stationMMI:    'PGA Max & MMI',
        impactList:    'Dampak Kecamatan',
        intensityLogo: 'Intensitas',
    };

    /**
     * Build an HTML grid of BMKG analysis images with lightbox click handlers.
     * Returns HTML string for a 2-col grid, or a "not available" message.
     */
    function bmkgImageGrid(eventid) {
        const imgs = bmkgImageUrls(eventid);
        if (!imgs) return '<p class="text-zinc-500 text-sm">Tidak ada gambar tersedia</p>';
        return Object.entries(imgs).map(([key, url]) => `
            <div class="group cursor-pointer" onclick="document.getElementById('img-modal-src').src='${url}';document.getElementById('img-modal-title').textContent='${bmkgImageLabels[key]}';GempaUtils.showModal('img-modal')">
                <div class="relative overflow-hidden rounded-xl border border-zinc-800/60 bg-zinc-950 aspect-video">
                    <img src="${url}" alt="${bmkgImageLabels[key]}" loading="lazy"
                         class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                         onerror="this.parentElement.parentElement.style.display='none'">
                </div>
                <p class="text-[10px] text-zinc-500 mt-1 text-center group-hover:text-zinc-300 transition-colors">${bmkgImageLabels[key]}</p>
            </div>
        `).join('');
    }

    /**
     * Fetch BMKG narrative (press release) HTML for a given eventid.
     * Returns the HTML string on success, or null on failure.
     */
    async function fetchNarasi(eventid) {
        try {
            const res = await fetch(`${BMKG_STORAGE}/${eventid}_narasi.txt`);
            if (!res.ok) return null;
            const text = await res.text();
            return text || null;
        } catch {
            return null;
        }
    }

    /**
     * Show narasi content inside a modal element. Fetches the narrative text
     * from BMKG storage and injects it. Call with the modal element IDs.
     */
    async function showNarasiModal(eventid, modalId, titleId, contentId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        showModal(modalId);
        document.getElementById(titleId).textContent = `Narasi BMKG — ${eventid}`;
        setHTML(contentId, '<div class="flex justify-center py-8"><div class="animate-spin w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full"></div></div>');

        const html = await fetchNarasi(eventid);
        if (html) {
            setHTML(contentId, html);
        } else {
            setHTML(contentId, '<p class="text-zinc-500 text-center py-8">Narasi tidak tersedia untuk event ini</p>');
        }
    }

    /** Show a modal by ID — removes hidden, locks body scroll. */
    function showModal(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    /** Hide a modal by ID — adds hidden, unlocks body scroll. */
    function hideModal(id) {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    /**
     * Standard 3-stat info row for detail modals (depth, time, coordinates).
     */
    function detailInfoRow(depth, datetime, latitude, longitude) {
        return `
            <div class="grid grid-cols-3 gap-3 text-center mb-4">
                <div class="bg-zinc-800/30 rounded-lg py-2.5">
                    <p class="text-[9px] text-zinc-500 uppercase font-medium">Kedalaman</p>
                    <p class="text-xs font-semibold text-zinc-300 mt-0.5">${depth}</p>
                </div>
                <div class="bg-zinc-800/30 rounded-lg py-2.5">
                    <p class="text-[9px] text-zinc-500 uppercase font-medium">Waktu</p>
                    <p class="text-xs font-semibold text-zinc-300 mt-0.5">${formatDatetime(datetime)}</p>
                </div>
                <div class="bg-zinc-800/30 rounded-lg py-2.5">
                    <p class="text-[9px] text-zinc-500 uppercase font-medium">Koordinat</p>
                    <p class="text-xs font-semibold text-zinc-300 mt-0.5">${latitude}, ${longitude}</p>
                </div>
            </div>`;
    }

    /**
     * Standard DataTable language config (Indonesian).
     */
    const dataTableLang = {
        search: 'Cari:',
        lengthMenu: 'Tampilkan _MENU_ data',
        info: '_START_–_END_ dari _TOTAL_',
        paginate: { previous: '‹', next: '›' },
        zeroRecords: 'Tidak ada data',
    };

    return {
        fetchJSON,
        magColor, magBg, magHex,
        formatDatetime, formatDate, datetimeSortKey,
        setText, setHTML,
        parseCoords,
        tsunamiLevelColor,
        bmkgImageUrls, bmkgImageLabels, bmkgImageGrid,
        fetchNarasi, showNarasiModal, showModal, hideModal,
        detailInfoRow, dataTableLang,
        BMKG_STORAGE,
    };
})();
