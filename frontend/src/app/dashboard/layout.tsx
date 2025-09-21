import { AppHeader } from "@/components/layout/AppHeader";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />
      <main className="pt-0">
        {children}
      </main>
    </div>
  );
} 