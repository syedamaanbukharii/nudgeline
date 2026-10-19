/** @type {import('next').NextConfig} */
const apiUrl = process.env.API_INTERNAL_URL || "http://localhost:8000";

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  // In production nginx routes /api to the API before requests reach Next.js.
  // This rewrite makes `npm run dev` work without nginx.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
};

export default nextConfig;
