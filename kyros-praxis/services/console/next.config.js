/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    const isDev = process.env.NODE_ENV !== "production";
    const scriptSrc = isDev
      ? "script-src 'self' 'unsafe-eval'"
      : "script-src 'self'";
    const connectSrc = [
      "'self'",
      "http://localhost:8000",
      "http://localhost:9000",
      "ws://localhost:8000",
      "ws://localhost:9000",
      // HMR / dev overlay
      "ws://localhost:3000",
    ].join(" ");
    const csp = [
      "default-src 'self'",
      scriptSrc,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      `connect-src ${connectSrc}`,
      "font-src 'self' data:",
      "object-src 'none'",
      "base-uri 'self'",
      "frame-ancestors 'none'",
      "form-action 'self'",
      "report-uri /csp-violation",
    ].join("; ");
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: csp,
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
