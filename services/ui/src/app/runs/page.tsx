"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Brain,
  Shield,
  Clock,
  AlertCircle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import api from "../utils/api";
import StartBattleModal from "../components/StartBattleModel";

interface RunRow {
  id: string;
  attacker_id: string;
  defender_id: string;
  breach_rate: number;
  status?: string;
  meta?: any;
  created_at?: string;
  total_rounds?: number;
  breaches?: number;
}

interface BattleListResponse {
  runs?: any[];
}

interface BattleStatusResponse {
  attacker_id?: string;
  defender_id?: string;
  breach_rate?: number;
  status?: string;
  meta?: {
    attacker_model?: string;
    defender_model?: string;
    attacker_url?: string;
    defender_url?: string;
  };
  created_at?: string;
  total_rounds?: number;
  breaches?: number;
}

export default function RunsPage() {
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  const loadRuns = async () => {
    try {
      const listRes = await api.get<BattleListResponse>("/battle/list");
      const runsList = listRes.data?.runs ?? [];

      const formatted = await Promise.all(
        runsList.map<Promise<RunRow>>(async (run) => {
          const runId = typeof run === "string" ? run : run.id;
          try {
            const statusRes = await api.get<BattleStatusResponse>(
              `/battle/status/${runId}`
            );
            const status = statusRes.data;

            return {
              id: runId,
              attacker_id:
                status.meta?.attacker_model ||
                status.attacker_id ||
                run.attacker_id ||
                "—",
              defender_id:
                status.meta?.defender_model ||
                status.defender_id ||
                run.defender_id ||
                "—",
              breach_rate: status.breach_rate ?? run.breach_rate ?? 0,
              status: status.status ?? run.status ?? "unknown",
              meta: status.meta ?? run.meta ?? {},
              created_at: status.created_at ?? run.created_at,
              total_rounds: status.total_rounds ?? run.total_rounds,
              breaches: status.breaches ?? run.breaches,
            };
          } catch {
            return {
              id: runId,
              attacker_id: run.meta?.attacker_model ?? run.attacker_id ?? "—",
              defender_id: run.meta?.defender_model ?? run.defender_id ?? "—",
              breach_rate: run.breach_rate ?? 0,
              status: run.status ?? "unknown",
              meta: run.meta ?? {},
              created_at: run.created_at,
              total_rounds: run.total_rounds,
              breaches: run.breaches,
            };
          }
        })
      );

      setRuns(formatted);
    } catch (e) {
      console.error("Failed to load runs", e);
    }
  };

  const totalPages = Math.ceil(runs.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentRuns = runs.slice(startIndex, endIndex);

  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  const startRun = async () => {
    setShowModal(true);
  };

  const onModalStarted = async () => {
    setShowModal(false);
    await loadRuns();
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case "running":
        return <Activity className="w-4 h-4 text-blue-400 animate-pulse" />;
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return "—";
    return new Date(dateString).toLocaleString();
  };

  return (
    <main className="min-h-screen w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-4xl font-extrabold text-cyan-400 flex items-center gap-2">
          <Activity className="w-8 h-8" /> Battle Runs
        </h1>
        <button
          onClick={startRun}
          disabled={loading}
          className={`px-5 py-2 rounded-lg font-semibold shadow-lg shadow-cyan-500/20 transition
            ${
              loading
                ? "bg-gray-600 cursor-not-allowed"
                : "bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white"
            }`}
        >
          {loading ? "Starting..." : "⚔️ Start Battle"}
        </button>
      </div>

      {showModal && (
        <StartBattleModal
          onClose={() => setShowModal(false)}
          onStarted={onModalStarted}
        />
      )}

      {/* Table Container */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-700/50 overflow-x-auto">
        <table className="w-full table-fixed">
          <thead className="bg-slate-800/80 border-b border-slate-700/50">
            <tr>
              <th className="w-24 px-3 py-3 text-left text-sm font-semibold text-slate-300">
                ID
              </th>
              <th className="w-28 px-3 py-3 text-left text-sm font-semibold text-slate-300">
                Status
              </th>
              <th className="w-[20%] px-3 py-3 text-left text-sm font-semibold text-slate-300">
                Attacker
              </th>
              <th className="w-[20%] px-3 py-3 text-left text-sm font-semibold text-slate-300">
                Defender
              </th>
              <th className="w-28 px-3 py-3 text-left text-sm font-semibold text-slate-300">
                Breach
              </th>
              <th className="w-20 px-3 py-3 text-left text-sm font-semibold text-slate-300">
                Rounds
              </th>
              <th className="w-24 px-3 py-3 text-left text-sm font-semibold text-slate-300">
                Created
              </th>
              <th className="w-24 px-3 py-3 text-left text-sm font-semibold text-slate-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/30">
            {currentRuns.map((run) => (
              <tr
                key={run.id}
                className="hover:bg-slate-800/30 transition-colors"
              >
                <td className="px-3 py-3">
                  <span className="font-mono text-cyan-300 text-xs truncate block">
                    {run.id.slice(0, 8)}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-1.5">
                    {getStatusIcon(run.status || "")}
                    <span className="text-xs capitalize truncate">
                      {run.status || "unknown"}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-2">
                      <Brain className="text-rose-400 w-4 h-4 flex-shrink-0" />
                      <span className="text-sm truncate">
                        {run.attacker_id ?? "—"}
                      </span>
                    </div>
                    {run.meta?.attacker_url && (
                      <div className="text-xs text-slate-500 truncate mt-1">
                        {run.meta.attacker_url.replace("https://", "")}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-2">
                      <Shield className="text-emerald-400 w-4 h-4 flex-shrink-0" />
                      <span className="text-sm truncate">
                        {run.defender_id ?? "—"}
                      </span>
                    </div>
                    {run.meta?.defender_url && (
                      <div className="text-xs text-slate-500 truncate mt-1">
                        {run.meta.defender_url.replace("https://", "")}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div>
                    <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden mb-1">
                      <div
                        className={`h-full rounded-full transition-all ${
                          run.breach_rate > 0.7
                            ? "bg-rose-500"
                            : run.breach_rate > 0.3
                            ? "bg-yellow-500"
                            : "bg-emerald-500"
                        }`}
                        style={{ width: `${(run.breach_rate ?? 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-300">
                      {((run.breach_rate ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <span className="text-xs text-slate-300">
                    {run.total_rounds ?? "—"}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span className="text-xs text-slate-400">
                    {formatDate(run.created_at || "")}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <Link
                    href={`/run/${run.id}`}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 text-xs font-medium transition"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700/50 bg-slate-800/30">
            <div className="text-sm text-slate-400">
              Showing {startIndex + 1}-{Math.min(endIndex, runs.length)} of{" "}
              {runs.length}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={currentPage === 1}
                className="p-1 rounded hover:bg-slate-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-sm text-slate-300 px-2">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() =>
                  setCurrentPage((p) => Math.min(p + 1, totalPages))
                }
                disabled={currentPage === totalPages}
                className="p-1 rounded hover:bg-slate-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
