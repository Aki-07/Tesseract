import "./globals.css";
import { Inter } from "next/font/google";
import { Metadata } from "next";
import NavigationBar from "./components/NavigationBar";
import ParticlesBackground from "./components/ParticleBackground";

export const metadata: Metadata = {
  title: {
    default: "Tesseract",
    template: "%s | Tesseract",
  },
  description:
    "Tesseract Control Center for orchestrating capsule battles and monitoring runs.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.className} relative min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black text-gray-100 overflow-hidden`}
      >
        <ParticlesBackground />
        <NavigationBar />

        <main className="relative z-10 px-8 py-12">{children}</main>

        <div className="absolute inset-0 pointer-events-none border-t border-b border-cyan-500/10 shadow-[0_0_40px_rgba(56,189,248,0.2)_inset]"></div>
      </body>
    </html>
  );
}
