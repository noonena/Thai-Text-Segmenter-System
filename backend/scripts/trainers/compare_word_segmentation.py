# """
# Word Segmentation Method Comparison
# Runs three methods on the LST20 test set using the same upstream pipeline
# (MTU CRF → Syllable CRF → word seg) and prints P/R/F1 for each.

# Methods compared:
#   1. Viterbi          — current 1-best DP with compound bonus
#   2. Longest Match    — forward maximum matching against LST20 dictionary
#   3. POS Reranking    — k-best Viterbi rescored by POS CRF confidence

# Usage:
#   python compare_word_segmentation.py
#   python compare_word_segmentation.py --max 2000   # quick run
#   python compare_word_segmentation.py --lam 0.5    # tune POS weight
# """

# import os
# import sys
# import glob
# import pickle
# import argparse
# import math
# from typing import List, Tuple

# # ── Path setup ────────────────────────────────────────────────────────────────
# TRAINERS_DIR = os.path.dirname(os.path.abspath(__file__))
# SCRIPTS_DIR  = os.path.dirname(TRAINERS_DIR)
# BACKEND_DIR  = os.path.dirname(SCRIPTS_DIR)
# NLP_DIR      = os.path.join(SCRIPTS_DIR, "nlp_utils")
# UTILS_DIR    = os.path.join(NLP_DIR, "utils")
# MODELS_DIR   = os.path.join(TRAINERS_DIR, "models")
# MODELS_PATH  = os.path.join(BACKEND_DIR, "models")

# for p in [BACKEND_DIR, SCRIPTS_DIR, NLP_DIR, UTILS_DIR, MODELS_DIR, TRAINERS_DIR]:
#     sys.path.insert(0, p)

# # ── Config ────────────────────────────────────────────────────────────────────
# MTU_MODEL_PATH = os.path.join(MODELS_PATH, "mtu_crf_model.pkl")
# SYL_MODEL_PATH = os.path.join(MODELS_PATH, "syllable_crf_model.pkl")
# POS_MODEL_PATH = os.path.join(MODELS_PATH, "pos_crf_model.pkl")
# DICT_PATH      = os.path.join(MODELS_PATH, "lst20_dictionary.pkl")
# TEST_DIR       = os.path.join(BACKEND_DIR, "..", "data", "LST20_Corpus", "test")
# MAX_SENTENCES  = 5000   # default — full test set ~38k, use --max to change
# # python backend/scripts/trainers/compare_word_segmentation.py --lam 4.0 --k 5

# # ── LST20 reader ──────────────────────────────────────────────────────────────
# def read_lst20_sentences(test_dir: str, max_sentences: int):
#     sentences = []
#     files = sorted(glob.glob(os.path.join(test_dir, "*.txt")))
#     current_words = []

#     for filepath in files:
#         with open(filepath, "r", encoding="utf-8") as f:
#             for line in f:
#                 line = line.strip()
#                 if not line:
#                     continue
#                 parts = line.split("\t")
#                 if len(parts) < 2:
#                     continue
#                 word = parts[0]
#                 if word == "_":
#                     if current_words:
#                         sentences.append(current_words[:])
#                         current_words = []
#                         if len(sentences) >= max_sentences:
#                             return sentences
#                 else:
#                     current_words.append(word)
#         if len(sentences) >= max_sentences:
#             break

#     if current_words:
#         sentences.append(current_words)
#     return sentences


# # ── Syllable reconstruction ───────────────────────────────────────────────────
# def mtus_to_syllables(mtus: List[str], labels: List[str]) -> List[str]:
#     syllables, current = [], []
#     for mtu, label in zip(mtus, labels):
#         if label == "S":
#             if current:
#                 syllables.append("".join(current))
#                 current = []
#             syllables.append(mtu)
#         elif label == "B":
#             current = [mtu]
#         elif label == "M":
#             current.append(mtu)
#         elif label == "E":
#             current.append(mtu)
#             syllables.append("".join(current))
#             current = []
#     if current:
#         syllables.append("".join(current))
#     return syllables


