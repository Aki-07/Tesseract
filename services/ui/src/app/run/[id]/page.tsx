"use client"; 

import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import api from "../../utils/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface RoundEntry {
  round: number;
  breach: boolean;
  attacker_output?: string;
  defender_output?: string;
}

interface RunDetail {
  run_id: string;
  attacker_id?: string;
  defender_id?: string;
  breach_rate?: number;
  status?: string;
  rounds: RoundEntry[];
}

export default function RunDetails() {
  const { id } = useParams();
  const [run, setRun] = useState<RunDetail | null>(null);

  useEffect(() => {
    if (!id) return;
    api.get(`/battle/get/${id}`).then((res) => setRun(res.data));
  }, [id]);

  const rounds = useMemo<RoundEntry[]>(
    () => (run && Array.isArray(run.rounds) ? (run.rounds as RoundEntry[]) : []),
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

  if (!run) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Run {id}</h1>
      <div className="text-gray-700 space-y-1">
        <div>
          <span className="font-semibold">Attacker:</span> {run.attacker_id || "—"}
        </div>
        <div>
          <span className="font-semibold">Defender:</span> {run.defender_id || "—"}
        </div>
        <div>
          <span className="font-semibold">Status:</span> {run.status}
        </div>
        <div>
          <span className="font-semibold">Breach Rate:</span> {(run.breach_rate ?? 0).toFixed(2)}
        </div>
      </div>

      <LineChart width={600} height={300} data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="round" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="breach" stroke="#10b981" />
      </LineChart>

      <h3 className="text-xl font-semibold mt-4">Rounds</h3>
      <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
        {JSON.stringify(rounds, null, 2)}
      </pre>
    </div>
  );
}
