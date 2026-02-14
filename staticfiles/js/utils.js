/**
 * Gempa Monitor — shared utility functions.
 * Provides fetch wrappers, date formatting, magnitude color coding, and DOM helpers.
 */
const GempaUtils = (() => {
    'use strict';

    /** Fetch JSON from an API endpoint with error handling. */
    async function fetchJSON(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    }

    /** Return a Tailwind text-color class based on magnitude. */
    function magColor(mag) {
        if (mag >= 7)   return 'text-red-500';
        if (mag >= 6)   return 'text-red-400';
        if (mag >= 5)   return 'text-orange-400';
        if (mag >= 4)   return 'text-yellow-400';
        if (mag >= 3)   return 'text-green-400';
        return 'text-gray-400';
    }

    /** Return a Tailwind bg-color class for magnitude badges. */
    function magBg(mag) {
        if (mag >= 7)   return 'bg-red-500/20 text-red-400';
        if (mag >= 6)   return 'bg-red-400/20 text-red-300';
        if (mag >= 5)   return 'bg-orange-400/20 text-orange-300';
        if (mag >= 4)   return 'bg-yellow-400/20 text-yellow-300';
        if (mag >= 3)   return 'bg-green-400/20 text-green-300';
        return 'bg-gray-700/40 text-gray-400';
    }

    /** Return a hex colour for Leaflet markers by magnitude. */
    function magHex(mag) {
        if (mag >= 7)   return '#ef4444';
        if (mag >= 6)   return '#f87171';
        if (mag >= 5)   return '#fb923c';
        if (mag >= 4)   return '#facc15';
        if (mag >= 3)   return '#4ade80';
        return '#9ca3af';
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
        return 'bg-gray-700/20 text-gray-400 border-gray-600';
    }

    return {
        fetchJSON,
        magColor, magBg, magHex,
        formatDatetime, formatDate,
        setText, setHTML,
        parseCoords,
        tsunamiLevelColor,
    };
})();
