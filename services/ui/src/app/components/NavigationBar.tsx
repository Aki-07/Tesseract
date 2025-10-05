"use client";

import Link from "next/link";
import { Cpu, Brain, Zap, Activity } from "lucide-react";

export default function NavigationBar() {
  return (
    <nav
      className="relative z-50 flex items-center justify-between px-8 py-4 
      bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950
      border-b border-cyan-500/30 
      shadow-[0_0_40px_rgba(56,189,248,0.15)]
      backdrop-blur-2xl"
    >
      {/* Left Section — Logo */}
      <Link href="/" className="group flex items-center gap-3">
        <div className="relative flex items-center justify-center">
          <Brain className="w-7 h-7 text-cyan-400 group-hover:scale-110 transition-transform duration-300" />
          <span className="absolute -bottom-1 left-6 h-[2px] w-0 bg-cyan-400 group-hover:w-6 transition-all duration-300" />
        </div>
        <span
          className="font-extrabold text-2xl tracking-wide 
          bg-gradient-to-r from-cyan-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent 
          group-hover:brightness-125 transition-all"
        >
          Tesseract
        </span>
      </Link>

      {/* Center Links */}
      <div className="hidden md:flex items-center gap-10 text-[15px] font-semibold tracking-wide">
        {[
          { href: "/", label: "Home" },
          { href: "/capsules", label: "Capsules" },
          { href: "/runs", label: "Runs" },
        ].map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className="relative group text-gray-300 hover:text-cyan-400 transition-colors duration-300"
          >
            {label}
            <span className="absolute left-0 -bottom-1 w-0 h-[2px] bg-cyan-400 group-hover:w-full transition-all duration-300 rounded-full"></span>
          </Link>
        ))}
      </div>

      {/* Right Section — Status Widget */}
      <div className="hidden md:flex items-center gap-4">
        <div className="relative px-4 py-2 rounded-xl bg-slate-800/60 border border-cyan-500/30 shadow-inner">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400 animate-pulse" />
            <span className="text-sm text-gray-300 font-medium">System</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span className="text-xs text-emerald-400">Online</span>
          </div>
          <div className="absolute -bottom-[1px] left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent animate-pulse" />
        </div>
      </div>

      <div className="md:hidden flex items-center space-x-4">
        <details className="relative group">
          <summary className="cursor-pointer text-cyan-400 text-lg">☰</summary>
          <div
            className="absolute right-0 mt-2 w-44 bg-slate-900/90 backdrop-blur-xl 
              border border-cyan-500/20 rounded-lg shadow-2xl flex flex-col p-3 space-y-3 z-50"
          >
            <Link href="/" className="hover:text-cyan-400 transition">
              Home
            </Link>
            <Link href="/capsules" className="hover:text-cyan-400 transition">
              Capsules
            </Link>
            <Link href="/runs" className="hover:text-cyan-400 transition">
              Runs
            </Link>
          </div>
        </details>
      </div>
    </nav>
  );
}
