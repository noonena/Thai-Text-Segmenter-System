import { useState, useEffect } from "react";
import { TrendingUp, AlertCircle, BarChart3, Info, RefreshCw } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const NLP_API = import.meta.env.VITE_NLP_API ?? "http://localhost:8000/api";

interface StageMetrics { precision: number; recall: number; f1: number }
interface PosTag { p: number; r: number; f1: number; n: number }
interface EvalResults {
  timestamp: string;
  sentences_evaluated: number;
  mtu: StageMetrics & { label_accuracy: number };
  syllable: StageMetrics;
  word_seg: StageMetrics & { errors: { sentence: string; gold: string[]; pred: string[] }[] };
  pos: { accuracy: number; total_tags: number; per_tag: Record<string, PosTag> };
  weakest_stage: string;
  is_running: boolean;
}

const pct = (v: number) => (v * 100).toFixed(1);

function StatisticsPage() {
  const [activeSection, setActiveSection] = useState<"overview" | "segmentation" | "pos">("overview");
  const [data, setData]     = useState<EvalResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${NLP_API}/stats`);
      if (!res.ok) {
        if (res.status === 404) { setError("not_found"); return; }
        throw new Error(`HTTP ${res.status}`);
      }
      setData(await res.json());
      setError(null);
    } catch (e) {
      setError("fetch_failed");
    } finally {
      setLoading(false);
    }
  };

  const triggerEval = async () => {
    setTriggering(true);
    try {
      await fetch(`${NLP_API}/stats/evaluate`, { method: "POST" });
      // Poll every 5 s until is_running becomes false
      const poll = setInterval(async () => {
        await fetchStats();
        if (data && !data.is_running) clearInterval(poll);
      }, 5000);
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => { fetchStats(); }, []);

  // ── Loading / error states ───────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center h-40 text-gray-500 text-sm">
      Loading evaluation results…
    </div>
  );

  if (error === "not_found" || !data) return (
    <div className="flex flex-col items-center justify-center h-48 gap-4">
      <p className="text-gray-600 text-sm">No evaluation results yet.</p>
      <button
        onClick={triggerEval}
        disabled={triggering}
        className="flex items-center gap-2 px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 disabled:opacity-50"
      >
        <RefreshCw className={`w-4 h-4 ${triggering ? "animate-spin" : ""}`} />
        Run Evaluation (~1 min)
      </button>
    </div>
  );

  if (error === "fetch_failed") return (
    <div className="flex items-center justify-center h-40 text-red-500 text-sm">
      Could not reach backend. Is the server running?
    </div>
  );

  // ── Derived chart data ────────────────────────────────────
  const stageChartData = [
    { name: "MTU",      P: parseFloat(pct(data.mtu.precision)),      R: parseFloat(pct(data.mtu.recall)),      F1: parseFloat(pct(data.mtu.f1)) },
    { name: "Syllable", P: parseFloat(pct(data.syllable.precision)),  R: parseFloat(pct(data.syllable.recall)), F1: parseFloat(pct(data.syllable.f1)) },
    { name: "Word Seg", P: parseFloat(pct(data.word_seg.precision)),  R: parseFloat(pct(data.word_seg.recall)), F1: parseFloat(pct(data.word_seg.f1)) },
    { name: "POS",      P: null,                                       R: null,                                  F1: parseFloat(pct(data.pos.accuracy)) },
  ];

  const topPosTags = Object.entries(data.pos.per_tag)
    .sort((a, b) => b[1].n - a[1].n)
    .slice(0, 10);

  const posChartData = topPosTags.map(([tag, v]) => ({
    tag,
    F1: parseFloat(pct(v.f1)),
    n: v.n,
  }));

  return (
    <div className="h-full overflow-auto pb-6 space-y-6">

      {/* Sub-nav */}
      <div className="flex gap-2 bg-gray-100 rounded-lg p-1">
        {(["overview", "segmentation", "pos"] as const).map(s => (
          <button key={s} onClick={() => setActiveSection(s)}
            className={"flex-1 h-9 rounded-md text-sm font-medium transition " +
              (activeSection === s ? "bg-black text-white" : "bg-transparent text-gray-800 hover:bg-gray-200")}>
            {s === "overview" ? "Overview" : s === "segmentation" ? "Word segmentation" : "POS tagging"}
          </button>
        ))}
      </div>

      {/* Refresh bar */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Last evaluated: {new Date(data.timestamp).toLocaleString()}  ·  {data.sentences_evaluated} sentences</span>
        <button onClick={() => { triggerEval(); }}
          disabled={triggering || data.is_running}
          className="flex items-center gap-1 px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50">
          <RefreshCw className={`w-3 h-3 ${(triggering || data.is_running) ? "animate-spin" : ""}`} />
          {data.is_running ? "Running…" : "Re-evaluate"}
        </button>
      </div>

      {/* ── OVERVIEW ── */}
      {activeSection === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">Word Seg F1</h3>
                <div className="p-2 rounded-full border border-gray-200"><BarChart3 className="w-4 h-4 text-gray-700" /></div>
              </div>
              <p className="text-3xl font-semibold text-gray-900">{pct(data.word_seg.f1)}%</p>
              <p className="text-xs text-gray-500 mt-1">Main metric (LST20 test)</p>
              <p className="text-xs text-gray-600 mt-4">
                P {pct(data.word_seg.precision)}% · R {pct(data.word_seg.recall)}%
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">POS Accuracy</h3>
                <div className="p-2 rounded-full border border-gray-200"><TrendingUp className="w-4 h-4 text-gray-700" /></div>
              </div>
              <p className="text-3xl font-semibold text-gray-900">{pct(data.pos.accuracy)}%</p>
              <p className="text-xs text-gray-500 mt-1">On gold-segmented words</p>
              <p className="text-xs text-gray-600 mt-4">{data.pos.total_tags.toLocaleString()} tags evaluated</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">Weakest Stage</h3>
                <div className="p-2 rounded-full border border-gray-200"><Info className="w-4 h-4 text-gray-700" /></div>
              </div>
              <p className="text-3xl font-semibold text-gray-900">{data.weakest_stage}</p>
              <p className="text-xs text-gray-500 mt-1">Needs most improvement</p>
              <p className="text-xs text-gray-600 mt-4">{data.sentences_evaluated} test sentences</p>
            </div>
          </div>

          {/* Stage comparison */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">All Stages — Precision / Recall / F1</h2>
            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-xs font-semibold text-gray-600">
                    <th className="px-4 py-2 border-b border-gray-200 text-left">Stage</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">Precision</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">Recall</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">F1 / Accuracy</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: "MTU",      p: data.mtu.precision,      r: data.mtu.recall,      f: data.mtu.f1 },
                    { label: "Syllable", p: data.syllable.precision,  r: data.syllable.recall, f: data.syllable.f1 },
                    { label: "Word Seg", p: data.word_seg.precision,  r: data.word_seg.recall, f: data.word_seg.f1 },
                    { label: "POS",      p: null,                      r: null,                 f: data.pos.accuracy },
                  ].map(row => (
                    <tr key={row.label} className="hover:bg-gray-50">
                      <td className="px-4 py-2 border-b border-gray-100 font-semibold">{row.label}</td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center">{row.p !== null ? `${pct(row.p)}%` : "—"}</td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center">{row.r !== null ? `${pct(row.r)}%` : "—"}</td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                          row.f >= 0.9 ? "bg-green-100 text-green-700" :
                          row.f >= 0.7 ? "bg-yellow-100 text-yellow-700" :
                          "bg-red-100 text-red-700"}`}>
                          {pct(row.f)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={stageChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="P"  name="Precision" fill="#6b7280" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="R"  name="Recall"    fill="#374151" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="F1" name="F1"        fill="#111827" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ── WORD SEGMENTATION ── */}
      {activeSection === "segmentation" && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Word Segmentation Metrics</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              {[
                { label: "Precision", val: pct(data.word_seg.precision) },
                { label: "Recall",    val: pct(data.word_seg.recall) },
                { label: "F1",        val: pct(data.word_seg.f1) },
              ].map(r => (
                <div key={r.label} className="rounded-lg bg-gray-50 px-4 py-3 text-center">
                  <p className="text-2xl font-semibold text-gray-900">{r.val}%</p>
                  <p className="text-xs text-gray-500 mt-1">{r.label}</p>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Low recall ({pct(data.word_seg.recall)}%) indicates over-merging — the segmenter joins words that should be separate.
            </p>
          </div>

          {/* Error examples */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="border-b border-gray-200 px-6 py-3">
              <h3 className="text-sm font-semibold text-gray-900">Real Error Examples (from LST20 test)</h3>
            </div>
            <div className="p-4 space-y-3">
              {data.word_seg.errors.map((ex, i) => (
                <div key={i} className="rounded-lg bg-gray-50 p-3 text-xs space-y-1">
                  <p className="text-gray-500">Input: <span className="text-gray-800 font-medium">{ex.sentence}</span></p>
                  <p className="text-green-700">Gold: {ex.gold.join(" | ")}</p>
                  <p className="text-red-600">Pred: {ex.pred.join(" | ")}</p>
                </div>
              ))}
            </div>
          </div>

          {/* MTU & Syllable detail */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Upstream Stage Metrics</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-xs font-semibold text-gray-600">
                    <th className="px-4 py-2 border-b border-gray-200 text-left">Stage</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">Precision</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">Recall</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">F1</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-100 font-semibold">MTU boundary</td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">{pct(data.mtu.precision)}%</td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">{pct(data.mtu.recall)}%</td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">{pct(data.mtu.f1)}%</td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-100 font-semibold">Syllable boundary</td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">{pct(data.syllable.precision)}%</td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">{pct(data.syllable.recall)}%</td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">{pct(data.syllable.f1)}%</td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-100 text-gray-500 text-xs" colSpan={4}>
                      MTU label accuracy: {pct(data.mtu.label_accuracy)}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── POS TAGGING ── */}
      {activeSection === "pos" && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-1">Overall POS Accuracy</h3>
            <p className="text-4xl font-semibold text-gray-900">{pct(data.pos.accuracy)}%</p>
            <p className="text-xs text-gray-500 mt-1">Evaluated on gold word segmentation · {data.pos.total_tags.toLocaleString()} tags</p>
          </div>

          {/* Per-tag table */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="border-b border-gray-200 px-6 py-3">
              <h3 className="text-sm font-semibold text-gray-900">Per-Tag F1 (by frequency)</h3>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-xs font-semibold text-gray-600">
                    <th className="px-4 py-2 border-b border-gray-200 text-left">Tag</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">Precision</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">Recall</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">F1</th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {topPosTags.map(([tag, v]) => (
                    <tr key={tag} className="hover:bg-gray-50">
                      <td className="px-4 py-2 border-b border-gray-100 font-semibold">{tag}</td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center">{pct(v.p)}%</td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center">{pct(v.r)}%</td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                          v.f1 >= 0.9 ? "bg-green-100 text-green-700" :
                          v.f1 >= 0.7 ? "bg-yellow-100 text-yellow-700" :
                          "bg-red-100 text-red-700"}`}>
                          {pct(v.f1)}%
                        </span>
                      </td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center text-gray-500">{v.n}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Per-Tag F1 Chart</h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={posChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="tag" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Bar dataKey="F1" fill="#111827" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Note */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
            <div className="flex gap-3">
              <AlertCircle className="w-4 h-4 mt-0.5 text-blue-600 shrink-0" />
              <p className="text-sm text-gray-700">
                POS is evaluated on <strong>gold word segmentation</strong> to isolate tagging errors from segmentation errors.
                Real-world POS accuracy will be lower because segmentation errors cascade into the POS stage.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StatisticsPage;
