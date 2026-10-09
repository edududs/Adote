// Draws the dashboard chart from the JSON endpoint. Chart.js is loaded by the dashboard page only.
(function () {
  "use strict";

  const canvas = document.getElementById("adoptions-by-breed");
  if (!canvas || !window.Chart) {
    return;
  }

  fetch(canvas.dataset.source, { headers: { Accept: "application/json" }, credentials: "same-origin" })
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      new window.Chart(canvas, {
        type: "bar",
        data: {
          labels: data.labels,
          datasets: [
            {
              label: "Adoções",
              data: data.adoptions,
              backgroundColor: "#3d7b80",
            },
          ],
        },
        options: {
          indexAxis: "y",
          scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
          plugins: { legend: { display: false } },
        },
      });
    });
})();
