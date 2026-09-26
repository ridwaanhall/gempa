/** Felt / M5+ pages: announced earthquakes as a list linked to the map. */

import { every, getJSON } from "../lib/api.js";
import { showEarthquake } from "../lib/detail.js";
import { $, $$, debounce, h, matches, replace } from "../lib/dom.js";
import { fmtDateTime, fmtDepth, fmtNumber, fmtRelative, parseFelt } from "../lib/format.js";
import { createMap, fitTo, quakeMarker } from "../lib/map.js";
import { empty, errorNote, magBadge, pill } from "../lib/ui.js";

const L = window.L;
const feed = $("#alerts").dataset.feed; // "felt" | "significant"
const map = createMap($("#map"));
const layer = L.layerGroup().addTo(map);
const markers = new Map();
const state = { events: [], query: "", fitted: false };

function open(eq) {
  $$("#list .event").forEach((b) => b.setAttribute("aria-current", String(b.dataset.id === eq.event_id)));
  const marker = markers.get(eq.event_id);
  if (marker) map.setView(marker.getLatLng(), Math.max(map.getZoom(), 6));
  showEarthquake(eq);
}

function summary(eq) {
  if (feed === "felt") {
    const felt = parseFelt(eq.felt);
    return felt.length ? `Dirasakan ${felt.slice(0, 3).map((f) => `${f.intensity} ${f.place}`).join(", ")}${felt.length > 3 ? "…" : ""}` : "";
  }
  return eq.potential;
}

function render() {
  const rows = state.events.filter((e) => matches(`${e.region} ${e.felt ?? ""}`, state.query));
  $("#count").textContent = `${fmtNumber(rows.length)} kejadian`;

  replace(
    $("#list"),
    rows.length
      ? rows.map((eq) =>
          h(
            "li",
            {},
            h(
              "button",
              { class: "event", type: "button", "data-id": eq.event_id, onclick: () => open(eq) },
              magBadge(eq.magnitude),
              h(
                "span",
                { style: { minWidth: 0 } },
                h("span", { class: "event__title", style: { display: "block", whiteSpace: "normal" } }, eq.region),
                h("span", { class: "event__meta" }, h("span", {}, fmtDateTime(eq.origin_time)), h("span", {}, fmtDepth(eq.depth_km))),
                summary(eq) ? h("span", { class: "xsmall muted", style: { display: "block", marginTop: "2px" } }, summary(eq)) : null,
              ),
              h(
                "span",
                { class: "event__side" },
                h("span", { "data-rel-time": eq.origin_time }, fmtRelative(eq.origin_time)),
                eq.tsunami_potential ? h("span", { class: "event__flags" }, pill("Tsunami", "signal")) : null,
              ),
            ),
          ),
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
    fitTo(map, rows.map((e) => [e.latitude, e.longitude]), 6);
    state.fitted = true;
  }
  document.dispatchEvent(new Event("gempa:rendered"));
}

$("#search").addEventListener("input", debounce((e) => { state.query = e.target.value.trim(); render(); }, 150));

async function load() {
  try {
    const { data } = await getJSON(`/api/v1/earthquakes/${feed}`);
    state.events = data;
    const oldest = data.at(-1);
    replace($("#page-meta"), h("span", {}, `${fmtNumber(data.length)} kejadian terakhir`), oldest ? h("span", {}, `sejak ${fmtDateTime(oldest.origin_time)}`) : null);
    render();
  } catch (err) {
    replace($("#list"), h("li", {}, errorNote(err.message)));
  }
}

load();
every(120000, load);
