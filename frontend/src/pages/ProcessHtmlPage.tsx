import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FilePlus, FileCode, Play, Trash2, Loader2 } from "lucide-react";

const API_ENDPOINT = "https://your-api-gateway-url.amazonaws.com/prod/process";

type Props = {
  settings: { tag: "span" | "div"; cssClass: string };
};

export default function ProcessHtmlPage({ settings }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawHtml, setRawHtml] = useState<string>("");
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const htmlText = reader.result as string;
      setRawHtml(htmlText);
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

  const handleRun = async () => {
    if (!rawHtml || !selectedFile) return;

    setProcessing(true);
    setError(null);

    try {
      // Send to AWS Lambda for processing
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          html_content: rawHtml,
          filename: selectedFile.name,
          settings: {
            tag: settings.tag,
            cssClass: settings.cssClass,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        // Download the wrapped HTML
        const blob = new Blob([result.wrapped_html], {
          type: "text/html;charset=utf-8",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = selectedFile.name.replace(/\.html?$/i, "") + "-wrapped.html";
        a.click();
        URL.revokeObjectURL(url);

        console.log("✅ Processing complete!");
      } else {
        throw new Error(result.error || "Processing failed");
      }
    } catch (err) {
      console.error("❌ Error:", err);
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setProcessing(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setRawHtml("");
    setError(null);
  };

  return (
    <div className="h-full flex flex-col">
      <h1 className="px-8">Input File</h1>
      <hr className="w-full border-t border-gray-300 mt-4" />

      {/* DROP ZONE */}
      <div
        {...getRootProps({
          className:
            "flex-1 m-8 flex flex-col justify-center items-center rounded-lg border-2 border-dashed cursor-pointer " +
            (isDragActive ? "border-black bg-gray-50" : "border-gray-300"),
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
                {isDragActive ? (
                  "Drop the .html file here"
                ) : (
                  <>
                    Drop a .html file or <u>select file</u>
                  </>
                )}
              </span>
            </>
          )}
        </div>
      </div>

      {/* ERROR MESSAGE */}
      {error && (
        <div className="mx-8 mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">❌ {error}</p>
        </div>
      )}

      <hr className="w-full border-t border-gray-300 mt-4" />

      {/* RUN / CLEAR */}
      <div className="w-full px-8 py-4 flex justify-center sm:justify-start gap-4">
        <button
          onClick={handleRun}
          disabled={!rawHtml || processing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-black text-white hover:bg-neutral-600 active:bg-neutral-600 focus-visible:outline-offset-2 focus-visible:outline-black disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {processing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Play className="w-5 h-5" />
          )}
          <span>{processing ? "Processing..." : "Run"}</span>
        </button>
        <button
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-400 text-slate-700 hover:bg-slate-100 hover:border-slate-500 active:bg-slate-200 focus-visible:outline-offset-2 focus-visible:outline-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleClear}
          disabled={!selectedFile || processing}
        >
          <Trash2 className="w-5 h-5" />
          <span>Clear</span>
        </button>
      </div>
    </div>
  );
}