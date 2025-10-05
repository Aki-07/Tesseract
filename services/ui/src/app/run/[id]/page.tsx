"use client"; 

import React, { useEffect, useState } from "react";
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

export default function RunDetails() {
  const { id } = useParams(); 
  const [run, setRun] = useState<any>(null);

  useEffect(() => {
    if (!id) return;
    api.get(`/runs/${id}`).then((res) => setRun(res.data));
  }, [id]);

  if (!run) return <div className="p-6">Loading...</div>;

  const rounds = run.rounds || [];

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Run {id}</h1>
      <div className="text-gray-700">
        Attacker: {run.attacker_id} | Defender: {run.defender_id}
      </div>
      <div className="text-gray-700 mb-4">
        Breach Rate: {(run.breach_rate ?? 0).toFixed(2)}
      </div>

      <LineChart width={600} height={300} data={rounds}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="round" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="breach_prob" stroke="#10b981" />
      </LineChart>

      <h3 className="text-xl font-semibold mt-4">Rounds</h3>
      <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
        {JSON.stringify(rounds, null, 2)}
      </pre>
    </div>
  );
}
