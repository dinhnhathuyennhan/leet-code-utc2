import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bản build tự chứa (.next/standalone) để chạy trong Docker image
  output: "standalone",
  // Không gửi header `X-Powered-By: Next.js` (lộ công nghệ)
  poweredByHeader: false,
  // Repo already manages its own root CLAUDE.md (gitignored); don't let
  // `next dev` regenerate AGENTS.md/CLAUDE.md inside frontend/ every run.
  agentRules: false,
};

export default nextConfig;
