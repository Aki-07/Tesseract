"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import api from "../utils/api";

// Available Cerebras models (verified working)
const CEREBRAS_MODELS = {
  "cerebras:llama-3.1-8b": "Llama-3.1-8B (Cerebras)",
  "cerebras:llama-4-scout-17b-16e": "Llama-4-Scout-17B-16E (Cerebras)",
  "cerebras:llama-4-scout-17b-4e": "Llama-4-Scout-17B-4E (Cerebras)",
} as const;

// Free, no-auth HuggingFace models (verified working)
const HF_MODELS = {
  "hf:meta-llama/Llama-3.2-1B-Instruct": "Llama-3.2-1B (Fastest)",
  "hf:meta-llama/Llama-3.2-3B-Instruct": "Llama-3.2-3B (Fast)",
  "hf:distilgpt2": "DistilGPT2 82M - Ultra Fast",
  "hf:gpt2": "GPT2 124M - Very Fast",
  "hf:gpt2-medium": "GPT2 Medium 355M - Fast",
  "hf:gpt2-large": "GPT2 Large 774M - Balanced",

  // GPT-Neo family
  "hf:EleutherAI/gpt-neo-125m": "GPT-Neo 125M - Very Fast",
  "hf:EleutherAI/gpt-neo-1.3B": "GPT-Neo 1.3B - Good Quality",

  // OPT family
  "hf:facebook/opt-350m": "OPT 350M - Fast",
  "hf:facebook/opt-1.3b": "OPT 1.3B - Better Quality",

  // BLOOM family
  "hf:bigscience/bloomz-560m": "BLOOMZ 560M - Multilingual",

  // Pythia family
  "hf:EleutherAI/pythia-410m": "Pythia 410M - Fast",
  "hf:EleutherAI/pythia-1b": "Pythia 1B - Balanced",
} as const;

// Llama models (require HF_API_KEY in backend)
const LLAMA_MODELS = {
  "hf:meta-llama/Llama-3.2-1B-Instruct":
    "Llama 3.2 1B Instruct (requires auth)",
  "hf:meta-llama/Llama-3.2-3B-Instruct":
    "Llama 3.2 3B Instruct (requires auth)",
} as const;

type CerebrasModel = keyof typeof CEREBRAS_MODELS;
type HFModel = keyof typeof HF_MODELS;