# # ── Evaluation helpers ────────────────────────────────────────────────────────
# def word_boundaries(words: List[str]) -> set:
#     """Character positions where each word ends."""
#     bounds, pos = set(), 0
#     for w in words:
#         pos += len(w)
#         bounds.add(pos)
#     return bounds


# def prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
#     p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
#     r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
#     f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
#     return p, r, f


# def accumulate(gold_words, pred_words, counters):
#     gold_b = word_boundaries(gold_words)
#     pred_b = word_boundaries(pred_words)
#     counters['tp'] += len(gold_b & pred_b)
#     counters['fp'] += len(pred_b - gold_b)
#     counters['fn'] += len(gold_b - pred_b)


# # ── Oracle helper ─────────────────────────────────────────────────────────────
# def oracle_score(gold_words, candidates):
#     """
#     Among all k candidates, return the one with highest boundary F1 vs gold.
#     Used to measure the ceiling of k-best reranking.
#     """
#     gold_b = word_boundaries(gold_words)
#     best_f1, best_words = -1.0, candidates[0][1]

#     for _, words in candidates:
#         pred_b = word_boundaries(words)
#         tp = len(gold_b & pred_b)
#         fp = len(pred_b - gold_b)
#         fn = len(gold_b - pred_b)
#         _, _, f = prf(tp, fp, fn)
#         if f > best_f1:
#             best_f1 = f
#             best_words = words

#     return best_words


# # ── Main ──────────────────────────────────────────────────────────────────────
# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--max",  type=int,   default=MAX_SENTENCES,
#                         help="Max test sentences to evaluate")
#     parser.add_argument("--lam",  type=float, default=0.3,
#                         help="POS reranking weight λ (default 0.3)")
#     parser.add_argument("--k",    type=int,   default=5,
#                         help="Beam size for k-best Viterbi (default 5)")
#     args = parser.parse_args()

#     print("=" * 70)
#     print("WORD SEGMENTATION METHOD COMPARISON")
#     print("=" * 70)

#     # ── Load models ───────────────────────────────────────────────────────────
#     print("\nLoading models...")

#     with open(MTU_MODEL_PATH, "rb") as f:
#         mtu_crf = pickle.load(f)
#     print("  MTU CRF loaded")

#     with open(SYL_MODEL_PATH, "rb") as f:
#         syl_crf = pickle.load(f)
#     print("  Syllable CRF loaded")

#     pos_crf = None
#     if os.path.exists(POS_MODEL_PATH):
#         with open(POS_MODEL_PATH, "rb") as f:
#             pos_crf = pickle.load(f)
#         print("  POS CRF loaded")
#     else:
#         print("  POS CRF not found — skipping POS reranking")

#     from word_segmentation import WordSegmenter
#     segmenter = WordSegmenter(DICT_PATH)

#     from mtu_features import segment_text_to_mtus
#     from syllable_features import extract_features_for_sentence

#     # ── Load test data ────────────────────────────────────────────────────────
#     print(f"\nLoading test sentences from {TEST_DIR}...")
#     sentences = read_lst20_sentences(TEST_DIR, args.max)
#     print(f"  Loaded {len(sentences)} sentences")

#     # ── Counters ──────────────────────────────────────────────────────────────
#     methods = ["viterbi", "longest_match", "oracle"]
#     if pos_crf:
#         methods.append("pos_rerank")

#     counters = {m: {'tp': 0, 'fp': 0, 'fn': 0} for m in methods}
#     skipped = 0

#     # ── Evaluate ──────────────────────────────────────────────────────────────
#     print("\nEvaluating...")
#     for i, gold_words in enumerate(sentences):
#         if i % 500 == 0:
#             print(f"  {i}/{len(sentences)}", flush=True)

#         text = "".join(gold_words)
#         if not text:
#             skipped += 1
#             continue

