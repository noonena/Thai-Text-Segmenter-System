
import { useState } from "react";
import { Play, Trash2, Loader2 } from "lucide-react";
import { saveToHistory } from "./HistoryPage";

const API_ENDPOINT = "http://localhost:8000/api/segment";

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
  const [processing, setProcessing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (!inputText.trim()) {
      setError("Please enter some text");
      return;
    }

    setProcessing(true);
    setError(null);
    setOutputHtml("");

    try {
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: inputText.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error ${response.status}`);
      }

      const result = await response.json();
      console.log("API Response:", result);

      // Check for words in response
      if (!result.success || !result.words) {
        throw new Error("No 'words' field in response");
      }

      // Build wrapped HTML from words
      const wrappedHtml = buildWrappedHtml(result.words, tag, cssClass);
      setOutputHtml(wrappedHtml);
      
      // Save to history
      saveToHistory({
        filename: `text-${Date.now()}.html`,
        segments: result.words.length,
        output: wrappedHtml
      });
    } catch (err) {
      console.error("❌ Full Error:", err);
      setError(err instanceof Error ? err.message : "Segmentation failed");
    } finally {
      setProcessing(false);
    }
  };

  const buildWrappedHtml = (
    words: string[],
    wrapTag: string,
    wrapClass: string
  ): string => {
    const thaiRegex = /[\u0E00-\u0E7F]/;

    const wrappedParts = words.map((word) => {
      if (thaiRegex.test(word)) {
        if (wrapClass) {
          return `<wbr><${wrapTag} class="${wrapClass}">${word}</${wrapTag}>`;
        } else {
          return `<wbr><${wrapTag}>${word}</${wrapTag}>`;
        }
      } else {
        return word;
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
          placeholder="สวัสดีครับผมชื่อวินใหม่"
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
              Copy HTML
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
          disabled={!inputText.trim() || processing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg 
                     bg-black text-white hover:bg-neutral-800
                     disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {processing ? (
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
          disabled={!inputText && !outputHtml}
          className="flex items-center gap-2 px-4 py-2 rounded-lg 
                     border border-gray-300 text-gray-700 
                     hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Trash2 className="w-5 h-5" />
          <span>Clear</span>
        </button>
      </div>
    </div>
  );
}