export default function StartBattleModal({
  onClose,
  onStarted,
}: {
  onClose: () => void;
  onStarted?: () => void;
}) {
  const router = useRouter();
  const [attacker, setAttacker] = useState<CerebrasModel | HFModel | string>(
    "cerebras:llama-3.1-8b"
  );
  const [defender, setDefender] = useState<CerebrasModel | HFModel | string>(
    "cerebras:llama-3.1-8b"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resolveSelection = (sel: string): string => {
    if (sel.startsWith("hf:")) {
      return `https://api-inference.huggingface.co/models/${sel.slice(3)}`;
    }
    if (sel.startsWith("cerebras:")) {
      return (
        process.env.NEXT_PUBLIC_CEREBRAS_URL ?? "https://api.cerebras.ai/v1"
      );
    }
    return sel;
  };

  const getModelNameForApi = (sel: string): string => {
    if (sel.startsWith("cerebras:")) {
      const modelMap: Record<string, string> = {
        "cerebras:llama-3.1-8b": "llama3.1-8b",
        "cerebras:llama-4-scout-17b-16e": "llama-4-scout-17b-16e-instruct",
        "cerebras:llama-4-scout-17b-4e": "llama-4-scout-17b-4e-instruct",
      };
      return modelMap[sel] || "llama3.1-8b";
    }
    return sel;
  };

  const start = async () => {
    setLoading(true);
    setError(null);

    try {
      const payload: any = {
        attacker_tool: "generate_attack",
        defender_tool: "evaluate_defense",
        rounds: 10,
        interval_seconds: 2.0,
      };

      if (attacker.startsWith("cerebras:")) {
        payload.attacker_url = resolveSelection(attacker);
        payload.attacker_model = getModelNameForApi(attacker);
      } else {
        payload.attacker_url = resolveSelection(attacker);
      }

      if (defender.startsWith("cerebras:")) {
        payload.defender_url = resolveSelection(defender);
        payload.defender_model = getModelNameForApi(defender);
      } else {
        payload.defender_url = resolveSelection(defender);
      }

      const res = await api.post("/battle/start", payload);
      const runId = res.data.run_id;

      if (onStarted) await onStarted();
      onClose();

      // Navigate to the run details page to watch live
      router.push(`/runs`);
    } catch (e: any) {
      console.error("Battle start error:", e);
      setError(
        e.response?.data?.detail || e.message || "Failed to start battle"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
    >
      <div className="w-full max-w-lg max-h-[90vh] overflow-auto bg-slate-900 text-white rounded-xl p-6 border border-slate-700 shadow-2xl">
        <h3 className="text-2xl font-bold mb-2 flex items-center gap-3">
          <span className="text-cyan-400">⚔️</span> Start Battle
        </h3>
        <p className="text-sm text-gray-400 mb-6">
          Select models and start a live attack/defense simulation
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-200 text-sm">
            {error}
          </div>
        )}

        <label className="block text-sm mb-2 font-medium text-gray-300">
          Attacker Model
        </label>
        <select
          value={attacker}
          onChange={(e) => setAttacker(e.target.value)}
          disabled={loading}
          className="w-full mb-5 p-3 rounded-lg bg-slate-800 text-white border border-slate-700 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <optgroup label="🚀 Cerebras (Fastest)">
            {Object.entries(CEREBRAS_MODELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </optgroup>

          <optgroup label="🦙 Llama (Requires HF Token)">
            <option value="hf:meta-llama/Llama-3.2-1B-Instruct">
              Llama 3.2 1B
            </option>
            <option value="hf:meta-llama/Llama-3.2-3B-Instruct">
              Llama 3.2 3B
            </option>
          </optgroup>

          <optgroup label="⚡ Tiny (100-400M) - Free HF">
            <option value="hf:distilgpt2">DistilGPT2 82M</option>
            <option value="hf:gpt2">GPT2 124M</option>
            <option value="hf:EleutherAI/gpt-neo-125m">GPT-Neo 125M</option>
            <option value="hf:facebook/opt-350m">OPT 350M</option>
            <option value="hf:EleutherAI/pythia-410m">Pythia 410M</option>
          </optgroup>

          <optgroup label="🔥 Small (500M-1.5B) - Free HF">
            <option value="hf:gpt2-medium">GPT2 Medium 355M</option>
            <option value="hf:bigscience/bloomz-560m">BLOOMZ 560M</option>
            <option value="hf:gpt2-large">GPT2 Large 774M</option>
            <option value="hf:EleutherAI/pythia-1b">Pythia 1B</option>
            <option value="hf:EleutherAI/gpt-neo-1.3B">GPT-Neo 1.3B</option>
            <option value="hf:facebook/opt-1.3b">OPT 1.3B</option>
          </optgroup>
        </select>

        <label className="block text-sm mb-2 font-medium text-gray-300">
          Defender Model
        </label>
        <select
          value={defender}
          onChange={(e) => setDefender(e.target.value)}
          disabled={loading}
          className="w-full mb-6 p-3 rounded-lg bg-slate-800 text-white border border-slate-700 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
        >
          <optgroup label="🚀 Cerebras Models">
            {Object.entries(CEREBRAS_MODELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </optgroup>

          <optgroup label="🦙 Llama (HF Token Required)">
            {Object.entries(LLAMA_MODELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </optgroup>

          <optgroup label="⚡ HuggingFace (Free)">
            {Object.entries(HF_MODELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </optgroup>
        </select>
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-slate-700 hover:bg-slate-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
            type="button"
          >
            Cancel
          </button>

          <button
            onClick={start}
            disabled={loading}
            className={`px-5 py-2.5 rounded-lg font-semibold transition flex items-center gap-2 ${
              loading
                ? "bg-slate-600 cursor-not-allowed"
                : "bg-cyan-500 hover:bg-cyan-400 text-white shadow-lg shadow-cyan-500/30"
            }`}
            type="button"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <span>⚔️</span>
                Start Battle
              </>
            )}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
