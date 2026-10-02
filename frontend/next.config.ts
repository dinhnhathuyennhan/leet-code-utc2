import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Repo already manages its own root CLAUDE.md (gitignored); don't let
  // `next dev` regenerate AGENTS.md/CLAUDE.md inside frontend/ every run.
  agentRules: false,
};

export default nextConfig;
