import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "next-themes";
import { AuthProvider } from "@/lib/AuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SupaQuery - AI-Powered Data Analysis",
  description: "Query and analyze your documents with AI. Upload PDFs, DOCX, images, and audio files, then chat with an intelligent assistant to extract insights.",
  keywords: ["SupaQuery", "AI", "Data Analysis", "Document Processing", "Next.js", "TypeScript", "Tailwind CSS", "shadcn/ui"],
  authors: [{ name: "SupaQuery Team" }],
  openGraph: {
    title: "SupaQuery - AI-Powered Data Analysis",
    description: "Upload documents and chat with AI to extract insights and answers",
    url: "https://supaquery.app",
    siteName: "SupaQuery",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "SupaQuery - AI-Powered Data Analysis",
    description: "Upload documents and chat with AI to extract insights and answers",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
        suppressHydrationWarning
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            {children}
            <Toaster />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
