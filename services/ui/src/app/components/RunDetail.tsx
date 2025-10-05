"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import api from "../utils/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type RoundEntry = {
  round: number;
  timestamp: string;
  breach?: boolean;
  attacker_output?: string | null;
  defender_output?: string | null;
  attacker_prompt?: string | null;
  defender_prompt?: string | null;
  attacker_called_url?: string | null;
  defender_called_url?: string | null;
  attacker_model?: string | null;
  defender_model?: string | null;
};

type RunDetail = {
  run_id: string;
  attacker_id?: string;
  defender_id?: string;
  breach_rate?: number;
  status?: string;
  rounds: RoundEntry[];
  meta?: {
    attacker_model?: string;
    defender_model?: string;
    attacker_url?: string;
    defender_url?: string;
  };
  total_rounds?: number;
  task_active?: boolean;
};

export default function RunDetails() {
  const { id } = useParams();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [polling, setPolling] = useState(true);
  const [showRaw, setShowRaw] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    let timer: number | null = null;

    const fetch = async () => {
      if (!id) return;
      try {
        const res = await api.get(`/battle/status/${id}`);
        if (!mountedRef.current) return;
        setRun(res.data);
      } catch (err) {
        console.error("Failed to fetch run status", err);
      }
    };

    fetch();
    if (polling) timer = window.setInterval(fetch, 1000);

    return () => {
      mountedRef.current = false;
      if (timer) window.clearInterval(timer);
    };
  }, [id, polling]);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const res = await api.get(`/battle/get/${id}`);
        setRun((prev) => prev ?? res.data);
      } catch {}
    })();
  }, [id]);

  const rounds = useMemo<RoundEntry[]>(
    () =>
      run && Array.isArray(run.rounds) ? (run.rounds as RoundEntry[]) : [],
    [run]
  );

  const chartData = useMemo(
    () =>
      rounds.map((round) => ({
        round: round.round,
        breach: round.breach ? 1 : 0,
      })),
    [rounds]
  );

  const copyToClipboard = async (text?: string | null) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {}
  };

  if (!run)
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-gray-400 text-xl">
        Loading run {id}…
      </div>
    );

  return (
    <main className="min-h-screen w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white flex flex-col gap-6 p-6 overflow-auto">
      {/* HEADER */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-cyan-500/30 pb-4">
        <div>
          <h1 className="text-4xl font-bold">
            <span className="bg-gradient-to-r from-red-400 via-rose-500 to-pink-500 bg-clip-text text-transparent">
              {run.meta?.attacker_model ?? run.attacker_id ?? "Attacker"}
            </span>
            <span className="text-gray-500 mx-2">vs</span>
            <span className="bg-gradient-to-r from-sky-400 via-cyan-500 to-blue-600 bg-clip-text text-transparent">
              {run.meta?.defender_model ?? run.defender_id ?? "Defender"}
            </span>
          </h1>
          <div className="text-sm text-gray-400 mt-2">
            Run ID:{" "}
            <span className="text-gray-300">{run.run_id.slice(0, 8)}</span> •{" "}
            Status: <span className="text-cyan-400">{run.status ?? "—"}</span> •
            Breach Rate:{" "}
            <span className="text-red-400">
              {(run.breach_rate ?? 0).toFixed(3)}
            </span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex gap-3">
            <button
              onClick={() => setPolling((p) => !p)}
              className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700"
            >
              {polling ? "Pause" : "Resume"}
            </button>
            <button
              onClick={() => setShowRaw((s) => !s)}
              className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700"
            >
              {showRaw ? "Hide JSON" : "Show JSON"}
            </button>
          </div>
          <div className="text-xs text-gray-500">
            Last update:{" "}
            {rounds.length > 0
              ? new Date(rounds[rounds.length - 1].timestamp).toLocaleString()
              : "—"}
          </div>
        </div>
      </header>

      {/* CHART SECTION */}
      <section className="w-full h-[40vh] bg-slate-800/40 border border-slate-700 rounded-xl p-6 shadow-xl">
        <h2 className="text-2xl font-semibold mb-3 text-cyan-300">
          Breach Trend by Round
        </h2>
        <ResponsiveContainer width="100%" height="90%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="round" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                color: "#e2e8f0",
              }}
            />
            <Line
              type="monotone"
              dataKey="breach"
              stroke="#f87171"
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </section>

      {/* ROUNDS SECTION - FIXED SCROLLING */}
      <section className="flex-1 min-h-0">
        {" "}
        {/* Crucial: min-h-0 allows flex child to shrink */}
        <h2 className="text-2xl font-semibold mb-4 text-emerald-300 sticky top-0 bg-slate-900/80 backdrop-blur-sm py-2 z-10">
          Rounds ({rounds.length})
        </h2>
        <div className="h-full max-h-[calc(100vh-500px)] min-h-[300px] overflow-y-auto border border-slate-700 rounded-lg bg-slate-800/30">
          <div className="space-y-4 p-4">
            {rounds.map((r) => (
              <div
                key={r.round}
                className={`p-5 rounded-lg border transition ${
                  r.breach
                    ? "border-red-500 bg-red-950/30"
                    : "border-slate-700 bg-slate-800/50"
                }`}
              >
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-200">
                      Round {r.round}{" "}
                      {r.breach && (
                        <span className="ml-2 text-red-400 font-bold">
                          ⚠ Breach
                        </span>
                      )}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {new Date(r.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-xs text-gray-400 text-right">
                    Attacker: {r.attacker_model ?? "—"} <br />
                    Defender: {r.defender_model ?? "—"}
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  {/* Attacker Output */}
                  <div className="bg-slate-900/70 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <p className="text-xs text-rose-400 font-semibold">
                        Attacker Output
                      </p>
                      <button
                        onClick={() => copyToClipboard(r.attacker_output)}
                        className="text-xs text-gray-500 hover:text-gray-300"
                      >
                        Copy
                      </button>
                    </div>
                    <div className="max-h-48 overflow-y-auto">
                      <pre className="whitespace-pre-wrap text-sm font-sans">
                        {r.attacker_output ?? "—"}
                      </pre>
                    </div>
                  </div>

                  {/* Defender Output */}
                  <div className="bg-slate-900/70 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <p className="text-xs text-emerald-400 font-semibold">
                        Defender Output
                      </p>
                      <button
                        onClick={() => copyToClipboard(r.defender_output)}
                        className="text-xs text-gray-500 hover:text-gray-300"
                      >
                        Copy
                      </button>
                    </div>
                    <div className="max-h-48 overflow-y-auto">
                      <pre className="whitespace-pre-wrap text-sm font-sans">
                        {r.defender_output ?? "—"}
                      </pre>
                    </div>
                  </div>
                </div>

                {/* Prompts Section - Only show if prompts exist */}
                {(r.attacker_prompt || r.defender_prompt) && (
                  <div className="mt-4 grid md:grid-cols-2 gap-4 text-sm">
                    {r.attacker_prompt && (
                      <div className="bg-slate-950/50 rounded-lg p-3">
                        <p className="text-xs text-amber-400 font-semibold mb-2">
                          Attacker Prompt
                        </p>
                        <div className="max-h-32 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-xs font-sans text-gray-300">
                            {r.attacker_prompt}
                          </pre>
                        </div>
                      </div>
                    )}
                    {r.defender_prompt && (
                      <div className="bg-slate-950/50 rounded-lg p-3">
                        <p className="text-xs text-amber-400 font-semibold mb-2">
                          Defender Prompt
                        </p>
                        <div className="max-h-32 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-xs font-sans text-gray-300">
                            {r.defender_prompt}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {showRaw && (
        <section className="mt-4">
          <h3 className="text-lg font-semibold mb-2 text-gray-300">Raw JSON</h3>
          <div className="max-h-96 overflow-y-auto bg-black/70 p-4 rounded">
            <pre className="text-xs overflow-auto">
              {JSON.stringify(run, null, 2)}
            </pre>
          </div>
        </section>
      )}
    </main>
  );
}
