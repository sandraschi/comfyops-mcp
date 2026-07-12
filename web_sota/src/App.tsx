import { useState, useEffect, useCallback } from "react";
import Sidebar, { type Page } from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import Dashboard from "@/pages/Dashboard";
import Generate from "@/pages/Generate";
import Gallery from "@/pages/Gallery";
import Workflows from "@/pages/Workflows";
import Models from "@/pages/Models";
import Discover from "@/pages/Discover";
import { checkHealth } from "@/lib/api";

function PageContent({ page, onNavigate }: { page: Page; onNavigate: (p: string) => void }) {
  switch (page) {
    case "dashboard":
      return <Dashboard onNavigate={onNavigate} />;
    case "generate":
      return <Generate />;
    case "gallery":
      return <Gallery />;
    case "workflows":
      return <Workflows />;
    case "discover":
      return <Discover onNavigate={onNavigate} />;
    case "models":
      return <Models />;
    default:
      return <Dashboard onNavigate={onNavigate} />;
  }
}

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  const handleNavigate = useCallback((p: string) => {
    setPage(p as Page);
  }, []);

  const refresh = useCallback(async () => {
    try {
      await checkHealth();
      setBackendOk(true);
    } catch {
      setBackendOk(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100">
      <Sidebar activePage={page} onNavigate={handleNavigate} backendOk={backendOk} />

      <div className="flex-1 flex flex-col min-w-0">
        <Topbar title={page} backendOk={backendOk} />

        <main className="flex-1 overflow-y-auto">
          <PageContent page={page} onNavigate={handleNavigate} />
        </main>
      </div>
    </div>
  );
}
