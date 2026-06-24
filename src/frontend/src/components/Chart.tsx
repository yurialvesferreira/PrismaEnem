"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface ChartProps {
  data: ChartData<"bar">;
  options?: ChartOptions<"bar">;
}

export default function Chart({ data, options }: ChartProps) {
  const defaultOptions: ChartOptions<"bar"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#e2e8f0', // slate-200
          font: { family: 'Inter, sans-serif' }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)', // slate-900
        titleColor: '#f8fafc', // slate-50
        bodyColor: '#cbd5e1', // slate-300
        borderColor: '#334155', // slate-700
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(51, 65, 85, 0.5)', // slate-700
        },
        ticks: { color: '#94a3b8' } // slate-400
      },
      x: {
        grid: {
          display: false,
        },
        ticks: { color: '#94a3b8' } // slate-400
      }
    }
  };

  const finalOptions = { ...defaultOptions, ...options };

  return <Bar data={data} options={finalOptions} />;
}
