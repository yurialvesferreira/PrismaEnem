"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import Chart from "@/components/Chart";

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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const FALLBACK_YEAR = 2023;

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [ranking, setRanking] = useState<StateRanking[]>([]);
  const [year, setYear] = useState<number>(FALLBACK_YEAR);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // MOCK de dados da Escola do Gestor
  const escolaMock = {
    nome: "Colégio Prisma",
    media_geral: 620.5,
    media_redacao: 750.0,
    media_matematica: 580.0,
  };

  const [reloadKey, setReloadKey] = useState(0);

  const retry = () => {
    setLoading(true);
    setError(null);
    setReloadKey((key) => key + 1);
  };

  useEffect(() => {
    let ignore = false;

    async function fetchData() {
      try {
        let selectedYear = FALLBACK_YEAR;
        try {
          const yearsRes = await axios.get<{ years: number[] }>(`${API_URL}/enem/years`);
          if (yearsRes.data.years?.length) {
            selectedYear = Math.max(...yearsRes.data.years);
          }
        } catch {
          // Endpoint de anos indisponível: segue com o ano padrão.
        }

        const [statsRes, rankingRes] = await Promise.all([
          axios.get<Stats>(`${API_URL}/enem/${selectedYear}/stats`),
          axios.get<StateRanking[]>(`${API_URL}/enem/${selectedYear}/states?limit=10`),
        ]);
        if (ignore) return;
        setYear(selectedYear);
        setStats(statsRes.data);
        setRanking(rankingRes.data);
      } catch (err) {
        console.error("Erro ao buscar dados da API:", err);
        if (!ignore) {
          setError(
            "Não foi possível carregar os dados da API. Verifique se o backend está no ar e se os dados foram processados."
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    fetchData();
    return () => {
      ignore = true;
    };
  }, [reloadKey]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xl font-medium text-indigo-400 animate-pulse tracking-wide">
            Decodificando microdados do ENEM...
          </p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
        <div className="max-w-md w-full bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center shadow-2xl">
          <div className="w-14 h-14 mx-auto rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mb-5">
            <svg className="w-7 h-7 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
          </div>
          <h1 className="text-xl font-bold text-slate-100 mb-2">Dados indisponíveis</h1>
          <p className="text-slate-400 text-sm mb-6">
            {error ?? "Nenhum dado retornado pela API."}
          </p>
          <button
            onClick={retry}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 transition-colors rounded-xl font-semibold text-white shadow-lg shadow-indigo-500/20"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  const deltaMediaGeral = escolaMock.media_geral - stats.media_geral;

  const comparisonData = {
    labels: ["Média Geral", "Redação", "Matemática"],
    datasets: [
      {
        label: "Sua Escola",
        data: [escolaMock.media_geral, escolaMock.media_redacao, escolaMock.media_matematica],
        backgroundColor: "rgba(99, 102, 241, 0.85)", // indigo-500
        borderColor: "rgba(99, 102, 241, 1)",
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: "Média Nacional",
        data: [stats.media_geral, stats.media_redacao, stats.media_matematica],
        backgroundColor: "rgba(148, 163, 184, 0.3)", // slate-400 low opacity
        borderColor: "rgba(148, 163, 184, 0.8)",
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const statesData = {
    labels: ranking.map((r) => r.uf),
    datasets: [
      {
        label: "Média Geral por UF",
        data: ranking.map((r) => r.media),
        backgroundColor: "rgba(16, 185, 129, 0.85)", // emerald-500
        borderColor: "rgba(16, 185, 129, 1)",
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-6 md:p-10 font-sans selection:bg-indigo-500/30">
      <div className="max-w-7xl mx-auto space-y-10">

        {/* HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-linear-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-linear-to-r from-indigo-400 to-purple-400">
                PrismaEnem
              </h1>
              <p className="text-slate-400 mt-1 text-sm font-medium">
                Dashboard Analítico do Gestor — ENEM {year}
              </p>
            </div>
          </div>
          <div className="mt-6 md:mt-0 px-5 py-2.5 bg-slate-800/80 rounded-xl font-medium border border-slate-700/50 shadow-inner flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
            <span className="text-slate-300">{escolaMock.nome}</span>
          </div>
        </header>

        {/* OVERVIEW CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-xl hover:bg-slate-800/40 transition-colors relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg className="w-16 h-16 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest relative z-10">Total de Inscritos (Nacional)</p>
            <p className="text-4xl font-black text-slate-100 mt-3 relative z-10">
              {stats.total_inscritos.toLocaleString("pt-BR")}
            </p>
          </div>

          <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-xl hover:bg-slate-800/40 transition-colors relative overflow-hidden group">
             <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg className="w-16 h-16 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest relative z-10">Sua Média Geral</p>
            <div className="flex items-end gap-3 mt-3 relative z-10">
              <p className="text-4xl font-black text-indigo-400">
                {escolaMock.media_geral.toFixed(1)}
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 text-sm relative z-10">
              <span className="text-slate-400 bg-slate-800/80 px-2 py-1 rounded">Nacional: {stats.media_geral.toFixed(1)}</span>
              {deltaMediaGeral >= 0 ? (
                <span className="text-emerald-400 text-xs font-bold">+{deltaMediaGeral.toFixed(1)}</span>
              ) : (
                <span className="text-rose-400 text-xs font-bold">{deltaMediaGeral.toFixed(1)}</span>
              )}
            </div>
          </div>

          <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-xl hover:bg-slate-800/40 transition-colors relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg className="w-16 h-16 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest relative z-10">Desempenho Redação</p>
            <p className="text-4xl font-black text-emerald-400 mt-3 relative z-10">
              {escolaMock.media_redacao.toFixed(1)}
            </p>
            <div className="flex items-center gap-2 mt-4 text-sm relative z-10">
              <span className="text-slate-400 bg-slate-800/80 px-2 py-1 rounded">Nacional: {stats.media_redacao.toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* CHARTS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-xl relative">
            <div className="absolute inset-0 bg-linear-to-b from-indigo-500/5 to-transparent rounded-2xl pointer-events-none"></div>
            <h2 className="text-lg font-bold text-slate-200 mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
              Comparativo Escolar vs Nacional
            </h2>
            <div className="h-80 relative z-10">
              <Chart
                data={comparisonData}
                options={{
                  scales: { y: { max: 1000 } }
                }}
              />
            </div>
          </div>

          <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 shadow-xl relative">
            <div className="absolute inset-0 bg-linear-to-b from-emerald-500/5 to-transparent rounded-2xl pointer-events-none"></div>
            <h2 className="text-lg font-bold text-slate-200 mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              Top 10 UFs - Média Geral
            </h2>
            <div className="h-80 relative z-10">
              <Chart
                data={statesData}
                options={{
                  plugins: { legend: { display: false } }
                }}
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
