import { useState } from "react";
import { Play, Trash2, Loader2 } from "lucide-react";
import { saveToHistory } from "./HistoryPage";
import { useProcessing } from "../contexts/ProcessingContext";

type Props = {
  settings?: {  // ← Made optional
    tag: "span" | "div";
    cssClass: string;
  };
};

export default function ProcessTextPage({ settings }: Props) {
  // Use default settings if not provided
  const tag = settings?.tag || "span";
  const cssClass = settings?.cssClass || "";

  const [inputText, setInputText] = useState<string>("");
  const [outputHtml, setOutputHtml] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const { isProcessing, startProcessing, stopProcessing, updateProgress } = useProcessing();

  const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';

const handleRun = async () => {
    if (!inputText.trim()) {
      setError("Please enter some text");
      return;
    }

    startProcessing("Initializing text segmentation...");
    setError(null);
    setOutputHtml("");

    let creep: ReturnType<typeof setInterval> | null = null;
    try {
      updateProgress(25, "Sending text to API...");

      let fakeProgress = 25;
      creep = setInterval(() => {
        fakeProgress = Math.min(fakeProgress + 2, 70);
        updateProgress(fakeProgress, "Processing...");
      }, 400);

      const response = await fetch(`${API_BASE}/nlp/text-process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ text: inputText.trim() }),
      });

      clearInterval(creep);
      creep = null;
      const data = await response.json();

      if (!data.success || !data.data) {
        throw new Error(data.error || "Segmentation failed");
      }

      updateProgress(75, "Processing segmentation results...");

      if (!data.data.words) {
        throw new Error("No 'words' field in response");
      }

      updateProgress(90, "Building wrapped HTML...");
      const wrappedHtml = buildWrappedHtml(data.data.words, tag, cssClass);
      setOutputHtml(wrappedHtml);

      fetch(`${API_BASE}/nlp/export-training`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          original_text: inputText.trim(),
          segmented_words: data.data.words,
          confidence: data.data.confidence || 0.95,
          metadata: { processing_method: "segment_text", tag, css_class: cssClass }
        }),
      }).catch(() => {});

      updateProgress(100, "Complete!");
      await new Promise(r => setTimeout(r, 600));
    } catch (err) {
      if (creep) clearInterval(creep);
      console.error("❌ Full Error:", err);
      setError(err instanceof Error ? err.message : "Segmentation failed");
    } finally {
      stopProcessing();
    }
  };

  const escapeHtml = (str: string): string =>
    str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  const buildWrappedHtml = (
    words: string[],
    wrapTag: string,
    wrapClass: string
  ): string => {
    const thaiRegex = /[\u0E00-\u0E7F]/;
    const safeTag = wrapTag === "div" ? "div" : "span";
    const safeClass = escapeHtml(wrapClass);

    const wrappedParts = words.map((word) => {
      const safeWord = escapeHtml(word);
      if (thaiRegex.test(word)) {
        if (safeClass) {
          return `<wbr><${safeTag} class="${safeClass}">${safeWord}</${safeTag}>`;
        } else {
          return `<wbr><${safeTag}>${safeWord}</${safeTag}>`;
        }
      } else {
        return safeWord;
      }
    });

    return wrappedParts.join("");
  };

  const handleClear = () => {
    setInputText("");
    setOutputHtml("");
    setError(null);
  };

  return (
    <div className="h-full flex flex-col">
      <h1 className="px-8 text-xl font-medium">Input Text</h1>
      <hr className="w-full border-t border-gray-300 mt-4" />

      {/* Input Area */}
      <div className="flex-1 m-8 flex flex-col">
        <label className="block text-sm text-gray-600 mb-2">
          Enter Thai Text
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          className="w-full flex-1 p-3 border border-gray-300 rounded-md 
                     focus:outline-none focus:ring-2 focus:ring-black 
                     focus:border-transparent resize-none"
          placeholder="สวัสดีค่า อยากกินชานมไข่มุกมากเลยค่ะ"
        />
      </div>

      {/* Output Area */}
      {outputHtml && (
        <div className="mx-8 mb-4 p-4 bg-gray-50 border border-gray-200 rounded-md">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              Wrapped Output (Tag: &lt;{tag}&gt;{cssClass && `, Class: "${cssClass}"`})
            </label>
            <button
              onClick={() => {
                navigator.clipboard.writeText(outputHtml);
              }}
              className="text-xs px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded"
            >
              Copy Text
            </button>
          </div>
          
          {/* HTML Code */}
          <div className="mb-3 p-2 bg-black text-green-400 rounded font-mono text-xs overflow-auto max-h-32">
            <pre className="whitespace-pre-wrap break-all">{outputHtml}</pre>
          </div>

          {/* Visual Preview */}
          <div className="p-2 bg-white border rounded">
            <div dangerouslySetInnerHTML={{ __html: outputHtml }} />
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mx-8 mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
          <span className="text-red-600">✕</span>
          <span className="text-red-800 text-sm">{error}</span>
        </div>
      )}

      <hr className="w-full border-t border-gray-300" />

      {/* Action Buttons */}
      <div className="w-full px-8 py-4 flex gap-4">
        <button
          onClick={handleRun}
          disabled={!inputText.trim() || isProcessing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg 
                     bg-black text-white enabled:hover:bg-neutral-800
                     disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Run</span>
            </>
          )}
        </button>

        <button
          onClick={handleClear}
          disabled={!inputText && !outputHtml || isProcessing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg 
                     border border-gray-300 text-gray-700 
                     enabled:hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Trash2 className="w-5 h-5" />
          <span>Clear</span>
        </button>
      </div>
    </div>
  );
}