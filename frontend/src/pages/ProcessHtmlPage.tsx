import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FilePlus, FileCode, Play, Trash2, Loader2 } from "lucide-react";
import { saveToHistory } from "./HistoryPage";
import { useProcessing } from "../contexts/ProcessingContext";

/* =======================
   Types
   ======================= */

type Props = {
  settings: {
    tag: "span" | "div";
    cssClass: string;
  };
};

/* =======================
   Component
   ======================= */

export default function ProcessHtmlPage({ settings }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawHtml, setRawHtml] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const { isProcessing, startProcessing, stopProcessing, updateProgress } = useProcessing();

  const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api';

  /* =======================
     Dropzone
     ======================= */

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      setRawHtml(reader.result as string);
      setSelectedFile(file);
      setError(null);
    };
    reader.readAsText(file, "utf-8");
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/html": [".html"] },
    multiple: false,
  });

  /* =======================
     Run processing
     ======================= */

  const handleRun = async () => {
    if (!rawHtml || !selectedFile) return;

    startProcessing("Processing HTML file...");
    setError(null);

    let creep: ReturnType<typeof setInterval> | null = null;
    try {
      updateProgress(25, "Sending HTML to API...");

      let fakeProgress = 25;
      creep = setInterval(() => {
        fakeProgress = Math.min(fakeProgress + 2, 70);
        updateProgress(fakeProgress, "Processing...");
      }, 400);

      const response = await fetch(`${API_BASE}/nlp/process-html`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ html: rawHtml }),
      });

      clearInterval(creep);
      creep = null;
      const data = await response.json();

      if (!data.success || !data.data) {
        throw new Error(data.error || "HTML processing failed");
      }

      updateProgress(75, "Processing results...");

      const result = data.data as any;

      // Count segments (estimate from wrapped HTML)
      const segmentCount = result.segment_count || 
                          (result.wrapped_html?.match(/<wbr>/gi) || []).length;

      console.log("📊 Segment count:", segmentCount);
      updateProgress(90, "Saving results...");
      
      // Save to history
      saveToHistory({
        filename: selectedFile.name,
        segments: segmentCount,
        output: result.wrapped_html || result.processed_html || rawHtml
      });

      updateProgress(95, "Exporting training data...");
      
      // Export to training data (non-blocking)
      fetch(`${API_BASE}/nlp/export-training`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          original_text: rawHtml,
          segmented_words: [], // HTML processing doesn't return word segments
          confidence: 0.95,
          metadata: {
            processing_method: "process_html",
            filename: selectedFile.name,
            segment_count: segmentCount,
            settings: settings
          }
        }),
      }).catch(error => {
        console.warn('Failed to export training data:', error);
        // Don't fail the whole process if training export fails
      });

      // Download processed HTML
      const outputHtml = result.wrapped_html || result.processed_html || rawHtml;
      const blob = new Blob([outputHtml], {
        type: "text/html;charset=utf-8",
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        selectedFile.name.replace(/\.html?$/i, "") + "-wrapped.html";
      a.click();
      URL.revokeObjectURL(url);
      
      updateProgress(100, "Complete!");
      await new Promise(r => setTimeout(r, 600));
    } catch (err) {
      if (creep) clearInterval(creep);
      console.error("❌ Error:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      stopProcessing();
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setRawHtml("");
    setError(null);
  };

  /* =======================
     Render
     ======================= */

  return (
    <div className="h-full flex flex-col">
      <h1 className="px-8">Input File</h1>
      <hr className="w-full border-t border-gray-300 mt-4" />

      {/* DROP ZONE */}
      <div
        {...getRootProps({
          className:
            "flex-1 m-8 flex flex-col justify-center items-center rounded-lg border-2 border-dashed cursor-pointer " +
            (isDragActive
              ? "border-black bg-gray-50"
              : "border-gray-300"),
        })}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center justify-center gap-4">
          {selectedFile ? (
            <>
              <FileCode className="w-20 h-20 text-green-600" />
              <div className="text-center">
                <p className="text-gray-900 font-semibold text-lg">
                  {selectedFile.name}
                </p>
                <p className="text-gray-500 text-sm mt-1">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
                <p className="text-green-600 text-sm mt-2">
                  Click to change or drop another file
                </p>
              </div>
            </>
          ) : (
            <>
              <FilePlus className="w-20 h-20 text-gray-400" />
              <span className="text-gray-500">
                {isDragActive
                  ? "Drop the .html file here"
                  : "Drop a .html file or select file"}
              </span>
            </>
          )}
        </div>
      </div>

      {/* ERROR */}
      {error && (
        <div className="mx-8 mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">❌ {error}</p>
        </div>
      )}

      <hr className="w-full border-t border-gray-300 mt-4" />

      {/* ACTIONS */}
      <div className="w-full px-8 py-4 flex gap-4">
        <button
          onClick={handleRun}
          disabled={!rawHtml || isProcessing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-black text-white disabled:bg-gray-400"
        >
          {isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Play className="w-5 h-5" />
          )}
          {isProcessing ? "Processing..." : "Run"}
        </button>

        <button
          onClick={handleClear}
          disabled={!selectedFile || isProcessing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-400 text-slate-700 disabled:opacity-50"
        >
          <Trash2 className="w-5 h-5" />
          Clear
        </button>
      </div>
    </div>
  );
}