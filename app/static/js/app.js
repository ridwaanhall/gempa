/** Site-wide behaviour: theme toggle, live indicator, active-tsunami banner, relative times. */

import { getJSON } from "./lib/api.js";
import { $, $$, h, replace } from "./lib/dom.js";
import { fmtClock, fmtMag, fmtRelative } from "./lib/format.js";

/* ---------- Theme ---------- */

const root = document.documentElement;

function setTheme(theme, persist) {
  root.dataset.theme = theme;
  if (persist) {
    try { localStorage.setItem("theme", theme); } catch {}
  }
  document.dispatchEvent(new CustomEvent("gempa:theme", { detail: { theme } }));
}

$("#theme-toggle")?.addEventListener("click", () => setTheme(root.dataset.theme === "dark" ? "light" : "dark", true));

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
  let stored = null;
  try { stored = localStorage.getItem("theme"); } catch {}
  if (!stored) setTheme(e.matches ? "dark" : "light", false);
});

/* ---------- Live indicator ---------- */

const live = $("#live-status");
const liveLabel = $("#live-label");
let lastOk = null;

function paintLive(state) {
  if (!live) return;
  live.dataset.state = state;
  if (state === "error") liveLabel.textContent = "Gagal memuat";
  else if (lastOk) liveLabel.textContent = `Diperbarui ${fmtClock(lastOk)}`;
}

document.addEventListener("gempa:data", (e) => {
  if (e.detail.ok) {
    lastOk = e.detail.at;
    paintLive("ok");
  } else {
    paintLive("error");
  }
});

// Pages without live data still get a sensible label.
setTimeout(() => {
  if (!lastOk && live?.dataset.state === "ok") liveLabel.textContent = "Data BMKG";
}, 4000);

/* ---------- Relative times: any element with data-rel-time ---------- */

function refreshRelative() {
  $$("[data-rel-time]").forEach((el) => {
    el.textContent = fmtRelative(el.dataset.relTime);
  });
}
setInterval(refreshRelative, 30000);
document.addEventListener("gempa:rendered", refreshRelative);

/* ---------- Active tsunami warning banner ---------- */

const ACTIVE_WINDOW_MS = 24 * 3600 * 1000;

async function checkTsunami() {
  const banner = $("#tsunami-banner");
  if (!banner) return;
  try {
    const { data } = await getJSON("/api/v1/tsunami");
    const active = data.find((ev) => !ev.ended && Date.now() - new Date(ev.origin_time) < ACTIVE_WINDOW_MS);
    if (!active) {
      banner.hidden = true;
      return;
    }
    replace(
      banner,
      h(
        "div",
        { class: "container" },
        h("strong", {}, "Peringatan dini tsunami aktif"),
        h("span", {}, `M ${fmtMag(active.magnitude)} · ${active.region} · status tertinggi ${active.max_level || "-"}`),
        document.body.dataset.page === "tsunami" ? null : h("a", { href: "/tsunami/" }, "Lihat detail →"),
      ),
    );
    banner.hidden = false;
  } catch {
    // The banner is best-effort; page content reports its own errors.
  }
}

checkTsunami();
setInterval(() => document.visibilityState === "visible" && checkTsunami(), 60000);
