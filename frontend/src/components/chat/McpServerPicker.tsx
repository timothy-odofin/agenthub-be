/**
 * McpServerPicker — mirrors the desktop SearchablePickerPopup / ServerCard /
 * ToolInspectorPopup / ToolCard pattern exactly.
 *
 * Layout:
 *  ┌─────────────────────────────────────────────────────────────┐
 *  │  [picker 460px]          │  [inspector panel 520px]         │
 *  │  search row              │  server icon · name · subtitle   │
 *  │  ─────────────────────── │  search tools                    │
 *  │  GROUP LABEL (n)    ▶    │  ──────────────────────────────  │
 *  │  [card][card]            │  [tool-icon] name                │
 *  │  [card][card]            │              description         │
 *  │  ─────────────────────── │  ──────────────────────────────  │
 *  │  n selected  [Clear][OK] │  n tools total                   │
 *  └─────────────────────────────────────────────────────────────┘
 */
import { useEffect, useRef, useState } from "react";
import { Eye, Search, Wrench, X } from "lucide-react";
import type { McpGroupInfo, McpServerInfo, McpToolInfo } from "@/types";

interface McpServerPickerProps {
  groups: McpGroupInfo[];
  selected: Set<string>;
  onApply: (ids: Set<string>) => void;
  onClose: () => void;
  anchorRef: React.RefObject<HTMLButtonElement | null>;
}

// ─────────────────────────────────────────────────────────────────────────────
// ToolCard  — mirrors desktop ToolCard.java
//   icon-container (muted bg) | name (bold) + description (wrapped)
// ─────────────────────────────────────────────────────────────────────────────

