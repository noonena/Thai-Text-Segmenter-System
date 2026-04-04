import { Search, Download } from "lucide-react";
import { useMemo, useState } from "react";
import { getHistory, removeFromHistory, type HistoryItem } from "./historyStorage";

// Card component
function HistoryCard({ item, onDelete }: { item: HistoryItem; onDelete: (id: string) => void }) {
  const handleDownload = () => {
    const blob = new Blob([item.output], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${item.filename}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mt-4 rounded-xl border border-[var(--light-gray)] bg-white px-5 py-4 shadow-sm">
      {/* Top row: name + actions */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold">{item.filename}</h2>
          <div className="mt-1 flex items-center gap-3 text-xs text-[var(--grayish)]">
            <span>{item.createdAt}</span>
            <span className="inline-flex items-center rounded-full bg-[var(--pill-bg,#e5f5d6)] px-2 py-0.5 text-[10px] font-medium text-black">
              {item.segments} segments
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={handleDownload}
            className="flex items-center gap-2 rounded-lg bg-[var(--green,#98c38b)] px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-[var(--green-dark,#387723)]"
          >
            <Download className="h-4 w-4" />
            Download
          </button>
          <button
            onClick={() => onDelete(item.id)}
            className="rounded-lg bg-red-400 px-3 py-2 text-xs font-medium text-white hover:bg-red-600 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Processed output */}
      <div className="mt-4 text-[11px]">
        <div className="mb-1 text-[10px] font-semibold tracking-wide text-[var(--grayish)]">
          PROCESSED OUTPUT
        </div>
        <div className="max-h-24 overflow-y-auto rounded-md bg-[#f7f7f7] px-3 py-2 font-mono text-[11px] leading-snug">
          {item.output}
        </div>
      </div>
    </div>
  );
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>(() => getHistory());
  const [searchQuery, setSearchQuery] = useState("");

  const handleDelete = (id: string) => {
    removeFromHistory(id);
    setHistory(prev => prev.filter(item => item.id !== id));
  };

  const filteredHistory = useMemo(
    () => history.filter((item) => item.filename.toLowerCase().includes(searchQuery.toLowerCase())),
    [history, searchQuery],
  );

  return (
    <div className="px-8 py-6">
      {/* Search bar */}
      <div className="flex items-center gap-3 h-[35px] border-2 border-[var(--grayish)] rounded-lg pl-4">
        <Search className="w-5 h-5 text-[var(--grayish)]" />
        <input
          type="text"
          placeholder="Search files..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full text-[var(--grayish)] bg-transparent focus:outline-none focus:text-black placeholder:text-[var(--grayish)]"
        />
      </div>

      {/* History cards */}
      {filteredHistory.length === 0 ? (
        <div className="mt-8 text-center text-[var(--grayish)]">
          {searchQuery ? "No matching files found" : "No history available"}
        </div>
      ) : (
        filteredHistory.map(item => (
          <HistoryCard 
            key={item.id} 
            item={item} 
            onDelete={handleDelete}
          />
        ))
      )}
    </div>
  );
}
