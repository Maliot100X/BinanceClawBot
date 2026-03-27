/** @type {import('next').NextConfig} */
const nextConfig = {
  // NOT static export — we need API routes
  reactStrictMode: true,
  images: { unoptimized: true },
  async rewrites() {
    return [
      {
        source: '/api/bot/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/:path*`,
      },
    ]
  },
}
module.exports = nextConfig
