/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    tsconfigPath: './tsconfig.json'
  },
  eslint: {
    ignoreDuringBuilds: true
  },
  transpilePackages: ['@kyros/core']
};

module.exports = nextConfig;