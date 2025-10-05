"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { Brain, Shield, Rocket } from "lucide-react";
import api from "./utils/api";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [stats, setStats] = useState<{ capsules: number; runs: number }>({
    capsules: 0,
    runs: 0,
  });

  useEffect(() => {
    Promise.all([api.get("/capsules"), api.get("/runs")]).then(([caps, runs]) =>
      setStats({ capsules: caps.data.length, runs: runs.data.length })
    );
  }, []);

  return (
    <div className="text-center space-y-10">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-5xl font-extrabold text-cyan-400 flex items-center justify-center gap-3"
      >
        <Brain className="w-10 h-10" /> Tessera Control Center
      </motion.h1>

      <p className="text-gray-300 max-w-2xl mx-auto text-lg">
        The evolving battlefield between autonomous <strong>attackers</strong>{" "}
        and <strong>defenders</strong>. Watch them learn, adapt, and mutate
        through real-time simulations.
      </p>

      <div className="flex justify-center gap-10 mt-10">
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white/10 p-6 rounded-2xl shadow-lg w-64 backdrop-blur-md border border-cyan-500/30"
        >
          <Shield className="w-8 h-8 mx-auto text-cyan-400" />
          <p className="text-4xl font-bold mt-2">{stats.capsules}</p>
          <p className="text-sm text-gray-400">Capsules</p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white/10 p-6 rounded-2xl shadow-lg w-64 backdrop-blur-md border border-emerald-500/30"
        >
          <Rocket className="w-8 h-8 mx-auto text-emerald-400" />
          <p className="text-4xl font-bold mt-2">{stats.runs}</p>
          <p className="text-sm text-gray-400">Runs</p>
        </motion.div>
      </div>

      <div className="flex justify-center gap-6 mt-14">
        <Link
          href="/capsules"
          className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg font-semibold text-white"
        >
          Manage Capsules
        </Link>
        <Link
          href="/runs"
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 rounded-lg font-semibold text-white"
        >
          View Runs
        </Link>
      </div>
    </div>
  );
}
