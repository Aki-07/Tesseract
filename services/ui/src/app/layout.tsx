import "./globals.css";
import { Inter } from "next/font/google";
import Link from "next/link";
import ParticlesBackground from "./components/ParticleBackground";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.className} relative min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-gray-100`}
      >
        <ParticlesBackground />

        <nav className="flex items-center justify-between px-8 py-4 backdrop-blur-sm bg-white/5 border-b border-white/10">
          <div className="text-xl font-semibold tracking-wide"> Tessera</div>
          <div className="space-x-6 text-sm">
            <Link href="/">Home</Link>
            <Link href="/capsules">Capsules</Link>
            <Link href="/runs">Runs</Link>
          </div>
        </nav>

        <main className="px-8 py-12">{children}</main>
      </body>
    </html>
  );
}