function ToolCard({ tool }: { tool: McpToolInfo }) {
  return (
    <div className="flex flex-col px-3.5 py-2.5 rounded-[10px] border border-gray-100 bg-white hover:bg-gray-50 transition-colors">
      <p className="text-[12.5px] font-semibold text-gray-800 leading-tight">{tool.name}</p>
      {tool.description && (
        <p className="text-[11px] text-gray-500 mt-0.5 leading-snug whitespace-normal break-words">
          {tool.description}
        </p>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ToolInspectorPanel — mirrors desktop ToolInspectorPopup.java
//   header: server icon + name + subtitle + close
//   search, scrollable ToolCard list, footer "n tools total"
// ─────────────────────────────────────────────────────────────────────────────

function ToolInspectorPanel({
  server,
  onClose,
}: {
  server: McpServerInfo;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");

  const filtered = server.tools.filter(
    (t) =>
      t.name.toLowerCase().includes(query.toLowerCase()) ||
      (t.description ?? "").toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="flex flex-col w-[520px] max-h-[480px] bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3.5 border-b border-gray-100">
        <div className="flex-shrink-0 w-[36px] h-[36px] rounded-[10px] bg-blue-50 flex items-center justify-center">
          <Wrench className="w-[18px] h-[18px] text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[14px] font-semibold text-gray-800 leading-tight">{server.name}</p>
          <p className="text-[11px] text-gray-400 mt-0.5">{server.tool_count} tools available</p>
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-700"
          title="Close inspector"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Search */}
      <div className="px-4 pt-3 pb-2">
        <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-[10px] px-3 py-2 focus-within:border-blue-400 transition-colors">
          <Search className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search tools..."
            className="flex-1 text-[13px] bg-transparent outline-none text-gray-700 placeholder:text-gray-400"
          />
          {query && (
            <button onClick={() => setQuery("")} className="text-gray-400 hover:text-gray-600">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Tool list */}
      <div className="flex-1 overflow-y-auto px-4 pb-2">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-gray-400">
            <Search className="w-7 h-7 mb-2 opacity-40" />
            <p className="text-xs">No tools match "{query}"</p>
          </div>
        ) : (
          <div className="flex flex-col gap-1.5 py-1">
            {filtered.map((tool) => (
              <ToolCard key={tool.name} tool={tool} />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center px-4 py-2.5 border-t border-gray-100">
        <span className="text-[12px] text-gray-400">
          {server.tool_count} tool{server.tool_count !== 1 ? "s" : ""} total
        </span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ServerCard — mirrors desktop ServerCard.java
//   icon-container (accent bg) | name + desc (wrapped) + tool-count
//   right: check badge (selected) + eye/inspect button
// ─────────────────────────────────────────────────────────────────────────────

function ServerCard({
  server,
  selected,
  onToggle,
  onInspect,
}: {
  server: McpServerInfo;
  selected: boolean;
  onToggle: () => void;
  onInspect: (s: McpServerInfo) => void;
}) {
  return (
    <div
      onClick={onToggle}
      className={`relative flex items-start gap-3 px-3.5 py-3 rounded-xl border cursor-pointer transition-all select-none ${
        selected
          ? "border-blue-500 bg-blue-50"
          : "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/30"
      }`}
    >
      {/* icon container */}
      <div className="flex-shrink-0 w-[36px] h-[36px] rounded-[10px] bg-blue-50 flex items-center justify-center">
        <Wrench className="w-5 h-5 text-blue-600" />
      </div>

      {/* text */}
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-semibold text-gray-800 leading-tight">{server.name}</p>
        <p className="text-[11.5px] text-gray-500 mt-0.5 leading-snug whitespace-normal break-words">
          {server.description}
        </p>
        <span className="inline-block mt-1.5 text-[11px] text-gray-400">
          {server.tool_count} tool{server.tool_count !== 1 ? "s" : ""}
        </span>
      </div>

      {/* right column: check badge + inspect button */}
      <div className="flex flex-col items-center gap-1.5 flex-shrink-0">
        <div
          className={`w-[22px] h-[22px] rounded-full bg-blue-600 flex items-center justify-center transition-all ${
            selected ? "opacity-100 scale-100" : "opacity-0 scale-75 pointer-events-none"
          }`}
        >
          <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
            <path
              d="M2 6l3 3 5-5"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {server.tools.length > 0 && (
          <button
            onClick={(e) => { e.stopPropagation(); onInspect(server); }}
            title="View tools"
            className="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// GroupHeader — mirrors desktop GroupHeader.java
// ─────────────────────────────────────────────────────────────────────────────

function GroupHeader({
  label,
  count,
  expanded,
  onToggle,
}: {
  label: string;
  count: number;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className="flex items-center gap-2 w-full text-left py-2 px-1 group"
    >
      <svg
        className={`w-3 h-3 text-gray-400 flex-shrink-0 transition-transform ${expanded ? "rotate-90" : ""}`}
        viewBox="0 0 12 12"
        fill="none"
      >
        <path
          d="M4 2l4 4-4 4"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">
        {label}
      </span>
      <span className="text-[11px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full leading-none">
        {count}
      </span>
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// McpServerPicker — mirrors desktop SearchablePickerPopup.java
//   picker (460px) + inspector panel (520px) side-by-side
// ─────────────────────────────────────────────────────────────────────────────

export default function McpServerPicker({
  groups,
  selected,
  onApply,
  onClose,
  anchorRef,
}: McpServerPickerProps) {
  const [draft, setDraft] = useState<Set<string>>(new Set(selected));
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [inspecting, setInspecting] = useState<McpServerInfo | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click — both panels count as inside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node) &&
        anchorRef.current &&
        !anchorRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose, anchorRef]);

  const toggleServer = (id: string) => {
    setDraft((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleGroup = (label: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(label) ? next.delete(label) : next.add(label);
      return next;
    });
  };

  const handleApply = () => {
    onApply(draft);
    onClose();
  };

  const lowerQuery = query.toLowerCase();

  const filteredGroups = groups
    .map((g) => ({
      ...g,
      servers: g.servers.filter(
        (s) =>
          s.name.toLowerCase().includes(lowerQuery) ||
          s.description.toLowerCase().includes(lowerQuery) ||
          s.tools.some((t) => t.name.toLowerCase().includes(lowerQuery))
      ),
    }))
    .filter((g) => g.servers.length > 0);

  const totalSelected = draft.size;

  return (
    /* Outer wrapper — flex row: picker always visible, inspector slides in to the right */
    <div
      ref={containerRef}
      className="absolute bottom-full left-0 mb-2 z-[100] flex flex-row items-end gap-2"
    >
      {/* ── Picker popup (460px) ── */}
      <div className="flex flex-col w-[460px] max-h-[480px] bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden">

        {/* Search row */}
        <div className="px-4 pt-4 pb-3 border-b border-gray-100">
          <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-[10px] px-3 py-2 focus-within:border-blue-400 transition-colors">
            <Search className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search servers..."
              className="flex-1 text-[13px] bg-transparent outline-none text-gray-700 placeholder:text-gray-400"
              autoFocus
            />
            {query && (
              <button onClick={() => setQuery("")} className="text-gray-400 hover:text-gray-600">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Groups + cards */}
        <div className="flex-1 overflow-y-auto px-4 py-2">
          {filteredGroups.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-gray-400">
              <Search className="w-8 h-8 mb-2 opacity-40" />
              <p className="text-sm">No servers match "{query}"</p>
            </div>
          ) : (
            filteredGroups.map((group) => (
              <div key={group.category} className="mb-3">
                <GroupHeader
                  label={group.label}
                  count={group.servers.length}
                  expanded={!collapsed.has(group.label)}
                  onToggle={() => toggleGroup(group.label)}
                />
                {!collapsed.has(group.label) && (
                  <div className="grid grid-cols-2 gap-2 mt-1 pl-4">
                    {group.servers.map((server) => (
                      <ServerCard
                        key={server.id}
                        server={server}
                        selected={draft.has(server.id)}
                        onToggle={() => toggleServer(server.id)}
                        onInspect={(s) =>
                          setInspecting((prev) => (prev?.id === s.id ? null : s))
                        }
                      />
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-gray-50/60">
          <span className="text-[12px] text-gray-400">
            {totalSelected === 0
              ? "0 servers selected"
              : `${totalSelected} server${totalSelected !== 1 ? "s" : ""} selected`}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDraft(new Set())}
              className="text-[12px] text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-[10px] border border-gray-200 hover:bg-gray-100 transition-all"
            >
              Clear
            </button>
            <button
              onClick={handleApply}
              className="text-[12px] font-bold text-white bg-blue-600 hover:bg-blue-700 px-4 py-1.5 rounded-[10px] transition-all"
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {/* ── Tool Inspector Panel — appears to the right when eye is clicked ── */}
      {inspecting && (
        <ToolInspectorPanel
          server={inspecting}
          onClose={() => setInspecting(null)}
        />
      )}
    </div>
  );
}
