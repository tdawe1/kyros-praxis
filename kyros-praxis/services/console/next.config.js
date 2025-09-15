/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self'",
              "img-src 'self' data: blob:",
              "style-src 'self' 'unsafe-inline'",
              "connect-src 'self' http://localhost:8000 http://localhost:9000 ws://localhost:8000 ws://localhost:9000",
              "object-src 'none'",
              "base-uri 'self'",
              "frame-ancestors 'none'",
              "report-uri /csp-violation",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
