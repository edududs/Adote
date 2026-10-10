// Dashboard: numbers count up, and the adoptions-by-breed chart. Reduced motion skips both animations.
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!reduceMotion) {
    document.querySelectorAll("[data-count]").forEach((element) => {
      const target = Number(element.dataset.count);
      if (!target) return;
      const start = performance.now();
      const duration = 800;
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = String(Math.round(target * eased));
        if (progress < 1) requestAnimationFrame(tick);
      };
      element.textContent = "0";
      requestAnimationFrame(tick);
    });
  }

  const canvas = document.getElementById("adoptions-by-breed");
  if (!canvas || !window.Chart) return;
  fetch(canvas.dataset.source, { headers: { Accept: "application/json" }, credentials: "same-origin" })
    .then((response) => response.json())
    .then((data) => {
      const box = canvas.closest("[data-chart-box]");
      if (box) box.style.height = `${data.labels.length * 44 + 64}px`;
      const font = { family: "'Inter Variable', system-ui, sans-serif", size: 13 };
      new window.Chart(canvas, {
        type: "bar",
        data: {
          labels: data.labels,
          datasets: [
            {
              label: "Adoções",
              data: data.adoptions,
              backgroundColor: "#2f6f74",
              hoverBackgroundColor: "#a8364b",
              borderRadius: 8,
              maxBarThickness: 28,
            },
          ],
        },
        options: {
          indexAxis: "y",
          maintainAspectRatio: false,
          animation: reduceMotion ? false : { duration: 600, easing: "easeOutQuart" },
          scales: {
            x: { beginAtZero: true, ticks: { precision: 0, color: "#6b5e66", font }, grid: { color: "#efe7e0" } },
            y: { ticks: { color: "#2a2128", font }, grid: { display: false } },
          },
          plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: "#2e1a2b", titleFont: font, bodyFont: font, padding: 10, cornerRadius: 8 },
          },
        },
      });
    });
})();
