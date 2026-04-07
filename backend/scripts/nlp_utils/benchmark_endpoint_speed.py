"""
Benchmark NLP endpoint speed vs input text length.

This script is intended to run separately from the backend server process.
Start the server first, then run this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib import error, request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_LENGTHS = [250, 500, 1000, 2000, 4000, 6000, 8000, 10000]


@dataclass
class BenchmarkResult:
    endpoint: str
    input_length_chars: int
    avg_latency_sec: float
    median_latency_sec: float
    min_latency_sec: float
    max_latency_sec: float
    speed_chars_per_sec: float
    avg_reported_segment_tps: float | None


def post_json(url: str, payload: dict, timeout_sec: float) -> tuple[dict, float]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(
            f"Cannot connect to {url}. Make sure backend server is running."
        ) from exc
    elapsed = time.perf_counter() - started

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response from {url}: {raw[:200]}") from exc

    return parsed, elapsed


def parse_lengths(lengths_arg: str) -> list[int]:
    values = []
    for part in lengths_arg.split(","):
        part = part.strip()
        if not part:
            continue
        value = int(part)
        if value <= 0:
            continue
        values.append(value)
    return sorted(set(values))


def build_lengths(text_length: int, requested_lengths: list[int]) -> list[int]:
    lengths = [n for n in requested_lengths if n <= text_length]
    if lengths:
        return lengths

    if text_length <= 0:
        return []

    # Fallback: generate 5 evenly distributed sizes from available text.
    steps = 5
    generated = sorted({max(1, (text_length * i) // steps) for i in range(1, steps + 1)})
    return generated


def benchmark_one_endpoint(
    endpoint_name: str,
    endpoint_url: str,
    text: str,
    lengths: list[int],
    repeats: int,
    timeout_sec: float,
    payload_builder: Callable[[str], dict],
) -> list[BenchmarkResult]:
    results: list[BenchmarkResult] = []

    for n in lengths:
        sample = text[:n]
        latencies: list[float] = []
        reported_segment_tps: list[float] = []

        for _ in range(repeats):
            response, elapsed = post_json(
                endpoint_url,
                payload_builder(sample),
                timeout_sec=timeout_sec,
            )
            if not response.get("success", False):
                raise RuntimeError(f"{endpoint_name} returned unsuccessful response: {response}")

            segment_tps = response.get("data", {}).get("segment_tps")
            if isinstance(segment_tps, (int, float)):
                reported_segment_tps.append(float(segment_tps))

            latencies.append(elapsed)

        avg_latency = statistics.mean(latencies)
        speed = (n / avg_latency) if avg_latency > 0 else 0.0
        avg_reported = (
            statistics.harmonic_mean(reported_segment_tps) if reported_segment_tps else None
        )

        results.append(
            BenchmarkResult(
                endpoint=endpoint_name,
                input_length_chars=n,
                avg_latency_sec=avg_latency,
                median_latency_sec=statistics.median(latencies),
                min_latency_sec=min(latencies),
                max_latency_sec=max(latencies),
                speed_chars_per_sec=speed,
                avg_reported_segment_tps=avg_reported,
            )
        )

        print(
            f"[{endpoint_name}] len={n:5d} | "
            f"avg={avg_latency:.4f}s | "
            f"speed={speed:,.2f} chars/s"
        )

    return results


def warm_up(base_url: str, warmup_text: str, timeout_sec: float) -> None:
    print("Running warm-up requests to initialize module...")
    text_url = f"{base_url}/api/nlp/text-process"
    html_url = f"{base_url}/api/nlp/process-html"

    post_json(text_url, {"text": warmup_text}, timeout_sec=timeout_sec)
    post_json(html_url, {"html": f"<p>{warmup_text}</p>"}, timeout_sec=timeout_sec)
    post_json(text_url, {"text": warmup_text}, timeout_sec=timeout_sec)
    post_json(html_url, {"html": f"<p>{warmup_text}</p>"}, timeout_sec=timeout_sec)
    print("Warm-up complete. Starting benchmark...\n")


def save_csv(results: list[BenchmarkResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "endpoint",
                "input_length_chars",
                "avg_latency_sec",
                "median_latency_sec",
                "min_latency_sec",
                "max_latency_sec",
                "speed_chars_per_sec",
                "avg_reported_segment_tps",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r.endpoint,
                    r.input_length_chars,
                    f"{r.avg_latency_sec:.6f}",
                    f"{r.median_latency_sec:.6f}",
                    f"{r.min_latency_sec:.6f}",
                    f"{r.max_latency_sec:.6f}",
                    f"{r.speed_chars_per_sec:.6f}",
                    "" if r.avg_reported_segment_tps is None else f"{r.avg_reported_segment_tps:.6f}",
                ]
            )


def save_plot(results: list[BenchmarkResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    by_endpoint: dict[str, list[BenchmarkResult]] = {}
    for result in results:
        by_endpoint.setdefault(result.endpoint, []).append(result)

    plt.figure(figsize=(10, 6))
    for endpoint, items in by_endpoint.items():
        ordered = sorted(items, key=lambda x: x.input_length_chars)
        x = [i.input_length_chars for i in ordered]
        y_1 = [i.avg_reported_segment_tps for i in ordered]
        y_2 = [i.speed_chars_per_sec for i in ordered]
        plt.plot(x, y_1, marker="o", linewidth=2, label=(endpoint + ' (TPS)'), linestyle="--")
        plt.plot(x, y_2, marker="o", linewidth=2, label=(endpoint + ' (chars/sec)'), linestyle="-")

    plt.title("Segmentation Speed vs Input Text Length")
    plt.xlabel("Input text length (characters)")
    plt.ylabel("Segmentation speed (TPS) / (chars/sec)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark /api/nlp/process-html and /api/nlp/text-process speed."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--text-file",
        default=str(Path(__file__).resolve().parents[3] / "backend" / "data" / "test.txt"),
        help="Path to source text file (default: repo_root/backend/data/test.txt)",
    )
    parser.add_argument(
        "--lengths",
        default=",".join(str(x) for x in DEFAULT_LENGTHS),
        help="Comma-separated input lengths in characters",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Runs per length for each endpoint (default: 3)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP timeout seconds per request (default: 120)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[2] / "results" / "benchmarks"),
        help="Output directory for CSV and graph",
    )
    args = parser.parse_args()

    source_file = Path(args.text_file)
    if not source_file.exists():
        raise FileNotFoundError(f"Text file not found: {source_file}")

    text = source_file.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    if not text:
        raise ValueError("Input text file is empty.")

    requested_lengths = parse_lengths(args.lengths)
    if not requested_lengths:
        requested_lengths = DEFAULT_LENGTHS

    lengths = build_lengths(len(text), requested_lengths)
    # text-process endpoint rejects over 10,000 chars.
    lengths = [n for n in lengths if n <= 10_000]
    if not lengths:
        raise ValueError("No valid lengths to test after applying endpoint limits.")

    warmup_text = text[: min(300, len(text))]
    warm_up(args.base_url, warmup_text, timeout_sec=args.timeout)

    text_process_results = benchmark_one_endpoint(
        endpoint_name="text-process",
        endpoint_url=f"{args.base_url}/api/nlp/text-process",
        text=text,
        lengths=lengths,
        repeats=max(1, args.repeats),
        timeout_sec=args.timeout,
        payload_builder=lambda sample: {"text": sample},
    )
    print()
    process_html_results = benchmark_one_endpoint(
        endpoint_name="process-html",
        endpoint_url=f"{args.base_url}/api/nlp/process-html",
        text=text,
        lengths=lengths,
        repeats=max(1, args.repeats),
        timeout_sec=args.timeout,
        payload_builder=lambda sample: {"html": f"<div>{sample}</div>"},
    )

    all_results = text_process_results + process_html_results

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir)
    csv_path = output_dir / f"endpoint_speed_benchmark_{timestamp}.csv"
    plot_path = output_dir / f"endpoint_speed_benchmark_{timestamp}.png"

    save_csv(all_results, csv_path)
    save_plot(all_results, plot_path)

    print("\nBenchmark complete.")
    print(f"CSV results:  {csv_path}")
    print(f"Speed graph:  {plot_path}")


if __name__ == "__main__":
    main()
