import type { Metadata } from "next";
import "@/styles/globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/context/ToastContext";
import { ClientLayout } from "@/components/layout/ClientLayout";

export const metadata: Metadata = {
  title: "RFP Intellect | AI-Powered RFP Intelligence & Monitoring Platform",
  description:
    "Autonomous RFP procurement discovery, Mode A direct URL extraction, automated website crawling, and LLM-driven opportunity intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ToastProvider>
            <ClientLayout>{children}</ClientLayout>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
