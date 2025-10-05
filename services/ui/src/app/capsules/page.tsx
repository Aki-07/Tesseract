"use client";

import React, { useEffect, useState } from "react";
import api from "../utils/api";

interface Capsule {
  id: string;
  name: string;
  type: string;
  service_url: string;
}

export default function Capsules() {
  const [capsules, setCapsules] = useState<Capsule[]>([]);

  const loadCapsules = async () => {
    const res = await api.get("/capsules");
    setCapsules(res.data);
  };

  useEffect(() => {
    loadCapsules();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Capsules</h1>
      <table className="min-w-full bg-white shadow rounded-lg">
        <thead className="bg-gray-200">
          <tr>
            <th className="p-2 text-left">ID</th>
            <th className="p-2 text-left">Name</th>
            <th className="p-2 text-left">Type</th>
            <th className="p-2 text-left">Service URL</th>
          </tr>
        </thead>
        <tbody>
          {capsules.map((c) => (
            <tr key={c.id} className="border-b hover:bg-gray-50">
              <td className="p-2">{c.id}</td>
              <td className="p-2">{c.name}</td>
              <td className="p-2 capitalize">{c.type}</td>
              <td className="p-2 text-xs text-gray-600">{c.service_url}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
