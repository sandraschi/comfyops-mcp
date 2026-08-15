import { useCallback, useEffect, useMemo, useState } from "react";
import {
  listGallery,
  deleteGenerations,
  getRelated,
  listWorkflows,
  outputUrl,
  galleryExportUrl,
  downloadItems,
  type GalleryItem,
  type GalleryQuery,
  type RelatedResult,
} from "@/lib/api";
import {
  ImageIcon,
  Loader2,
  Calendar,
  Hash,
  Cpu,
  X,
  Search,
  ArrowUpDown,
  Trash2,
  Copy,
  GitBranch,
  FilterX,
  CheckSquare,
  Square,
  FileJson,
  FileSpreadsheet,
  ExternalLink,
} from "lucide-react";

function isVideo(filename: string): boolean {
  return /\.(mp4|webm|mov|gif)$/i.test(filename);
}

const SORTS = [
  { id: "date_desc", label: "Newest first" },
  { id: "date_asc", label: "Oldest first" },
  { id: "prompt", label: "Prompt A-Z" },
  { id: "seed", label: "Seed" },
  { id: "workflow", label: "Workflow" },
  { id: "model", label: "Model" },
];

const inputCls =
  "bg-zinc-800/60 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-zinc-200 " +
  "focus:outline-none focus:border-blue-500/60 placeholder:text-zinc-600";

