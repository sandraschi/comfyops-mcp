import { useEffect, useState } from "react";
import { ExternalLink, Compass, Globe, BookOpen, Users } from "lucide-react";
import { listWorkflows } from "@/lib/api";

const SOURCE_ICONS: Record<string, typeof Globe> = {
  official: BookOpen,
  marketplace: Globe,
  community: Users,
  registry: BookOpen,
};

const SOURCE_COLORS: Record<string, string> = {
  official: "text-blue-400 border-blue-500/30 bg-blue-500/10",
  marketplace: "text-amber-400 border-amber-500/30 bg-amber-500/10",
  community: "text-green-400 border-green-500/30 bg-green-500/10",
  registry: "text-purple-400 border-purple-500/30 bg-purple-500/10",
};

export default function Discover({ onNavigate }: { onNavigate: (p: string) => void }) {
  const [workflowCount, setWorkflowCount] = useState(0);

  useEffect(() => {
    listWorkflows().then((wf) => setWorkflowCount(wf.length)).catch(() => {});
  }, []);

  return (
    <div data-testid="discover" className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
          <Compass className="text-amber-400" size={24} />
          Discover Workflows
        </h1>
        <p className="text-zinc-400 mt-1">
          The ComfyUI community has published thousands of workflows across these platforms.
          Find one you like and add it to your local depot with{" "}
          <code className="text-amber-400 text-sm">comfy_workflows/register</code>.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <>
          <SourceCard
            name="ComfyUI Examples"
            url="https://comfyanonymous.github.io/ComfyUI_examples/"
            type="official"
            description="Official example gallery — basic to advanced workflows with screenshots"
          />
          <SourceCard
            name="CivitAI"
            url="https://civitai.com"
            type="marketplace"
            description="Model and workflow marketplace with parameter previews and community ratings"
          />
          <SourceCard
            name="OpenArt"
            url="https://openart.ai/workflows"
            type="community"
            description="Curated community workflows with before/after comparisons"
          />
          <SourceCard
            name="ComfyUI Registry"
            url="https://registry.comfy.org"
            type="registry"
            description="Official node and workflow registry — discoverable, versioned"
          />
          <SourceCard
            name="Reddit r/comfyui"
            url="https://www.reddit.com/r/comfyui/"
            type="community"
            description="Daily shared workflows, troubleshooting, and tips from 100k+ members"
          />
          <SourceCard
            name="ComfyUI Discord"
            url="https://discord.gg/comfyui"
            type="community"
            description="Real-time help, workflow sharing, and announcements"
          />
        </>
      </div>

      <div className="mt-8 p-4 rounded-lg border border-zinc-800 bg-zinc-900/50">
        <h2 className="text-sm font-semibold text-zinc-300 mb-2">Your Local Depot</h2>
        <p className="text-sm text-zinc-500">
          {workflowCount > 0
            ? `You have ${workflowCount} workflows in your local depot. Browse them in the ` : ""}
          <button
            onClick={() => onNavigate("workflows")}
            className="text-amber-400 hover:text-amber-300 underline underline-offset-2"
          >
            Workflows page
          </button>
          .
        </p>
      </div>
    </div>
  );
}

function SourceCard({
  name, url, type, description,
}: {
  name: string; url: string; type: string; description?: string;
}) {
  const Icon = SOURCE_ICONS[type] || Globe;
  const colorClass = SOURCE_COLORS[type] || "text-zinc-400 border-zinc-700 bg-zinc-800/50";

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex items-start gap-3 p-4 rounded-lg border transition-all hover:scale-[1.02] ${colorClass}`}
    >
      <Icon size={20} className="shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{name}</span>
          <ExternalLink size={12} className="shrink-0 opacity-60" />
        </div>
        {description && (
          <p className="text-xs mt-1 opacity-70 line-clamp-2">{description}</p>
        )}
      </div>
    </a>
  );
}
