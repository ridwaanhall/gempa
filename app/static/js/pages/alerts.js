/** Felt / M5+ pages: announced earthquakes as a list linked to the map. */

import { every, getJSON } from "../lib/api.js";
import { showEarthquake } from "../lib/detail.js";
import { $, $$, debounce, h, matches, replace } from "../lib/dom.js";
import { fmtDateTime, fmtNumber } from "../lib/format.js";
import { initialData } from "../lib/initial.js";
import { createMap, fitIndonesia, quakeMarker } from "../lib/map.js";
import { empty, errorNote, eventItem } from "../lib/ui.js";

const L = window.L;
const feed = $("#alerts").dataset.feed; // "felt" | "significant"
const map = createMap($("#map"));
const layer = L.layerGroup().addTo(map);
const markers = new Map();
const state = { events: [], query: "", selected: null, fitted: false };

function open(eq) {
  state.selected = eq.event_id;
  $$("#list .event").forEach((b) => b.setAttribute("aria-current", String(b.dataset.id === eq.event_id)));
  const marker = markers.get(eq.event_id);
  if (marker) map.setView(marker.getLatLng(), Math.max(map.getZoom(), 6));
  showEarthquake(eq);
}

const note = (eq) => (feed === "felt" ? (eq.felt ? `Dirasakan ${eq.felt}` : "") : eq.potential);

function render() {
  const rows = state.events.filter((e) => matches(`${e.region} ${e.felt ?? ""}`, state.query));
  $("#count").textContent = `${fmtNumber(rows.length)} kejadian`;

  replace(
    $("#list"),
    rows.length
      ? rows.map((eq) =>
          eventItem(eq, {
            note: note(eq),
            flag: eq.tsunami_potential ? "Tsunami" : "",
            current: eq.event_id === state.selected,
            onClick: () => open(eq),
          }),
        )
      : h("li", {}, empty("Tidak ada kejadian", "Coba kata kunci lain.")),
  );

  layer.clearLayers();
  markers.clear();
  [...rows].sort((a, b) => a.magnitude - b.magnitude).forEach((eq) => {
    const marker = quakeMarker(eq, { popup: false }).addTo(layer);
    marker.on("click", () => open(eq));
    markers.set(eq.event_id, marker);
  });
  if (!state.fitted && rows.length) {
    fitIndonesia(map, rows);
    state.fitted = true;
  }
  document.dispatchEvent(new Event("gempa:rendered"));
}

function setEvents(data) {
  state.events = data;
  const oldest = data.at(-1);
  replace(
    $("#page-meta"),
    h("span", { class: "chip" }, `${fmtNumber(data.length)} kejadian terakhir`),
    oldest ? h("span", { class: "chip" }, `sejak ${fmtDateTime(oldest.origin_time)}`) : null,
  );
  render();
}

$("#search").addEventListener("input", debounce((e) => { state.query = e.target.value.trim(); render(); }, 150));

async function load() {
  try {
    const { data } = await getJSON(`/api/v1/earthquakes/${feed}`);
    setEvents(data);
  } catch (err) {
    if (!state.events.length) replace($("#list"), h("li", {}, errorNote(err.message)));
  }
}

const initial = initialData();
if (initial) setEvents(initial.events);
else load();
every(120000, load);
