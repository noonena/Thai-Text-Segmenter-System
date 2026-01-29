import { Search, Download } from "lucide-react";

type HistoryItem = {
  filename: string;
  createdAt: string;   // e.g. "20 Nov 2024, 14:30"
  segments: number;    // e.g. 187
  output: string;      // processed HTML as plain text
};

// Card component
function HistoryCard({ item }: { item: HistoryItem }) {
  return (
    <div className="mt-4 rounded-xl border border-[var(--light-gray)] bg-white px-5 py-4 shadow-sm">
      {/* Top row: name + download */}
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

        <button className="flex items-center gap-2 rounded-lg bg-[var(--green,#98c38b)] px-4 py-2 text-xs font-medium text-white">
          <Download className="h-4 w-4" />
          Download
        </button>
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

// Example data
const exampleItem: HistoryItem = {
  filename: "Product-page.html",
  createdAt: "20 Nov 2024, 14:30",
  segments: 187,
  output: "<html><body><h1><wbr>สินค้า<wbr>แนะนำ</h1><p>…</p></body></html>",
};

export default function HistoryPage() {
  return (
    <div className="px-8 py-6">
      {/* Search bar */}
      <div className="flex items-center gap-3 h-[35px] border-2 border-[var(--grayish)] rounded-lg pl-4">
        <Search className="w-5 h-5 text-[var(--grayish)]" />
        <input
          type="text"
          placeholder="Search files..."
          className="w-full text-[var(--grayish)] bg-transparent focus:outline-none focus:text-black placeholder:text-[var(--grayish)]"
        />
      </div>

      {/* History card */}
      <HistoryCard item={exampleItem} />
    </div>
  );
}
