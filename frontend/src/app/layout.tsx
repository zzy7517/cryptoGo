/**
 * 根布局组件 (Root Layout)
 * 
 * 文件作用：
 * - Next.js 应用的根布局，定义全局 HTML 结构
 * - 配置全局字体（Geist Sans 和 Geist Mono）
 * - 设置页面元数据（标题、描述、SEO信息）
 * - 包装全局 Providers（React Query等）
 * 
 * 特点：
 * - 这是服务端组件（Server Component），在服务器端渲染
 * - 所有页面都会继承这个布局
 * - 只在应用启动时渲染一次
 */
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CryptoGo - 智能加密货币交易系统",
  description: "基于大语言模型的智能加密货币交易系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
