import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Every page is statically generated from public/data at build time; keep the
  // JSON out of any function bundle.
  outputFileTracingExcludes: { "*": ["public/data/**"] },
  async headers() {
    return [
      {
        source: "/data/:path*",
        headers: [
          { key: "Cache-Control", value: "public, max-age=0, s-maxage=86400, stale-while-revalidate=604800" },
        ],
      },
    ];
  },
  async redirects() {
    return [{ source: "/team", destination: "/team/CHC", permanent: false }];
  },
};

export default nextConfig;
