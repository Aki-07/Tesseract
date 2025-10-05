"use client";
import React, { useEffect, useState } from "react";
import api from "../utils/api";
import Link from "next/link";

interface Run {
  id: string;
  attacker_id: string;
  defender_id: string;
  breach_rate?: number;
  created_at?: string;
}

export default function Runs() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(false);

  const loadRuns = async () => {
    const res = await api.get("/runs");
    setRuns(res.data);
  };

  const startRun = async () => {
    setLoading(true);
    await api.post("/battle/start_multi", { mode: "from_registry" });
    setLoading(false);
    loadRuns();
  };

  useEffect(() => {
    loadRuns();
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Runs</h1>
        <button
          onClick={startRun}
          disabled={loading}
          className="bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700"
        >
          {loading ? "Starting..." : "Start Battle"}
        </button>
      </div>

      <table className="min-w-full bg-white shadow rounded-lg">
        <thead className="bg-gray-200">
          <tr>
            <th className="p-2 text-left">ID</th>
            <th className="p-2 text-left">Attacker</th>
            <th className="p-2 text-left">Defender</th>
            <th className="p-2 text-left">Breach Rate</th>
            <th className="p-2 text-left">Details</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id} className="border-b hover:bg-gray-50">
              <td className="p-2">{r.id}</td>
              <td className="p-2">{r.attacker_id}</td>
              <td className="p-2">{r.defender_id}</td>
              <td className="p-2">{(r.breach_rate ?? 0).toFixed(2)}</td>
              <td className="p-2">
                <Link href={`/run/${r.id}`} className="text-blue-600 underline">
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
