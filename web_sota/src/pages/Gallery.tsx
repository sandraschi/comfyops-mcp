import { useEffect, useState } from "react";
import { listRecent, outputUrl, type GalleryItem } from "@/lib/api";
import { ImageIcon, Loader2, Calendar, Hash, Cpu, X } from "lucide-react";

function isVideo(filename: string): boolean {
  return /\.(mp4|webm|mov|gif)$/i.test(filename);
}

export default function Gallery() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lightbox, setLightbox] = useState<{
    item: GalleryItem;
    index: number;
  } | null>(null);

  useEffect(() => {
    listRecent(60)
      .then((res) => setItems(res))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!lightbox) return;
      if (e.key === "Escape") setLightbox(null);
      if (e.key === "ArrowRight") {
        setLightbox((lb) =>
          lb ? { item: items[(lb.index + 1) % items.length], index: (lb.index + 1) % items.length } : lb
        );
      }
      if (e.key === "ArrowLeft") {
        setLightbox((lb) =>
          lb
            ? {
                item: items[(lb.index - 1 + items.length) % items.length],
                index: (lb.index - 1 + items.length) % items.length,
              }
            : lb
        );
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [lightbox, items]);

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
      <p className="text-sm text-zinc-500 mb-5">
        {items.length} recorded generation{items.length === 1 ? "" : "s"} — click to view full size
      </p>

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
          {items.map((item, idx) => {
            const out = item.outputs?.[0];
            const url = out ? outputUrl(out) : null;
            const video = out ? isVideo(out.filename) : false;
            return (
              <div
                key={item.prompt_id}
                className="glass-card-hover overflow-hidden group cursor-pointer"
                onClick={() => setLightbox({ item, index: idx })}
              >
                <div className="aspect-square bg-zinc-900 flex items-center justify-center relative overflow-hidden">
                  {url ? (
                    video ? (
                      <video
                        src={url}
                        className="w-full h-full object-cover"
                        muted
                        loop
                        preload="metadata"
                        onMouseEnter={(e) => e.currentTarget.play()}
                        onMouseLeave={(e) => {
                          e.currentTarget.pause();
                          e.currentTarget.currentTime = 0;
                        }}
                      />
                    ) : (
                      <img
                        src={url}
                        alt={item.prompt}
                        loading="lazy"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                        }}
                      />
                    )
                  ) : (
                    <ImageIcon className="w-10 h-10 text-zinc-600" />
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
            );
          })}
        </div>
      )}

      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col items-center justify-center p-6"
          onClick={() => setLightbox(null)}
        >
          <button
            className="absolute top-4 right-4 p-2 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
          {lightbox.item.outputs?.[0] &&
            (isVideo(lightbox.item.outputs[0].filename) ? (
              <video
                src={outputUrl(lightbox.item.outputs[0])}
                className="max-h-[80vh] max-w-full rounded-lg"
                controls
                autoPlay
              />
            ) : (
              <img
                src={outputUrl(lightbox.item.outputs[0])}
                alt={lightbox.item.prompt}
                className="max-h-[80vh] max-w-full object-contain rounded-lg"
              />
            ))}
          <div className="mt-4 max-w-2xl text-center">
            <p className="text-zinc-300 text-sm leading-relaxed">{lightbox.item.prompt}</p>
            <p className="text-zinc-500 text-xs mt-2 font-mono">
              {lightbox.item.workflow_id} · seed {lightbox.item.seed} ·{" "}
              {new Date(lightbox.item.date).toLocaleString()} ·{" "}
              {lightbox.index + 1}/{items.length}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
