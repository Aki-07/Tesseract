"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Brain, Shield, Rocket, Cpu } from "lucide-react";
import api from "./utils/api";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [stats, setStats] = useState<{ capsules: number; runs: number }>({
    capsules: 0,
    runs: 0,
  });

  useEffect(() => {
    async function loadStats() {
      try {
        const [caps, runsRes] = await Promise.all([
          api.get("/capsules"),
          api.get("/battle/list"),
        ]);

        const capsulesCount = Array.isArray(caps.data) ? caps.data.length : 0;
        const runsCount = Array.isArray(runsRes.data?.runs)
          ? runsRes.data.runs.length
          : 0;

        setStats({ capsules: capsulesCount, runs: runsCount });
      } catch (err) {
        console.error("Failed to fetch stats:", err);
        setStats({ capsules: 0, runs: 0 });
      }
    }

    loadStats();
    const interval = setInterval(loadStats, 5000); // auto-refresh every 5s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden flex flex-col items-center justify-center text-center px-6 pt-3 pb-40">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-slate-800 to-black animate-gradient-slow"></div>
      <div className="absolute inset-0 bg-[url('/glow.svg')] opacity-30 mix-blend-screen"></div>

      <motion.div
        className="absolute w-96 h-96 rounded-full bg-cyan-500/20 blur-3xl"
        animate={{ x: [0, 100, -100, 0], y: [0, 50, -50, 0] }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute w-72 h-72 rounded-full bg-emerald-500/20 blur-3xl"
        animate={{ x: [50, -50, 80, -80], y: [50, -50, 0, 50] }}
        transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        className="relative z-10 text-6xl sm:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-emerald-400 drop-shadow-lg flex items-center justify-center gap-3"
      >
        <Brain className="w-12 h-12 text-cyan-400 drop-shadow-md" />
        <span>Tesseract</span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="relative z-10 text-gray-300 max-w-2xl mx-auto text-lg leading-relaxed mt-6"
      >
        Enter the <strong className="text-cyan-400">neural battlefield</strong>{" "}
        where autonomous <strong className="text-rose-400">attackers</strong>{" "}
        and <strong className="text-emerald-400">defenders</strong> evolve
        through real-time simulations. Track, adapt, and witness{" "}
        <span className="text-blue-400">AI evolution</span> in action.
      </motion.p>

      <div className="relative z-10 flex flex-wrap justify-center gap-10 mt-16">
        <StatCard
          icon={<Shield className="w-10 h-10 mx-auto text-cyan-400 mb-3" />}
          value={stats.capsules}
          label="Capsules Active"
          borderColor="border-cyan-500/30"
        />
        <StatCard
          icon={<Rocket className="w-10 h-10 mx-auto text-emerald-400 mb-3" />}
          value={stats.runs}
          label="Simulations Run"
          borderColor="border-emerald-500/30"
        />
      </div>

      <motion.div
        className="relative z-10 flex flex-wrap justify-center gap-6 mt-16"
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <Link
          href="/capsules"
          className="group relative px-8 py-3 font-semibold rounded-lg text-white bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 transition-all shadow-md shadow-cyan-500/20"
        >
          Manage Capsules
        </Link>
        <Link
          href="/runs"
          className="group relative px-8 py-3 font-semibold rounded-lg text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 transition-all shadow-md shadow-emerald-500/20"
        >
          View Runs
        </Link>
      </motion.div>

      <div className="relative z-10 mt-20 text-gray-500 text-sm">
        <Cpu className="inline w-4 h-4 mr-2 text-cyan-500" />
        <span className="text-cyan-400">Evolving AI Agents</span>
      </div>

      <style jsx global>{`
        @keyframes gradientMove {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }
        .animate-gradient-slow {
          background-size: 400% 400%;
          animation: gradientMove 20s ease infinite;
        }
      `}</style>
    </div>
  );
}

function StatCard({
  icon,
  value,
  label,
  borderColor,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  borderColor: string;
}) {
  return (
    <motion.div
      whileHover={{ scale: 1.05, rotate: 1 }}
      transition={{ type: "spring", stiffness: 200 }}
      className={`bg-white/10 backdrop-blur-md p-6 rounded-2xl shadow-lg w-64 border ${borderColor}`}
    >
      {icon}
      <motion.p
        key={value}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="text-5xl font-bold text-white"
      >
        {value}
      </motion.p>
      <p className="text-sm text-gray-400 mt-1">{label}</p>
    </motion.div>
  );
}
