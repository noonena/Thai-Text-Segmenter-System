import { useState } from "react";
import ProcessHtmlPage from "./pages/ProcessHtmlPage";
import ProcessTextPage from "./pages/ProcessTextPage";
import HistoryPage from "./pages/HistoryPage";
import StatisticsPage from "./pages/StatisticsPage";
import SettingPage from "./pages/SettingPage";
import { Settings, FileText, History, ChartLine } from "lucide-react";
import { ProcessingProvider } from "./contexts/ProcessingContext";
import { ProcessingModal } from "./components/ProcessingModal";
import { ApiErrorBoundary } from "./components/ApiErrorBoundary";
import { BunnyLogo } from "./components/BunnyLogo";

type Page = "process" | "history" | "stats";
type InputMode = "html" | "text";
type InputActive = "active" | "inactive";

function AppContent() {
  const [page, setPage] = useState<Page>("process");
  const [inputMode, setInputMode] = useState<InputMode>("html");
  const [inputActive, setInputActive] = useState<InputActive>("active");
  const [open, setOpen] = useState(false);
  const [settings, setSettings] = useState({
    tag: "span" as "span" | "div",
    cssClass: ""
  });

  const handleApplySettings = (newSettings: { tag: "span" | "div"; cssClass: string }) => {
    setSettings(newSettings);
    console.log("Applied settings:", newSettings);
  };

  return (
    <div>
      <div className="h-screen">
        <div className="max-w-[95%] mx-auto pt-[2.5%] flex flex-col h-full">
          <div className="h-[12vh] bg-white rounded-lg shadow-md px-8 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <BunnyLogo size={60} />
            <div className="flex flex-col gap-2">
              <h1 className="text-2xl font-semibold">Thai text segmenter</h1>
            </div>
            </div>
            <div className="flex items-center gap-4">
              <button onClick={() => setOpen(true)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors focus:outline-none">
                <Settings className="w-6 h-6" />
              </button>
            </div>
            {open && (
              <SettingPage 
                onClose={() => setOpen(false)}
                onApply={handleApplySettings}
              />
            )}
          </div>

          <div className="h-full pt-[2%] flex-1">
            <div className="h-full bg-white rounded-t-lg shadow-md flex flex-col">
<div className="w-full flex flex-col bg-(--light-grayish) rounded-t-lg sm:flex-row justify-between py-0 sm:h-[50px]">
                <div className="flex w-full justify-between sm:justify-start h-full flex-1">
                  <button
                    onClick={() => {
                      setPage("process");
                      setInputActive("active");
                    }}
                    className={
                      "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                      (page === "process"
                        ? "bg-black text-white"
                        : "bg-transparent text-black")
                    }
                  >
                    <span className="flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      <span>Process</span>
                    </span>
                  </button>

                  <button
                    onClick={() => {
                      setPage("history");
                      setInputActive("inactive");
                    }}
                    className={
                      "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                      (page === "history"
                        ? "bg-black text-white"
                        : "bg-transparent text-black")
                    }
                  >
                    <span className="flex items-center gap-2">
                      <History className="w-4 h-4" />
                      <span>History</span>
                    </span>
                  </button>

                  <button
                    onClick={() => {
                      setPage("stats");
                      setInputActive("inactive");
                    }}
                    className={
                      "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                      (page === "stats"
                        ? "bg-black text-white"
                        : "bg-transparent text-black")
                    }
                  >
                    <span className="flex items-center gap-2">
                      <ChartLine className="w-4 h-4" />
                      <span>Statistics</span>
                    </span>
                  </button>
                </div>
                {inputActive === "active" && (
                  <div className="flex w-full sm:w-[15%] h-9 sm:h-full rounded-lg border-2 border-black mt-1 sm:mt-0">
                    <button
                      onClick={() => setInputMode("html")}
                      className={
                        "flex-1 text-center " +
                        (inputMode === "html"
                          ? "bg-black text-white rounded-r-lg rounded-l-sm"
                          : "bg-transparent text-black")
                      }
                    >
                      HTML
                    </button>
                    <button
                      onClick={() => setInputMode("text")}
                      className={
                        "flex-1 text-center " +
                        (inputMode === "text"
                          ? "bg-black text-white rounded-l-lg rounded-r-sm"
                          : "bg-transparent text-black")
                      }
                    >
                      Text
                    </button>
                  </div>
                )}
                  </div>
                 <div className="mt-4 flex-1 bg-white">
                   <ApiErrorBoundary>
                      {page === "process" && inputMode === "html" && (
                        <ProcessHtmlPage settings={settings} />
                      )}
                      {page === "process" && inputMode === "text" && <ProcessTextPage settings={settings} />}
                      {page === "history" && <HistoryPage />}
                      {page === "stats" && <StatisticsPage />}
                    </ApiErrorBoundary>
                  </div>
              </div>
           </div>
         </div>
       </div>
     </div>
   );
  }

function App() {
  return (
    <ProcessingProvider>
      <AppContent />
      <ProcessingModal />
    </ProcessingProvider>
  );
}

export default App;
