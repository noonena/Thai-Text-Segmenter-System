import { useState } from "react";
import {
  TrendingUp,
  AlertCircle,
  BarChart3,
  Info,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function StatisticsPage() {
  const [activeSection, setActiveSection] = useState<"overview" | "segmentation" | "pos">("overview");

  // ── Data ──────────────────────────────────────────────────────
  const formalResults = {
    baseline: { P: 92.5, R: 90.3, F: 91.4 },
    proposed: { P: 95.8, R: 94.2, F: 95.0 },
  };

  const informalResults = {
    baseline: { P: 88.2, R: 85.7, F: 86.9 },
    proposed: { P: 93.4, R: 91.8, F: 92.6 },
  };

  const posTaggingResults = {
    A: { P: 94.2, R: 93.1, F: 93.6 },
    B: { P: 95.5, R: 94.8, F: 95.1 },
    C: { P: 93.8, R: 92.9, F: 93.3 },
  };

  const wordSegmentationChartData = [
    { name: "Baseline (CNN)", Formal: 91.4, Informal: 86.9 },
    { name: "Proposed (CRF)", Formal: 95.0, Informal: 92.6 },
  ];

  const posComparisonData = [
    { name: "Test A", CRF: 93.6, Perceptron: 90.2 },
    { name: "Test B", CRF: 95.1, Perceptron: 91.8 },
    { name: "Test C", CRF: 93.3, Perceptron: 89.5 },
  ];

  const incorrectTagData = [
    { tag: "NN → VB", percentage: 69.77, description: "Noun misclassified as Verb" },
    { tag: "NN → PRP", percentage: 31.11, description: "Noun misclassified as Preposition" },
    { tag: "VB → NN", percentage: 7.3, description: "Verb misclassified as Noun" },
    { tag: "ADJ → NN", percentage: 5.9, description: "Adjective misclassified as Noun" },
  ];

  const averageComparisonData = [
    { name: "CRF Proposed Method", value: 91.36, fill: "#111827" },
    { name: "Perceptron Baseline", value: 88.16, fill: "#d1d5db" },
  ];

  // ── UI ─────────────────────────────────────────────────────────
  return (
    <div className="h-full overflow-auto pb-6 space-y-6">
      {/* Sub navigation – match Process / History / Statistics style */}
      <div className="flex gap-2 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setActiveSection("overview")}
          className={
            "flex-1 h-9 rounded-md text-sm font-medium transition " +
            (activeSection === "overview"
              ? "bg-black text-white"
              : "bg-transparent text-gray-800 hover:bg-gray-200")
          }
        >
          Overview
        </button>
        <button
          onClick={() => setActiveSection("segmentation")}
          className={
            "flex-1 h-9 rounded-md text-sm font-medium transition " +
            (activeSection === "segmentation"
              ? "bg-black text-white"
              : "bg-transparent text-gray-800 hover:bg-gray-200")
          }
        >
          Word segmentation
        </button>
        <button
          onClick={() => setActiveSection("pos")}
          className={
            "flex-1 h-9 rounded-md text-sm font-medium transition " +
            (activeSection === "pos"
              ? "bg-black text-white"
              : "bg-transparent text-gray-800 hover:bg-gray-200")
          }
        >
          POS tagging
        </button>
      </div>

      {/* OVERVIEW */}
      {activeSection === "overview" && (
        <div className="space-y-6">
          {/* Summary cards – neutral, simple */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">
                  Word segmentation
                </h3>
                <div className="p-2 rounded-full border border-gray-200">
                  <BarChart3 className="w-4 h-4 text-gray-700" />
                </div>
              </div>
              <p className="text-3xl font-semibold text-gray-900">95.0%</p>
              <p className="text-xs text-gray-500 mt-1">F-score (formal texts)</p>
              <p className="text-xs text-gray-600 mt-4">
                +3.6% compared to baseline CNN
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">
                  Informal texts
                </h3>
                <div className="p-2 rounded-full border border-gray-200">
                  <TrendingUp className="w-4 h-4 text-gray-700" />
                </div>
              </div>
              <p className="text-3xl font-semibold text-gray-900">92.6%</p>
              <p className="text-xs text-gray-500 mt-1">F-score</p>
              <p className="text-xs text-gray-600 mt-4">
                +5.7% compared to baseline CNN
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">
                  POS tagging
                </h3>
                <div className="p-2 rounded-full border border-gray-200">
                  <Info className="w-4 h-4 text-gray-700" />
                </div>
              </div>
              <p className="text-3xl font-semibold text-gray-900">95.1%</p>
              <p className="text-xs text-gray-500 mt-1">Best F-score (Test B)</p>
              <p className="text-xs text-gray-600 mt-4">
                +3.3% over perceptron baseline
              </p>
            </div>
          </div>

          {/* Quick comparison */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Performance summary
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-800">
                  Word segmentation
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <span className="text-gray-700">Precision (formal)</span>
                    <span className="font-semibold text-gray-900">
                      {formalResults.proposed.P}%
                    </span>
                  </div>
                  <div className="flex justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <span className="text-gray-700">Recall (formal)</span>
                    <span className="font-semibold text-gray-900">
                      {formalResults.proposed.R}%
                    </span>
                  </div>
                  <div className="flex justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <span className="text-gray-700">F-score (informal)</span>
                    <span className="font-semibold text-gray-900">
                      {informalResults.proposed.F}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-800">
                  POS tagging (per test set)
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <span className="text-gray-700">Test A</span>
                    <span className="font-semibold text-gray-900">
                      {posTaggingResults.A.F}%
                    </span>
                  </div>
                  <div className="flex justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <span className="text-gray-700">Test B</span>
                    <span className="font-semibold text-gray-900">
                      {posTaggingResults.B.F}%
                    </span>
                  </div>
                  <div className="flex justify-between rounded-lg bg-gray-50 px-3 py-2">
                    <span className="text-gray-700">Test C</span>
                    <span className="font-semibold text-gray-900">
                      {posTaggingResults.C.F}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* WORD SEGMENTATION */}
      {activeSection === "segmentation" && (
        <div className="space-y-6">
          {/* Formal table */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="border-b border-gray-200 px-6 py-3">
              <h3 className="text-sm font-semibold text-gray-900">
                Table 5.2 – formal texts
              </h3>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-600">
                    <th className="px-4 py-2 border-b border-gray-200">
                      Algorithm
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      Precision (%)
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      Recall (%)
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      F-score (%)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-100">
                      Baseline (CNN)
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {formalResults.baseline.P}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {formalResults.baseline.R}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {formalResults.baseline.F}
                    </td>
                  </tr>
                  <tr className="bg-gray-50/80 hover:bg-gray-100">
                    <td className="px-4 py-2 border-b border-gray-100 font-semibold">
                      Proposed (CRF)
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {formalResults.proposed.P}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {formalResults.proposed.R}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {formalResults.proposed.F}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Informal table */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="border-b border-gray-200 px-6 py-3">
              <h3 className="text-sm font-semibold text-gray-900">
                Table 5.3 – informal texts
              </h3>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-600">
                    <th className="px-4 py-2 border-b border-gray-200">
                      Algorithm
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      Precision (%)
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      Recall (%)
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      F-score (%)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-100">
                      Baseline (CNN)
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {informalResults.baseline.P}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {informalResults.baseline.R}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {informalResults.baseline.F}
                    </td>
                  </tr>
                  <tr className="bg-gray-50/80 hover:bg-gray-100">
                    <td className="px-4 py-2 border-b border-gray-100 font-semibold">
                      Proposed (CRF)
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {informalResults.proposed.P}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {informalResults.proposed.R}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {informalResults.proposed.F}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Bar chart */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">
              F-score comparison (formal vs informal)
            </h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={wordSegmentationChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{ fill: "#4b5563", fontSize: 12 }} />
                  <YAxis domain={[80, 100]} tick={{ fill: "#4b5563", fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="Formal"
                    name="Formal texts"
                    fill="#111827"
                    radius={[6, 6, 0, 0]}
                  />
                  <Bar
                    dataKey="Informal"
                    name="Informal texts"
                    fill="#9ca3af"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* POS TAGGING */}
      {activeSection === "pos" && (
        <div className="space-y-6">
          {/* POS table */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="border-b border-gray-200 px-6 py-3">
              <h3 className="text-sm font-semibold text-gray-900">
                POS tagging performance
              </h3>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-600">
                    <th className="px-4 py-2 border-b border-gray-200">
                      Test data
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      Precision (%)
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      Recall (%)
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      F-score (%)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-100">
                      Test A
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {posTaggingResults.A.P}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {posTaggingResults.A.R}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {posTaggingResults.A.F}
                    </td>
                  </tr>
                  <tr className="bg-gray-50/80 hover:bg-gray-100">
                    <td className="px-4 py-2 border-b border-gray-100 font-semibold">
                      Test B (re-segmented)
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {posTaggingResults.B.P}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {posTaggingResults.B.R}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center font-semibold">
                      {posTaggingResults.B.F}
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b border-gray-100">
                      Test C
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {posTaggingResults.C.P}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {posTaggingResults.C.R}
                    </td>
                    <td className="px-4 py-2 border-b border-gray-100 text-center">
                      {posTaggingResults.C.F}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* POS chart */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">
              CRF vs perceptron (F-score)
            </h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={posComparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{ fill: "#4b5563", fontSize: 12 }} />
                  <YAxis domain={[85, 100]} tick={{ fill: "#4b5563", fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="CRF"
                    name="Proposed CRF"
                    stroke="#111827"
                    strokeWidth={3}
                    dot={{ r: 5, fill: "#111827" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="Perceptron"
                    name="Baseline perceptron"
                    stroke="#9ca3af"
                    strokeWidth={3}
                    dot={{ r: 5, fill: "#9ca3af" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Error table */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
            <div className="border-b border-gray-200 px-6 py-3">
              <h3 className="text-sm font-semibold text-gray-900">
                Common tagging errors
              </h3>
            </div>
            <div className="p-4 overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-600">
                    <th className="px-4 py-2 border-b border-gray-200">
                      Error type
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200">
                      Description
                    </th>
                    <th className="px-4 py-2 border-b border-gray-200 text-center">
                      %
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {incorrectTagData.map((item) => (
                    <tr key={item.tag} className="hover:bg-gray-50">
                      <td className="px-4 py-2 border-b border-gray-100 font-semibold">
                        {item.tag}
                      </td>
                      <td className="px-4 py-2 border-b border-gray-100">
                        {item.description}
                      </td>
                      <td className="px-4 py-2 border-b border-gray-100 text-center">
                        <span className="inline-flex px-3 py-1 rounded-full bg-red-100 text-red-700 text-xs font-medium">
                          {item.percentage}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Notes */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 shadow-sm">
            <div className="flex gap-3">
              <div className="mt-1 p-2 rounded-full bg-amber-500 text-white">
                <AlertCircle className="w-4 h-4" />
              </div>
              <div className="space-y-2 text-sm text-gray-800">
                <h3 className="text-sm font-semibold text-gray-900">
                  Error analysis notes
                </h3>
                <p>
                  These errors mainly come from word ambiguity in Thai.
                </p>
                <p>
                  Example: <span className="font-medium">“มัน”</span> can be a
                  pronoun (PRP) or a noun (NN) depending on context.
                </p>
                <p>
                  The largest group (69.77%) is <span className="font-medium">NN → VB</span>,
                  which shows that distinguishing nouns vs. verbs is still the hardest part.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StatisticsPage;