#         try:
#             # MTU stage
#             mtus_nested, _, _ = segment_text_to_mtus(text, mtu_crf)
#             mtus = ["".join(m) for m in mtus_nested]

#             # Syllable stage
#             syl_feats  = extract_features_for_sentence(mtus)
#             syl_labels = syl_crf.predict([syl_feats])[0]
#             syllables  = mtus_to_syllables(mtus, syl_labels)

#             if not syllables:
#                 skipped += 1
#                 continue

#             # Method 1: 1-best Viterbi
#             pred_viterbi = segmenter.segment_with_viterbi(syllables)
#             accumulate(gold_words, pred_viterbi, counters["viterbi"])

#             # Method 2: Longest match
#             pred_lm = segmenter.segment_with_longest_match(syllables)
#             accumulate(gold_words, pred_lm, counters["longest_match"])

#             # Method 3: Oracle (ceiling)
#             kbest = segmenter.segment_with_viterbi_kbest(syllables, k=args.k)
#             pred_oracle = oracle_score(gold_words, kbest)
#             accumulate(gold_words, pred_oracle, counters["oracle"])

#             # Method 4: POS reranking
#             if pos_crf:
#                 pred_pos = segmenter.segment_with_pos_reranking(
#                     syllables, pos_crf, lam=args.lam, k=args.k
#                 )
#                 accumulate(gold_words, pred_pos, counters["pos_rerank"])

#         except Exception as e:
#             skipped += 1
#             continue

#     # ── Results ───────────────────────────────────────────────────────────────
#     print(f"\nSkipped: {skipped} sentences (empty or pipeline error)")
#     print()
#     print("=" * 70)
#     print(f"RESULTS  (sentences={len(sentences)-skipped}, k={args.k}, λ={args.lam})")
#     print("=" * 70)
#     print(f"  {'Method':<20}  {'Precision':>10}  {'Recall':>10}  {'F1':>10}")
#     print(f"  {'-'*20}  {'-'*10}  {'-'*10}  {'-'*10}")

#     labels = {
#         "viterbi":       "1-best Viterbi",
#         "longest_match": "Longest Match",
#         "oracle":        f"Oracle (k={args.k})",
#         "pos_rerank":    f"POS Rerank (λ={args.lam})",
#     }

#     for m in methods:
#         c = counters[m]
#         p, r, f = prf(c['tp'], c['fp'], c['fn'])
#         print(f"  {labels[m]:<20}  {p*100:>9.2f}%  {r*100:>9.2f}%  {f*100:>9.2f}%")

#     print()

#     # ── Interpretation ────────────────────────────────────────────────────────
#     v_f1 = prf(*[counters['viterbi'][k] for k in ('tp','fp','fn')])[2]
#     lm_f1 = prf(*[counters['longest_match'][k] for k in ('tp','fp','fn')])[2]
#     or_f1 = prf(*[counters['oracle'][k] for k in ('tp','fp','fn')])[2]

#     print("Interpretation:")
#     gap = (or_f1 - v_f1) * 100
#     print(f"  Oracle headroom above Viterbi: {gap:+.2f}% F1")
#     if gap < 1.0:
#         print("  → Very little headroom. Bottleneck is upstream (MTU/syllable)")
#         print("    or dictionary coverage, not ranking. Fix scoring formula first.")
#     elif gap < 3.0:
#         print("  → Modest headroom. POS reranking may give small gains.")
#     else:
#         print("  → Good headroom. Correct answer IS in top-k; reranking can help.")

#     if lm_f1 > v_f1:
#         print(f"\n  Longest Match beats Viterbi by {(lm_f1-v_f1)*100:.2f}% F1.")
#         print("  → Compound bonus (3.5/syllable) is over-merging. Consider tuning it.")
#     else:
#         print(f"\n  Viterbi beats Longest Match by {(v_f1-lm_f1)*100:.2f}% F1.")
#         print("  → DP framework is sound; scoring just needs better calibration.")

#     print("=" * 70)


# if __name__ == "__main__":
#     main()
