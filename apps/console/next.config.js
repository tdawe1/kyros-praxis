const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    externalDir: true,
  },
  outputFileTracingRoot: path.join(__dirname, '..', '..'),
  async rewrites() {
    // Proxy API requests to backend on port 8001 to avoid CORS in dev
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
