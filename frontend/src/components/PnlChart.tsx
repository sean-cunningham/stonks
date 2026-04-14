import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

interface Props {
  realized: number;
  unrealized: number;
  fillsCount: number;
}

export function PnlChart({ realized, unrealized, fillsCount }: Props) {
  const labels = ["Start", "Now"];
  const combined = realized + unrealized;
  const data = {
    labels,
    datasets: [
      {
        label: "Combined P&L (USD)",
        data: [0, combined],
        borderColor: "rgb(56, 189, 248)",
        backgroundColor: "rgba(56, 189, 248, 0.15)",
        fill: true,
        tension: 0.3,
      },
      {
        label: "Realized",
        data: [0, realized],
        borderColor: "rgb(74, 222, 128)",
        fill: false,
        tension: 0.2,
      },
    ],
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: "#cbd5e1" } },
      title: {
        display: true,
        text: `P&L snapshot (fills: ${fillsCount})`,
        color: "#e2e8f0",
      },
    },
    scales: {
      x: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
      y: { ticks: { color: "#94a3b8" }, grid: { color: "#334155" } },
    },
  };
  return (
    <div className="h-56 w-full">
      <Line data={data} options={options} />
    </div>
  );
}
