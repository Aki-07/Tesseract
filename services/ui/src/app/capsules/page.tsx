"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Brain, Shield, Cpu } from "lucide-react";
import api from "../utils/api";
import DataTable from "../components/Datatable";

interface Capsule {
  id: string;
  name: string;
  role: string;
  config?: Record<string, unknown> | null;
}

export default function CapsulesPage() {
  const [capsules, setCapsules] = useState<Capsule[]>([]);

  const loadCapsules = async () => {
    try {
      const res = await api.get("/capsules");
      setCapsules(res.data ?? []);
    } catch (err) {
      console.error("Failed to load capsules", err);
    }
  };

  useEffect(() => {
    loadCapsules();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-10">
      <div className="flex justify-between items-center">
        <h1 className="text-4xl font-extrabold text-cyan-400 flex items-center gap-2">
          <Cpu className="w-8 h-8" /> Registered Capsules
        </h1>
        <button
          onClick={loadCapsules}
          className="px-5 py-2 rounded-lg font-semibold bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-cyan-500/20"
        >
          🔄 Refresh
        </button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="rounded-xl overflow-hidden bg-white/5 border border-white/10 backdrop-blur-md"
      >
        <DataTable
          data={capsules}
          columns={[
            { key: "id", label: "ID" },
            { key: "name", label: "Name" },
            {
              key: "role",
              label: "Role",
              render: (value) => (
                <span
                  className={`capitalize ${
                    value === "attacker" ? "text-rose-400" : "text-emerald-400"
                  }`}
                >
                  {value}
                </span>
              ),
            },
            {
              key: "config",
              label: "Service URL",
              render: (val) => String(val?.service_url ?? "—"),
            },
          ]}
        />
      </motion.div>

      {capsules.length === 0 && (
        <p className="text-center text-gray-400 italic">
          No capsules registered yet. Try running{" "}
          <span className="text-cyan-400">/register</span> from the
          orchestrator.
        </p>
      )}
    </div>
  );
}
