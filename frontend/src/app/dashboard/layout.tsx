import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden p-4 lg:p-6 gap-4">
        <TopBar />
        <main className="flex-1 overflow-y-auto space-y-6 pb-8">
          {children}
        </main>
      </div>
    </div>
  );
}
