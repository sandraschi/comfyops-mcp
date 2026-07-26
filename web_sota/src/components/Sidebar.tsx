import { useState } from "react";
import {
  LayoutDashboard,
  Sparkles,
  Image,
  Workflow,
  Cpu,
  Compass,
  HelpCircle,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export type Page =
  | "dashboard"
  | "generate"
  | "gallery"
  | "workflows"
  | "models"
  | "discover"
  | "help"
  | "settings";

interface NavItem {
  id: Page;
  label: string;
  icon: typeof LayoutDashboard;
}

const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "generate", label: "Generate", icon: Sparkles },
  { id: "gallery", label: "Gallery", icon: Image },
  { id: "workflows", label: "Workflows", icon: Workflow },
  { id: "discover", label: "Discover", icon: Compass },
  { id: "models", label: "Models", icon: Cpu },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "help", label: "Help", icon: HelpCircle },
];

interface SidebarProps {
  activePage: Page;
  onNavigate: (page: Page) => void;
  backendOk: boolean | null;
}

export default function Sidebar({ activePage, onNavigate, backendOk }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      data-testid="sidebar"
      className={`h-screen sticky top-0 flex flex-col bg-zinc-900/70 backdrop-blur-xl border-r border-zinc-800/50 transition-all duration-300 z-40 ${
        collapsed ? "w-16" : "w-56"
      }`}
    >
      {/* Logo + collapse */}
      <div className="flex items-center justify-between px-4 h-14 border-b border-zinc-800/50">
        {!collapsed && (
          <span className="text-lg font-bold tracking-tight text-amber-400">
            comfy<span className="text-zinc-100">ops</span>
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              data-testid={`nav-${item.id}`}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? "bg-amber-600/15 text-amber-400 border border-amber-600/20"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 border border-transparent"
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={18} className="shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Backend status */}
      <div className="px-4 py-3 border-t border-zinc-800/50">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              backendOk === null
                ? "bg-zinc-500 animate-pulse"
                : backendOk
                ? "bg-green-500"
                : "bg-red-500"
            }`}
          />
          {!collapsed && (
            <span className="text-xs text-zinc-500">
              {backendOk === null
                ? "Connecting..."
                : backendOk
                ? "Connected"
                : "Offline"}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}
