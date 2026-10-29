/** @type {import('next').NextConfig} */
function getBackendUrl() {
  let url = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  url = url.trim();
  if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }
  return url.replace(/\/$/, "");
}

const backendUrl = getBackendUrl();

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
      {
        source: "/metrics",
        destination: `${backendUrl}/metrics`,
      },
      {
        source: "/disclaimer",
        destination: `${backendUrl}/disclaimer`,
      },
    ];
  },
};

module.exports = nextConfig;