export default function Gallery() {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [lightbox, setLightbox] = useState<{ item: GalleryItem; index: number } | null>(null);
  const [related, setRelated] = useState<RelatedResult | null>(null);
  const [relatedLoading, setRelatedLoading] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ ids: string[]; label: string } | null>(null);
  const [busy, setBusy] = useState(false);

  // --- Filters (debounced on change via effect) ---
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("date_desc");
  const [workflowFilter, setWorkflowFilter] = useState("");
  const [modelFilter, setModelFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 24;

  const query: GalleryQuery = useMemo(() => {
    const qq: GalleryQuery = { sort, limit: PAGE_SIZE, offset: page * PAGE_SIZE };
    if (workflowFilter) qq.workflow_id = workflowFilter;
    if (modelFilter) qq.model = modelFilter;
    if (q.trim()) qq.q = q.trim();
    if (dateFrom) qq.date_from = dateFrom;
    if (dateTo) qq.date_to = dateTo;
    return qq;
  }, [q, sort, workflowFilter, modelFilter, dateFrom, dateTo, page]);

  const load = useCallback(
    async (replace: boolean) => {
      try {
        setLoading(true);
        const res = await listGallery(query);
        setItems((prev) => (replace ? res.items : [...prev, ...res.items]));
        setTotal(res.total);
        setHasMore(res.has_more);
        setError("");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    },
    [query]
  );

  useEffect(() => {
    setPage(0);
    load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, sort, workflowFilter, modelFilter, dateFrom, dateTo]);

  useEffect(() => {
    listWorkflows()
      .then((wf) => setWorkflows(wf.map((w) => w.id).sort()))
      .catch(() => {});
  }, []);

  const models = useMemo(() => {
    const s = new Set<string>();
    for (const it of items) if (it.model) s.add(it.model);
    return [...s].sort();
  }, [items]);

  const hasFilters = Boolean(q || workflowFilter || modelFilter || dateFrom || dateTo);

  const clearFilters = () => {
    setQ("");
    setWorkflowFilter("");
    setModelFilter("");
    setDateFrom("");
    setDateTo("");
    setPage(0);
  };

  // --- Selection ---
  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelected((prev) =>
      prev.size === items.length ? new Set() : new Set(items.map((i) => i.prompt_id))
    );
  };

  const selectedItems = useMemo(
    () => items.filter((i) => selected.has(i.prompt_id)),
    [items, selected]
  );

  // --- Actions ---
  const doDelete = async (ids: string[]) => {
    setBusy(true);
    try {
      await deleteGenerations(ids);
      const gone = new Set(ids);
      setItems((prev) => prev.filter((i) => !gone.has(i.prompt_id)));
      setSelected((prev) => {
        const next = new Set(prev);
        ids.forEach((id) => next.delete(id));
        return next;
      });
      setTotal((t) => Math.max(0, t - ids.length));
      setConfirmDelete(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setBusy(false);
    }
  };

  const openRelated = async (item: GalleryItem) => {
    setRelatedLoading(item.prompt_id);
    try {
      const res = await getRelated(item.prompt_id);
      setRelated(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Related lookup failed");
    } finally {
      setRelatedLoading(null);
    }
  };

  const copyPrompt = (text: string) => {
    navigator.clipboard?.writeText(text).catch(() => {});
  };

  const openInNewTab = (item: GalleryItem) => {
    const out = item.outputs?.[0];
    if (out) window.open(outputUrl(out), "_blank");
  };

  // Keyboard navigation for lightbox
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

  if (loading && items.length === 0) {
    return (
      <div data-testid="gallery" className="page-container">
        <div className="flex items-center justify-center h-64 text-zinc-500">
          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          Loading gallery...
        </div>
      </div>
    );
  }

  if (error && items.length === 0) {
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
      <div className="flex items-center justify-between mb-2">
        <h2 className="page-title mb-0">Gallery</h2>
        <p className="text-sm text-zinc-500">
          {total} generation{total === 1 ? "" : "s"}
        </p>
      </div>

      {/* Toolbar: search, sort, filters, export */}
      <div data-testid="gallery-toolbar" className="glass-card p-4 mb-5 space-y-3">
        <div className="flex flex-wrap gap-2 items-center">
          <div className="relative">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              data-testid="gallery-search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search prompts, workflows, models..."
              className={`${inputCls} pl-9 w-64`}
            />
          </div>
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-zinc-500" />
            <select
              data-testid="gallery-sort"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className={`${inputCls} cursor-pointer`}
            >
              {SORTS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <select
            data-testid="gallery-filter-workflow"
            value={workflowFilter}
            onChange={(e) => setWorkflowFilter(e.target.value)}
            className={`${inputCls} cursor-pointer`}
          >
            <option value="">All workflows</option>
            {workflows.map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </select>
          <select
            data-testid="gallery-filter-model"
            value={modelFilter}
            onChange={(e) => setModelFilter(e.target.value)}
            className={`${inputCls} cursor-pointer`}
          >
            <option value="">All models</option>
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <input
            data-testid="gallery-date-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className={inputCls}
            title="From date"
          />
          <input
            data-testid="gallery-date-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className={inputCls}
            title="To date"
          />
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-amber-400 hover:bg-amber-500/10 transition-colors"
              title="Clear filters"
            >
              <FilterX className="w-4 h-4" />
              Clear
            </button>
          )}
          <div className="ml-auto flex gap-2">
            <a
              data-testid="gallery-export-csv"
              href={galleryExportUrl("csv", query)}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors"
              title="Export filtered set as CSV"
            >
              <FileSpreadsheet className="w-4 h-4" />
              CSV
            </a>
            <a
              data-testid="gallery-export-json"
              href={galleryExportUrl("json", query)}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors"
              title="Export filtered set as JSON"
            >
              <FileJson className="w-4 h-4" />
              JSON
            </a>
          </div>
        </div>
        {hasFilters && (
          <p className="text-xs text-zinc-600">
            Showing {items.length}/{total} results — filters active. Exports cover the filtered set
            (up to 200 rows server-side).
          </p>
        )}
      </div>

      {/* Batch action bar */}
      {selected.size > 0 && (
        <div
          data-testid="gallery-batch-bar"
          className="glass-card p-3 mb-5 flex items-center gap-3 border border-blue-500/40"
        >
          <span className="text-sm text-blue-300 font-medium">
            {selected.size} selected
          </span>
          <button
            onClick={() => downloadItems(selectedItems, "csv")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Export CSV
          </button>
          <button
            onClick={() => downloadItems(selectedItems, "json")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors"
          >
            <FileJson className="w-4 h-4" />
            Export JSON
          </button>
          <button
            data-testid="gallery-batch-delete"
            onClick={() => setConfirmDelete({ ids: [...selected], label: `${selected.size} selected` })}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors ml-auto"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      )}

      {items.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <ImageIcon className="w-12 h-12 mx-auto mb-3 text-zinc-700" />
          <p className="text-zinc-500">No generations match.</p>
          <p className="text-zinc-600 text-sm mt-1">
            {hasFilters ? "Try clearing the filters." : "Generate your first image to see it here."}
          </p>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-2 mb-3">
            <button
              data-testid="gallery-select-all"
              onClick={toggleSelectAll}
              className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              {selected.size === items.length ? (
                <CheckSquare className="w-4 h-4 text-blue-400" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              {selected.size === items.length ? "Deselect all" : "Select all"}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {items.map((item, idx) => {
              const out = item.outputs?.[0];
              const url = out ? outputUrl(out) : null;
              const video = out ? isVideo(out.filename) : false;
              const isSel = selected.has(item.prompt_id);
              return (
                <div
                  data-testid="gallery-item"
                  key={item.prompt_id}
                  className={`glass-card-hover overflow-hidden group relative cursor-pointer ${
                    isSel ? "ring-2 ring-blue-500/70" : ""
                  }`}
                  onClick={() => setLightbox({ item, index: idx })}
                >
                  <button
                    data-testid="gallery-item-check"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSelect(item.prompt_id);
                    }}
                    className={`absolute top-2 left-2 z-10 p-1.5 rounded-md transition-colors ${
                      isSel
                        ? "bg-blue-500/80 text-white"
                        : "bg-black/50 text-zinc-400 hover:text-white hover:bg-black/70"
                    }`}
                    aria-label={isSel ? "Deselect" : "Select"}
                  >
                    {isSel ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                  </button>

                  {/* Hover action row */}
                  <div className="absolute top-2 right-2 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      data-testid="gallery-item-related"
                      onClick={(e) => {
                        e.stopPropagation();
                        openRelated(item);
                      }}
                      className="p-1.5 rounded-md bg-black/60 text-zinc-300 hover:text-amber-400 transition-colors"
                      title="Crossconnects: related generations"
                      aria-label="Related"
                    >
                      {relatedLoading === item.prompt_id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <GitBranch className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      data-testid="gallery-item-copy"
                      onClick={(e) => {
                        e.stopPropagation();
                        copyPrompt(item.prompt);
                      }}
                      className="p-1.5 rounded-md bg-black/60 text-zinc-300 hover:text-white transition-colors"
                      title="Copy prompt"
                      aria-label="Copy prompt"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    <button
                      data-testid="gallery-item-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmDelete({ ids: [item.prompt_id], label: item.prompt.slice(0, 40) });
                      }}
                      className="p-1.5 rounded-md bg-black/60 text-zinc-300 hover:text-red-400 transition-colors"
                      title="Delete record"
                      aria-label="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

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

          {hasMore && (
            <div className="text-center mt-6">
              <button
                data-testid="gallery-load-more"
                onClick={() => {
                  setPage((p) => p + 1);
                  load(false);
                }}
                disabled={loading}
                className="px-4 py-2 rounded-lg text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors disabled:opacity-50"
              >
                {loading ? "Loading..." : "Load more"}
              </button>
            </div>
          )}
        </>
      )}

      {/* Lightbox */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col items-center justify-center p-6"
          onClick={() => setLightbox(null)}
        >
          <button
            className="absolute top-4 right-4 p-2 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300"
            aria-label="Close"
            onClick={() => setLightbox(null)}
          >
            <X className="w-5 h-5" />
          </button>
          <div className="absolute top-4 left-4 flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                copyPrompt(lightbox.item.prompt);
              }}
              className="p-2 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300"
              title="Copy prompt"
            >
              <Copy className="w-5 h-5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                openInNewTab(lightbox.item);
              }}
              className="p-2 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300"
              title="Open in new tab"
            >
              <ExternalLink className="w-5 h-5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                openRelated(lightbox.item);
              }}
              className="p-2 rounded-full bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300"
              title="Related generations"
            >
              <GitBranch className="w-5 h-5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setConfirmDelete({ ids: [lightbox.item.prompt_id], label: lightbox.item.prompt.slice(0, 40) });
              }}
              className="p-2 rounded-full bg-zinc-800/80 hover:bg-red-500/30 text-red-400"
              title="Delete record"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
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
              {new Date(lightbox.item.date).toLocaleString()} · {lightbox.index + 1}/{items.length}
            </p>
          </div>
        </div>
      )}

      {/* Related / crossconnects panel */}
      {related && (
        <div
          data-testid="gallery-related-panel"
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6"
          onClick={() => setRelated(null)}
        >
          <div
            className="glass-card max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                  <GitBranch className="w-5 h-5 text-amber-400" />
                  Crossconnects
                </h3>
                <p className="text-xs text-zinc-500 mt-1 max-w-xl truncate">{related.base.prompt}</p>
              </div>
              <button
                onClick={() => setRelated(null)}
                className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex flex-wrap gap-3 mb-5 text-sm">
              <span className="px-3 py-1.5 rounded-lg bg-zinc-800/70 text-zinc-300">
                workflow <code className="text-amber-400">{related.crossconnects.workflow}</code>{" "}
                <span className="text-zinc-500">· {related.crossconnects.same_workflow_count} more</span>
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-zinc-800/70 text-zinc-300">
                model <code className="text-blue-400">{related.crossconnects.model || "n/a"}</code>{" "}
                <span className="text-zinc-500">· {related.crossconnects.same_model_count} more</span>
              </span>
            </div>

            {related.items.length === 0 ? (
              <p className="text-zinc-500 text-sm">No other generations share this workflow or model.</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {related.items.map((it) => {
                  const out = it.outputs?.[0];
                  return (
                    <button
                      key={it.prompt_id}
                      className="text-left glass-card-hover overflow-hidden"
                      onClick={() => {
                        const idx = items.findIndex((x) => x.prompt_id === it.prompt_id);
                        setRelated(null);
                        if (idx >= 0) setLightbox({ item: it, index: idx });
                        else setLightbox({ item: it, index: 0 });
                      }}
                    >
                      <div className="aspect-video bg-zinc-900 overflow-hidden">
                        {out && (
                          <img
                            src={outputUrl(out)}
                            alt={it.prompt}
                            loading="lazy"
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = "none";
                            }}
                          />
                        )}
                      </div>
                      <div className="p-2.5">
                        <p className="text-xs text-zinc-300 line-clamp-2">{it.prompt}</p>
                        <p className="text-[10px] text-zinc-600 mt-1 font-mono truncate">
                          {it.workflow_id} · {it.date?.slice(0, 10)}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confirm delete */}
      {confirmDelete && (
        <div className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="glass-card max-w-md w-full p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-zinc-100 mb-2 flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-red-400" />
              Delete generation record{confirmDelete.ids.length > 1 ? "s" : ""}?
            </h3>
            <p className="text-sm text-zinc-400 mb-1">
              <code className="text-zinc-300">{confirmDelete.label}</code>
            </p>
            <p className="text-xs text-zinc-600 mb-5">
              Removes {confirmDelete.ids.length} record{confirmDelete.ids.length > 1 ? "s" : ""} from
              the gallery. Output files on disk are kept.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 rounded-lg text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
              >
                Cancel
              </button>
              <button
                data-testid="gallery-confirm-delete"
                onClick={() => doDelete(confirmDelete.ids)}
                disabled={busy}
                className="px-4 py-2 rounded-lg text-sm bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors disabled:opacity-50"
              >
                {busy ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
