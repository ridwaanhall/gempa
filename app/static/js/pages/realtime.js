/** Realtime: filterable, sortable table of detections linked to the map. */

import { every, getJSON } from "../lib/api.js";
import { showRealtime } from "../lib/detail.js";
import { $, $$, debounce, h, matches, replace } from "../lib/dom.js";
import { fmtDateTime, fmtDepth, fmtNumber, fmtRelative } from "../lib/format.js";
import { createMap, quakeMarker } from "../lib/map.js";
import { empty, errorNote, magBadge, sortable } from "../lib/ui.js";

const L = window.L;
const map = createMap($("#map"));
const layer = L.layerGroup().addTo(map);
const markers = new Map();

const state = { events: [], min: 0, query: "", selected: null };
const table = sortable($("#table"), { key: "origin_time", dir: "desc", onChange: render });

function visible() {
  return table.sort(state.events.filter((e) => e.magnitude >= state.min && matches(e.region, state.query)));
}

function select(ev, { open = true } = {}) {
  state.selected = ev.event_id;
  $$("#rows tr[aria-selected]").forEach((tr) => tr.setAttribute("aria-selected", String(tr.dataset.id === ev.event_id)));
  const marker = markers.get(ev.event_id);
  if (marker) {
    map.setView(marker.getLatLng(), Math.max(map.getZoom(), 6));
    marker.openPopup();
  }
  if (open) showRealtime(ev);
}

function render() {
  const rows = visible();
  $("#count").textContent = `${fmtNumber(rows.length)} dari ${fmtNumber(state.events.length)} kejadian`;

  replace(
    $("#rows"),
    rows.length
      ? rows.map((ev) =>
          h(
            "tr",
            { "data-id": ev.event_id, "aria-selected": String(ev.event_id === state.selected), tabindex: "0",
              onclick: () => select(ev),
              onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(ev); } } },
            h("td", { class: "num" }, magBadge(ev.magnitude, "sm")),
            h("td", { class: "nowrap" }, h("span", { class: "mono" }, fmtDateTime(ev.origin_time).replace(" WIB", "")), h("div", { class: "xsmall muted", "data-rel-time": ev.origin_time }, fmtRelative(ev.origin_time))),
            h("td", { class: "wrap" }, ev.region),
            h("td", { class: "num mono" }, fmtDepth(ev.depth_km)),
          ),
        )
      : h("tr", {}, h("td", { colspan: 4 }, empty("Tidak ada kejadian", "Ubah filter atau kata kunci pencarian."))),
  );

  layer.clearLayers();
  markers.clear();
  // Draw small first so bigger events stay on top.
  [...rows].sort((a, b) => a.magnitude - b.magnitude).forEach((ev) => {
    const marker = quakeMarker(ev).addTo(layer);
    marker.on("click", () => select(ev, { open: false }));
    markers.set(ev.event_id, marker);
  });
  document.dispatchEvent(new Event("gempa:rendered"));
}

$$("#mag-filter button").forEach((btn) =>
  btn.addEventListener("click", () => {
    state.min = Number(btn.dataset.min);
    $$("#mag-filter button").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    render();
  }),
);
$("#search").addEventListener("input", debounce((e) => { state.query = e.target.value.trim(); render(); }, 150));

async function load() {
  try {
    const { data, meta } = await getJSON("/api/v1/earthquakes/realtime?limit=500");
    state.events = data;
    const oldest = data.at(-1);
    replace($("#page-meta"), h("span", {}, `${fmtNumber(meta.count)} deteksi`), oldest ? h("span", {}, `sejak ${fmtDateTime(oldest.origin_time)}`) : null);
    render();
  } catch (err) {
    replace($("#rows"), h("tr", {}, h("td", { colspan: 4 }, errorNote(err.message))));
  }
}

load();
every(60000, load);
