import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone', // 为 Docker 部署启用 standalone 模式
};

export default nextConfig;
