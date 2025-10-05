"use client";

import RunDetails from "@/app/components/RunDetail";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import api from "../../utils/api";

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

export default function RunDetailsForAId() {
  const { id } = useParams();
  const [run, setRun] = useState<RunDetail | null>(null);

  useEffect(() => {
    if (!id) return;
    api.get(`/battle/get/${id}`).then((res) => setRun(res.data));
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

  if (!run) return <div className="p-6 text-white">Loading...</div>;

  return (
    <main className="min-h-screen w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white p-8 overflow-y-auto">
      {/* Run Summary */}
      <RunDetails />
    </main>
  );
}
