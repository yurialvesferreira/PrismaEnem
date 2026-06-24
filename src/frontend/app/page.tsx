"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
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

interface Stats {
  total_inscritos: number;
  media_geral: number;
  media_redacao: number;
  media_matematica: number;
}

interface StateRanking {
  uf: string;
  media: number;
  total_alunos: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [ranking, setRanking] = useState<StateRanking[]>([]);
  const [loading, setLoading] = useState(true);

  // MOCK de dados da Escola do Gestor
  const escolaMock = {
    nome: "Colégio Exemplo",
    media_geral: 620.5,
    media_redacao: 750.0,
    media_matematica: 580.0,
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsRes, rankingRes] = await Promise.all([
          axios.get("http://localhost:8000/api/v1/enem/2023/stats"),
          axios.get("http://localhost:8000/api/v1/enem/2023/states?limit=10"),
        ]);
        setStats(statsRes.data);
        setRanking(rankingRes.data);
      } catch (error) {
        console.error("Erro ao buscar dados da API:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="text-xl font-semibold text-blue-600 animate-pulse">
          Carregando dados do ENEM...
        </div>
      </div>
    );
  }

  const comparisonData = {
    labels: ["Média Geral", "Redação", "Matemática"],
    datasets: [
      {
        label: "Sua Escola",
        data: [escolaMock.media_geral, escolaMock.media_redacao, escolaMock.media_matematica],
        backgroundColor: "rgba(59, 130, 246, 0.8)", // blue-500
      },
      {
        label: "Média Nacional",
        data: stats ? [stats.media_geral, stats.media_redacao, stats.media_matematica] : [0, 0, 0],
        backgroundColor: "rgba(148, 163, 184, 0.6)", // slate-400
      },
    ],
  };

  const statesData = {
    labels: ranking.map((r) => r.uf),
    datasets: [
      {
        label: "Média Geral por UF",
        data: ranking.map((r) => r.media),
        backgroundColor: "rgba(16, 185, 129, 0.8)", // emerald-500
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
              PrismaEnem
            </h1>
            <p className="text-slate-500 mt-1">Dashboard do Gestor Escolar</p>
          </div>
          <div className="mt-4 md:mt-0 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg font-medium border border-blue-100">
            {escolaMock.nome}
          </div>
        </header>

        {/* OVERVIEW CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-center">
            <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">Total de Inscritos (Nacional)</p>
            <p className="text-4xl font-bold text-slate-800 mt-2">
              {stats?.total_inscritos.toLocaleString("pt-BR") || "-"}
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-center">
            <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">Sua Média Geral</p>
            <p className="text-4xl font-bold text-blue-600 mt-2">
              {escolaMock.media_geral.toFixed(1)}
            </p>
            <p className="text-sm text-slate-500 mt-2">
              Média Nacional: {stats?.media_geral.toFixed(1)}
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-center">
            <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">Desempenho Redação</p>
            <p className="text-4xl font-bold text-emerald-600 mt-2">
              {escolaMock.media_redacao.toFixed(1)}
            </p>
            <p className="text-sm text-slate-500 mt-2">
              Média Nacional: {stats?.media_redacao.toFixed(1)}
            </p>
          </div>
        </div>

        {/* CHARTS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-6">Comparativo: Sua Escola vs Nacional</h2>
            <div className="h-80">
              <Bar 
                data={comparisonData} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: { beginAtZero: true, max: 1000 }
                  }
                }} 
              />
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-6">Top 10 UFs - Média Geral</h2>
            <div className="h-80">
              <Bar 
                data={statesData} 
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false }
                  },
                  scales: {
                    y: { beginAtZero: true }
                  }
                }} 
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
