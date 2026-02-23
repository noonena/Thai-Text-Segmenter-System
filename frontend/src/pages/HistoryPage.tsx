import { Search, Download } from "lucide-react";
import { useState, useEffect } from "react";

type HistoryItem = {
  id: string;
  filename: string;
  createdAt: string;   // e.g. "20 Nov 2024, 14:30"
  segments: number;    // e.g. 187
  output: string;      // processed HTML as plain text
};

// Storage utilities
const STORAGE_KEY = "thai-text-history";

const getHistory = (): HistoryItem[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

const saveToHistory = (item: Omit<HistoryItem, "id" | "createdAt">) => {
  const history = getHistory();
  const newItem: HistoryItem = {
    ...item,
    id: Date.now().toString(),
    createdAt: new Date().toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    }).replace(/,/g, "")
  };
  
  history.unshift(newItem); // Add to beginning
  if (history.length > 50) history.pop(); // Keep max 50 items
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  return newItem;
};

const removeFromHistory = (id: string) => {
  const history = getHistory();
  const filtered = history.filter(item => item.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
};

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
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  const handleDelete = (id: string) => {
    removeFromHistory(id);
    setHistory(prev => prev.filter(item => item.id !== id));
  };

  const filteredHistory = history.filter(item =>
    item.filename.toLowerCase().includes(searchQuery.toLowerCase())
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

// Export utilities for other components
export { saveToHistory, getHistory, removeFromHistory };
