/** @type {import('next').NextConfig} */
const isDevelopment = process.env.NODE_ENV === 'development';

const nextConfig = {
  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: isDevelopment
              ? [
                  "default-src 'self'",
                  "script-src 'self' 'unsafe-eval'", // Required for Next.js dev
                  "style-src 'self' 'unsafe-inline'", // Required for Carbon
                  "img-src 'self' data: blob: https:",
                  "font-src 'self' data:",
                  "object-src 'none'",
                  "connect-src 'self' http://localhost:* ws://localhost:*",
                  "frame-ancestors 'none'",
                  "base-uri 'self'",
                  "form-action 'self'",
                ].join('; ')
              : [
                  "default-src 'self'",
                  "script-src 'self'",
                  "style-src 'self'",
                  "img-src 'self' data: https:",
                  "font-src 'self' data:",
                  "object-src 'none'",
                  "connect-src 'self' https://*.kyros-praxis.com wss://*.kyros-praxis.com",
                  "frame-ancestors 'none'",
                  "base-uri 'self'",
                  "form-action 'self'",
                  "upgrade-insecure-requests",
                ].join('; '),
          },
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), accelerometer=(), autoplay=(), encrypted-media=(), fullscreen=(), gyroscope=(), magnetometer=(), payment=(), usb=()',
          },
        ],
      },
    ];
  },
  
  // Production optimizations
  poweredByHeader: false,
  compress: true,
  
  // Environment variables validation
  env: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'https://kyros-praxis.com',
  },
  
  // Redirect HTTP to HTTPS in production
  async redirects() {
    return isDevelopment
      ? []
      : [
          {
            source: '/:path*',
            has: [
              {
                type: 'header',
                key: 'x-forwarded-proto',
                value: 'http',
              },
            ],
            destination: 'https://:host/:path*',
            permanent: true,
          },
        ];
  },
};

module.exports = nextConfig;


// Injected content via Sentry wizard below

const { withSentryConfig } = require("@sentry/nextjs");

module.exports = withSentryConfig(
  module.exports,
  {
    // For all available options, see:
    // https://www.npmjs.com/package/@sentry/webpack-plugin#options

    org: "kyros-4n",
    project: "console",

    // Only print logs for uploading source maps in CI
    silent: !process.env.CI,

    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // Route browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers.
    // This can increase your server load as well as your hosting bill.
    // Note: Check that the configured route will not match with your Next.js middleware, otherwise reporting of client-
    // side errors will fail.
    tunnelRoute: "/monitoring",

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    disableLogger: true,

    // Enables automatic instrumentation of Vercel Cron Monitors. (Does not yet work with App Router route handlers.)
    // See the following for more information:
    // https://docs.sentry.io/product/crons/
    // https://vercel.com/docs/cron-jobs
    automaticVercelMonitors: true,
  }
);
