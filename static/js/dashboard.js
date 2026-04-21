const chartDataNode = document.getElementById("chart-data");

if (chartDataNode) {
  const chartData = JSON.parse(chartDataNode.textContent);
  const styles = getComputedStyle(document.documentElement);
  const textColor = styles.getPropertyValue("--muted").trim() || "#94a3b8";
  const borderColor = "rgba(148, 163, 184, 0.08)";

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: textColor,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: textColor },
        grid: { color: borderColor },
      },
      y: {
        ticks: { color: textColor },
        grid: { color: borderColor },
      },
    },
  };

  const trendChartNode = document.getElementById("trendChart");
  if (trendChartNode) {
    new Chart(trendChartNode, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: "Humor",
            data: chartData.mood,
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59, 130, 246, 0.18)",
            tension: 0.35,
          },
          {
            label: "Sono",
            data: chartData.sleep,
            borderColor: "#22c55e",
            backgroundColor: "rgba(34, 197, 94, 0.14)",
            tension: 0.35,
          },
          {
            label: "Progresso",
            data: chartData.progress,
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245, 158, 11, 0.14)",
            tension: 0.35,
          },
        ],
      },
      options: commonOptions,
    });
  }

  const habitChartNode = document.getElementById("habitChart");
  if (habitChartNode) {
    new Chart(habitChartNode, {
      type: "bar",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: "Estudo",
            data: chartData.study,
            backgroundColor: "rgba(59, 130, 246, 0.72)",
            borderRadius: 12,
          },
          {
            label: "Exercicio",
            data: chartData.exercise,
            backgroundColor: "rgba(34, 197, 94, 0.72)",
            borderRadius: 12,
          },
        ],
      },
      options: commonOptions,
    });
  }

  const comparisonChartNode = document.getElementById("comparisonChart");
  if (comparisonChartNode) {
    new Chart(comparisonChartNode, {
      type: "bar",
      data: {
        labels: chartData.weekly_labels,
        datasets: [
          {
            label: "Humor medio",
            data: chartData.weekly_mood,
            backgroundColor: "rgba(56, 189, 248, 0.72)",
            borderRadius: 12,
          },
          {
            label: "Progresso medio",
            data: chartData.weekly_progress,
            backgroundColor: "rgba(245, 158, 11, 0.72)",
            borderRadius: 12,
          },
        ],
      },
      options: commonOptions,
    });
  }
}
