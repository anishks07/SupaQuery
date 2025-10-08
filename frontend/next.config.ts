import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    // Ignore ESLint errors during builds
    ignoreDuringBuilds: true,
  },
  // Enable standalone output for Docker
  output: 'standalone',
  // Disable strict mode in production for better compatibility
  reactStrictMode: process.env.NODE_ENV === 'development',
  // Webpack configuration
  webpack: (config, { dev }) => {
    if (dev) {
      // Enable hot module replacement in development
      config.watchOptions = {
        poll: 1000, // Check for changes every second (useful for Docker)
        aggregateTimeout: 300,
      };
    }
    return config;
  },
  // Image optimization configuration
  images: {
    domains: ['localhost'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  // Experimental features
  experimental: {
    // Enable server actions if needed
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

export default nextConfig;
