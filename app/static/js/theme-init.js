// Runs before first paint (blocking, in <head>) so the page never flashes the wrong theme.
(function () {
  var theme = "light";
  try {
    var stored = localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") theme = stored;
    else if (window.matchMedia("(prefers-color-scheme: dark)").matches) theme = "dark";
  } catch (e) {}
  document.documentElement.setAttribute("data-theme", theme);
})();
