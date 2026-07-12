import { useEffect, useState } from "react";
import { listRecent, type GalleryItem } from "@/lib/api";
import { ImageIcon, Loader2, Calendar, Hash, Cpu } from "lucide-react";

export default function Gallery() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listRecent(30)
      .then((res) => setItems(res))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div data-testid="gallery" className="page-container">
        <div className="flex items-center justify-center h-64 text-zinc-500">
          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          Loading gallery...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="gallery" className="page-container">
        <div className="glass-card p-6 text-center">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="gallery" className="page-container">
      <h2 className="page-title">Gallery</h2>

      {items.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <ImageIcon className="w-12 h-12 mx-auto mb-3 text-zinc-700" />
          <p className="text-zinc-500">No generations yet.</p>
          <p className="text-zinc-600 text-sm mt-1">
            Generate your first image to see it here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {items.map((item) => (
            <div
              key={item.prompt_id}
              className="glass-card-hover overflow-hidden group"
            >
              <div className="aspect-square bg-zinc-800 flex items-center justify-center relative">
                {item.outputs && item.outputs.length > 0 ? (
                  <div className="w-full h-full bg-zinc-800 flex items-center justify-center text-zinc-600">
                    <ImageIcon className="w-10 h-10" />
                  </div>
                ) : (
                  <div className="w-full h-full bg-zinc-800 flex items-center justify-center text-zinc-600">
                    <ImageIcon className="w-10 h-10" />
                  </div>
                )}
              </div>
              <div className="p-4 space-y-2">
                <p className="text-sm text-zinc-300 line-clamp-2 leading-relaxed">
                  {item.prompt}
                </p>
                <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-zinc-500">
                  {item.seed != null && (
                    <span className="flex items-center gap-1">
                      <Hash size={10} />
                      {item.seed}
                    </span>
                  )}
                  {item.model && (
                    <span className="flex items-center gap-1">
                      <Cpu size={10} />
                      {item.model}
                    </span>
                  )}
                  {item.date && (
                    <span className="flex items-center gap-1">
                      <Calendar size={10} />
                      {new Date(item.date).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <div className="text-xs text-zinc-600 font-mono truncate">
                  {item.workflow_id}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
