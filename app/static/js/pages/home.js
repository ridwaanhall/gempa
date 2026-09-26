/** Home: latest felt earthquake + realtime summary + recent detections. */

import { every, getJSON } from "../lib/api.js";
import { showEarthquake, showRealtime } from "../lib/detail.js";
import { $, h, replace } from "../lib/dom.js";
import {
  fmtCoords, fmtDateTime, fmtDepth, fmtLong, fmtMag, fmtNumber, fmtRelative, magBucket, magColor, parseFelt,
} from "../lib/format.js";
import { createMap, epicenterMarker, quakeMarker } from "../lib/map.js";
import { errorNote, facts, feltList, magBadge, pill } from "../lib/ui.js";

const L = window.L;
const map = createMap($("#latest-map"), { scrollWheelZoom: false });
const recentLayer = L.layerGroup().addTo(map);
let epicenter = null;
let shownEventId = null;

/* ---------- Latest felt earthquake ---------- */

function renderLatest(eq) {
  const scale = $("#latest-scale");
  scale.style.setProperty("--mag-bg", magColor(eq.magnitude));
  $("#latest-mag").textContent = fmtMag(eq.magnitude);
  replace($("#latest-region"), eq.region);
  replace($("#latest-time"), fmtLong(eq.origin_time), " · ", h("span", { "data-rel-time": eq.origin_time }, fmtRelative(eq.origin_time)));

  replace(
    $("#latest-facts"),
    ...facts([
      ["Kedalaman", fmtDepth(eq.depth_km)],
      ["Koordinat", fmtCoords(eq.latitude, eq.longitude)],
      ["Potensi tsunami", eq.tsunami_potential ? h("strong", { style: { color: "var(--signal)" } }, "Berpotensi tsunami") : "Tidak berpotensi"],
      ["Kategori", `${["Mikro", "", "", "Minor", "Ringan", "Sedang", "Kuat", "Besar"][magBucket(eq.magnitude)] || "Mikro"} (M${fmtMag(eq.magnitude)})`],
    ]).childNodes,
  );

  const felt = parseFelt(eq.felt);
  replace($("#latest-felt"), felt.length ? [h("p", { class: "xsmall muted", style: { marginBottom: "var(--s-2)" } }, "Dirasakan (skala MMI)"), feltList(felt)] : "");

  replace(
    $("#latest-actions"),
    h("button", { class: "btn btn--primary", type: "button", onclick: () => showEarthquake(eq) }, "Detail & peta guncangan"),
    h("a", { class: "btn", href: "/felt/" }, "Gempa dirasakan lainnya"),
  );

  if (shownEventId !== eq.event_id) {
    epicenter?.remove();
    epicenter = epicenterMarker(eq.latitude, eq.longitude, eq.magnitude).addTo(map);
    map.setView([eq.latitude, eq.longitude], 6, { animate: false });
    shownEventId = eq.event_id;
  }
  document.dispatchEvent(new Event("gempa:rendered"));
}

async function loadLatest() {
  try {
    const { data } = await getJSON("/api/v1/earthquakes/latest");
    renderLatest(data);
  } catch (err) {
    replace($("#latest-region"), "Data gempa terakhir tidak tersedia");
    replace($("#latest-time"), errorNote(err.message));
  }
}

/* ---------- Realtime summary + list ---------- */

const DAY = 86400000;

function stat(label, value, note) {
  return h("div", { class: "stat" }, h("p", { class: "stat__label" }, label), h("p", { class: "stat__value" }, value), h("p", { class: "stat__note" }, note || " "));
}

function renderSummary(realtime, significant, tsunami) {
  const now = Date.now();
  const day = realtime.filter((e) => now - new Date(e.origin_time) < DAY);
  const strongest = day.reduce((a, b) => (!a || b.magnitude > a.magnitude ? b : a), null);
  const m5week = significant.filter((e) => now - new Date(e.origin_time) < 7 * DAY);
  const active = tsunami.find((e) => !e.ended && now - new Date(e.origin_time) < DAY);
  const lastTsunami = tsunami[0];

  replace(
    $("#summary"),
    stat("Gempa 24 jam", fmtNumber(day.length), "terdeteksi otomatis"),
    stat("Terkuat 24 jam", strongest ? fmtMag(strongest.magnitude) : "–", strongest?.region),
    stat("M5+ 7 hari", fmtNumber(m5week.length), m5week[0] ? `terakhir ${fmtRelative(m5week[0].origin_time)}` : "di wilayah Indonesia"),
    stat(
      "Tsunami",
      active ? h("span", { style: { color: "var(--signal)" } }, "Aktif") : "Aman",
      active ? active.region : lastTsunami ? `peringatan terakhir ${fmtRelative(lastTsunami.origin_time)}` : "tidak ada peringatan",
    ),
  );
}

function renderRecent(realtime) {
  const items = realtime.slice(0, 10);
  replace(
    $("#recent-list"),
    items.map((ev) =>
      h(
        "li",
        {},
        h(
          "button",
          { class: "event", type: "button", onclick: () => showRealtime(ev) },
          magBadge(ev.magnitude),
          h("span", { style: { minWidth: 0 } }, h("span", { class: "event__title", style: { display: "block" } }, ev.region), h("span", { class: "event__meta" }, h("span", {}, fmtDateTime(ev.origin_time)), h("span", {}, fmtDepth(ev.depth_km)))),
          h("span", { class: "event__side" }, h("span", { "data-rel-time": ev.origin_time }, fmtRelative(ev.origin_time)), ev.magnitude >= 5 ? h("span", { class: "event__flags" }, pill("M5+", "signal", true)) : null),
        ),
      ),
    ),
  );

  recentLayer.clearLayers();
  realtime
    .filter((e) => Date.now() - new Date(e.origin_time) < 2 * DAY)
    .forEach((ev) => quakeMarker(ev, { faint: true }).addTo(recentLayer));
  $("#summary-hint").textContent = `${fmtNumber(realtime.length)} deteksi terakhir`;
  document.dispatchEvent(new Event("gempa:rendered"));
}

async function loadRealtime() {
  try {
    const [rt, sig, ts] = await Promise.allSettled([
      getJSON("/api/v1/earthquakes/realtime"),
      getJSON("/api/v1/earthquakes/significant"),
      getJSON("/api/v1/tsunami"),
    ]);
    if (rt.status !== "fulfilled") throw rt.reason;
    const realtime = rt.value.data;
    renderSummary(realtime, sig.value?.data ?? [], ts.value?.data ?? []);
    renderRecent(realtime);
  } catch (err) {
    replace($("#recent-list"), h("li", {}, errorNote(err.message)));
  }
}

loadLatest();
loadRealtime();
every(60000, () => Promise.all([loadLatest(), loadRealtime()]));
