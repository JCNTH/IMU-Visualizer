import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MBL IMUViz - IMU Visualization & Inverse Kinematics",
  description: "Advanced IMU sensor visualization and inverse kinematics processing application for biomechanics research",
  keywords: ["IMU", "biomechanics", "inverse kinematics", "sensor visualization", "motion capture"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className} suppressHydrationWarning={true}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
