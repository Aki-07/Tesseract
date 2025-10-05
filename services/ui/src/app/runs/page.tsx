"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Brain, Shield, Activity } from "lucide-react";
import Link from "next/link";
import api from "../utils/api";
import DataTable from "../components/Datatable";

interface RunRow {
  id: string;
  attacker_id: string;
  defender_id: string;
  breach_rate: number;
  status?: string;
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
    attacker_id?: string;
    defender_id?: string;
  };
}

export default function RunsPage() {
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [loading, setLoading] = useState(false);

  const loadRuns = async () => {
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
              status.attacker_id ||
              status.meta?.attacker_id ||
              run.attacker_id ||
              "—",
            defender_id:
              status.defender_id ||
              status.meta?.defender_id ||
              run.defender_id ||
              "—",
            breach_rate: status.breach_rate ?? run.breach_rate ?? 0,
            status: status.status ?? run.status ?? "unknown",
          };
        } catch {
          return {
            id: runId,
            attacker_id: run.attacker_id || "—",
            defender_id: run.defender_id || "—",
            breach_rate: run.breach_rate ?? 0,
            status: run.status ?? "unknown",
          };
        }
      })
    );

    setRuns(formatted);
  };

  const startRun = async () => {
    setLoading(true);
    try {
      await api.post("/battle/start_multi", { mode: "from_registry" });
      await loadRuns();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-10">
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

      {/* Paginated + Scrollable Data Table */}
      <DataTable
        data={runs}
        pageSize={15}
        scrollHeight="600px"
        columns={[
          {
            key: "id",
            label: "Run ID",
            render: (v) => (
              <span className="font-mono text-cyan-300">{v.slice(0, 8)}</span>
            ),
          },
          {
            key: "attacker_id",
            label: "Attacker",
            render: (v) => (
              <div className="flex items-center gap-2">
                <Brain className="text-rose-400 w-4 h-4" />
                <span>{v?.slice(0, 8) ?? "—"}</span>
              </div>
            ),
          },
          {
            key: "defender_id",
            label: "Defender",
            render: (v) => (
              <div className="flex items-center gap-2">
                <Shield className="text-emerald-400 w-4 h-4" />
                <span>{v?.slice(0, 8) ?? "—"}</span>
              </div>
            ),
          },
          {
            key: "breach_rate",
            label: "Breach Rate",
            render: (v) => (
              <div className="w-40">
                <div className="w-full h-2 bg-gray-700/50 rounded-full overflow-hidden mb-1">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      v > 0.7
                        ? "bg-rose-500"
                        : v > 0.3
                        ? "bg-yellow-500"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${(v ?? 0) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-400">
                  {((v ?? 0) * 100).toFixed(1)}%
                </span>
              </div>
            ),
          },
          {
            key: "status",
            label: "Details",
            render: (_, row) => (
              <Link
                href={`/run/${row.id}`}
                className="text-cyan-400 hover:text-cyan-300 transition font-medium"
              >
                View →
              </Link>
            ),
          },
        ]}
      />
    </div>
  );
}
