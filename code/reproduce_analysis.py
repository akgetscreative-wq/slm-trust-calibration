#!/usr/bin/env python3
"""
reproduce_analysis.py - Exploratory Error-Risk Analysis for Llama 3.2 3B
Audited 300-Row Primary Subset (ARC-Challenge, GSM8K, MMLU Abstract Algebra)

Usage:
    python reproduce_analysis.py --data ../data/approved_analysis_data.csv --out ../results
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def compute_metrics(y_true, scores):
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    n = len(y)
    errors = int(y.sum())
    prev = float(y.mean())
    auroc = float(roc_auc_score(y, s)) if len(np.unique(y)) > 1 else float("nan")
    auprc = float(average_precision_score(y, s)) if len(np.unique(y)) > 1 else float("nan")
    return {
        "n": n,
        "errors": errors,
        "error_prevalence": prev,
        "AUROC_error_risk": auroc,
        "AUPRC_error_risk": auprc,
    }

def main():
    parser = argparse.ArgumentParser(description="Reproduce LLM Trust Research Analysis")
    parser.add_argument("--data", default="../data/approved_analysis_data.csv", help="Path to approved data CSV")
    parser.add_argument("--out", default="../results", help="Output directory")
    args = parser.parse_args()

    data_path = Path(args.data)
    out_dir = Path(args.out)
    figs_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found at {data_path.resolve()}")

    df = pd.read_csv(data_path)
    required_cols = {"question_id", "domain", "audit_correct_label", "self_confidence_v2", "self_check_v2"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    # Derived variables
    df["correct"] = pd.to_numeric(df["audit_correct_label"], errors="raise").astype(int)
    df["error"] = 1 - df["correct"]
    df["confidence"] = pd.to_numeric(df["self_confidence_v2"], errors="raise") / 100.0
    df["confidence_risk"] = 1.0 - df["confidence"]
    df["check_no"] = (df["self_check_v2"].astype(str).str.upper() != "YES").astype(int)

    # =========================================================================
    # 1. BASELINE SIGNAL METRICS (Pooled and Within-Domain Descriptive)
    # =========================================================================
    baseline_records = []

    # Pooled
    for model_name, score in [
        ("Constant Prevalence Baseline", np.full(len(df), df["error"].mean())),
        ("Confidence-only: inverted confidence", df["confidence_risk"]),
        ("Self-check-only: NO is risk", df["check_no"])
    ]:
        if model_name == "Constant Prevalence Baseline":
            m = {
                "n": len(df), "errors": int(df["error"].sum()), "error_prevalence": float(df["error"].mean()),
                "AUROC_error_risk": 0.5, "AUPRC_error_risk": float(df["error"].mean())
            }
        else:
            m = compute_metrics(df["error"], score)
        baseline_records.append({
            "evaluation": "pooled_descriptive",
            "held_out_domain": "all",
            "model": model_name,
            **m
        })

    # Within-domain descriptive
    for dom, g in df.groupby("domain", sort=False):
        for model_name, score in [
            ("Constant Prevalence Baseline", np.full(len(g), g["error"].mean())),
            ("Confidence-only: inverted confidence", g["confidence_risk"]),
            ("Self-check-only: NO is risk", g["check_no"])
        ]:
            if model_name == "Constant Prevalence Baseline":
                m = {
                    "n": len(g), "errors": int(g["error"].sum()), "error_prevalence": float(g["error"].mean()),
                    "AUROC_error_risk": 0.5, "AUPRC_error_risk": float(g["error"].mean())
                }
            else:
                m = compute_metrics(g["error"], score)
            baseline_records.append({
                "evaluation": "within-domain_descriptive",
                "held_out_domain": dom,
                "model": model_name,
                **m
            })

    baseline_df = pd.DataFrame(baseline_records)
    baseline_df.to_csv(out_dir / "final_metrics.csv", index=False)

    # =========================================================================
    # 2. LEAVE-ONE-DOMAIN-OUT (LODO) CROSS-VALIDATION
    # =========================================================================
    lodo_records = []
    lodo_predictions = []

    domains = df["domain"].unique()
    for dom in domains:
        train = df[df["domain"] != dom].copy()
        test = df[df["domain"] == dom].copy()

        feature_sets = {
            "Confidence logistic": ["confidence_risk"],
            "Self-check logistic": ["check_no"],
            "Combined logistic": ["confidence_risk", "check_no"]
        }

        for model_name, feats in feature_sets.items():
            pipe = make_pipeline(
                StandardScaler(),
                LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42)
            )
            pipe.fit(train[feats], train["error"])
            pred_probs = pipe.predict_proba(test[feats])[:, 1]

            m = compute_metrics(test["error"], pred_probs)
            lodo_records.append({
                "evaluation": "leave-one-domain-out",
                "held_out_domain": dom,
                "model": model_name,
                "train_n": len(train),
                "test_n": len(test),
                **m
            })

            for ix, p in zip(test.index, pred_probs):
                lodo_predictions.append({
                    "row_index": int(ix),
                    "question_id": str(df.loc[ix, "question_id"]),
                    "domain": dom,
                    "model": model_name,
                    "predicted_error_probability": float(p),
                    "true_error": int(df.loc[ix, "error"]),
                    "self_confidence_v2": float(df.loc[ix, "self_confidence_v2"]),
                    "self_check_v2": str(df.loc[ix, "self_check_v2"])
                })

    lodo_df = pd.DataFrame(lodo_records)
    lodo_df.to_csv(out_dir / "fold_metrics.csv", index=False)

    preds_df = pd.DataFrame(lodo_predictions)
    preds_df.to_csv(out_dir / "lodo_predictions.csv", index=False)

    # =========================================================================
    # 3. SELECTIVE PREDICTION (Deployable Threshold vs Target Coverage)
    # =========================================================================
    # For deployable rule: select threshold on training fold, freeze it, evaluate on held-out test fold!
    target_coverages = [0.50, 0.75, 0.90]
    selective_records = []

    for dom in domains:
        train = df[df["domain"] != dom].copy()
        test = df[df["domain"] == dom].copy()

        # Fit combined model on train
        pipe = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42))
        pipe.fit(train[["confidence_risk", "check_no"]], train["error"])
        train_probs = pipe.predict_proba(train[["confidence_risk", "check_no"]])[:, 1]
        test_probs = pipe.predict_proba(test[["confidence_risk", "check_no"]])[:, 1]

        # Also evaluate raw confidence risk
        train_conf_risk = train["confidence_risk"].to_numpy()
        test_conf_risk = test["confidence_risk"].to_numpy()

        for target_cov in target_coverages:
            # Combined model threshold chosen on train quantile
            # Accept if predicted error risk <= threshold
            thresh_comb = np.percentile(train_probs, target_cov * 100)
            accepted_mask_comb = test_probs <= thresh_comb
            n_accepted_comb = int(accepted_mask_comb.sum())
            actual_cov_comb = n_accepted_comb / len(test)
            err_comb = int(test.loc[accepted_mask_comb, "error"].sum()) if n_accepted_comb > 0 else 0
            acc_err_rate_comb = (err_comb / n_accepted_comb) if n_accepted_comb > 0 else float("nan")
            acc_accuracy_comb = 1.0 - acc_err_rate_comb if n_accepted_comb > 0 else float("nan")

            selective_records.append({
                "held_out_domain": dom,
                "model": "Combined Logistic (Deployable Threshold)",
                "target_coverage": target_cov,
                "frozen_threshold": float(thresh_comb),
                "test_n": len(test),
                "accepted_n": n_accepted_comb,
                "actual_coverage": actual_cov_comb,
                "accepted_errors": err_comb,
                "accepted_error_rate": acc_err_rate_comb,
                "accepted_accuracy": acc_accuracy_comb,
                "unfiltered_baseline_accuracy": float(test["correct"].mean())
            })

            # Confidence-only threshold chosen on train quantile
            thresh_conf = np.percentile(train_conf_risk, target_cov * 100)
            accepted_mask_conf = test_conf_risk <= thresh_conf
            n_accepted_conf = int(accepted_mask_conf.sum())
            actual_cov_conf = n_accepted_conf / len(test)
            err_conf = int(test.loc[accepted_mask_conf, "error"].sum()) if n_accepted_conf > 0 else 0
            acc_err_rate_conf = (err_conf / n_accepted_conf) if n_accepted_conf > 0 else float("nan")
            acc_accuracy_conf = 1.0 - acc_err_rate_conf if n_accepted_conf > 0 else float("nan")

            selective_records.append({
                "held_out_domain": dom,
                "model": "Confidence Only (Deployable Threshold)",
                "target_coverage": target_cov,
                "frozen_threshold": float(thresh_conf),
                "test_n": len(test),
                "accepted_n": n_accepted_conf,
                "actual_coverage": actual_cov_conf,
                "accepted_errors": err_conf,
                "accepted_error_rate": acc_err_rate_conf,
                "accepted_accuracy": acc_accuracy_conf,
                "unfiltered_baseline_accuracy": float(test["correct"].mean())
            })

    selective_df = pd.DataFrame(selective_records)
    selective_df.to_csv(out_dir / "selective_prediction_coverage.csv", index=False)

    # =========================================================================
    # 4. FAILURE CASES IDENTIFICATION
    # =========================================================================
    failure_cases = []

    # 1. High-confidence errors (confidence >= 80, error == 1)
    hi_conf_errs = df[(df["self_confidence_v2"] >= 80) & (df["error"] == 1)]
    for _, r in hi_conf_errs.iterrows():
        failure_cases.append({
            "category": "High-Confidence Error (Overconfidence)",
            "question_id": str(r["question_id"]),
            "domain": r["domain"],
            "confidence": float(r["self_confidence_v2"]),
            "self_check": r["self_check_v2"],
            "model_answer": str(r["model_answer"])[:120].replace("\n", " "),
            "note": "Model expressed >=80% certainty on an erroneous answer."
        })

    # 2. Self-check false reassurance (self_check == 'YES', error == 1)
    yes_errs = df[(df["self_check_v2"] == "YES") & (df["error"] == 1)].head(15)
    for _, r in yes_errs.iterrows():
        failure_cases.append({
            "category": "False Reassurance (Affirmative Error)",
            "question_id": str(r["question_id"]),
            "domain": r["domain"],
            "confidence": float(r["self_confidence_v2"]),
            "self_check": r["self_check_v2"],
            "model_answer": str(r["model_answer"])[:120].replace("\n", " "),
            "note": "Model endorsed answer with 'YES' despite being objectively incorrect."
        })

    # 3. False alarm / Overly cautious (self_check == 'NO', error == 0)
    no_correct = df[(df["self_check_v2"] == "NO") & (df["correct"] == 1)]
    for _, r in no_correct.iterrows():
        failure_cases.append({
            "category": "False Alarm (Unwarranted Rejection)",
            "question_id": str(r["question_id"]),
            "domain": r["domain"],
            "confidence": float(r["self_confidence_v2"]),
            "self_check": r["self_check_v2"],
            "model_answer": str(r["model_answer"])[:120].replace("\n", " "),
            "note": "Model was objectively correct but rejected its own answer with 'NO'."
        })

    fail_df = pd.DataFrame(failure_cases)
    fail_df.to_csv(out_dir / "failure_cases.csv", index=False)

    # =========================================================================
    # 5. FIGURES GENERATION
    # =========================================================================
    # Figure 1: Calibration curve by domain
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)
    colors = {"MMLU": "#1f77b4", "GSM8K": "#ff7f0e", "ARC-Challenge": "#2ca02c"}
    
    # 5 equal bins
    bins = np.linspace(0, 1, 6)
    for dom in ["MMLU", "GSM8K", "ARC-Challenge"]:
        sub = df[df["domain"] == dom]
        p = sub["confidence"].to_numpy()
        y = sub["correct"].to_numpy()
        bin_confs, bin_accs = [], []
        for i in range(len(bins)-1):
            mask = (p >= bins[i]) & (p < (bins[i+1] if i < len(bins)-2 else bins[i+1]+1e-9))
            if mask.sum() > 0:
                bin_confs.append(p[mask].mean())
                bin_accs.append(y[mask].mean())
        ax.plot(bin_confs, bin_accs, marker="o", lw=1.8, label=dom, color=colors[dom])

    ax.plot([0, 1], [0, 1], linestyle="--", color="#d62728", label="Ideal calibration")
    ax.set_xlabel("Mean verbalized confidence", fontsize=10)
    ax.set_ylabel("Observed labelled accuracy", fontsize=10)
    ax.set_title("Confidence vs. observed accuracy by domain", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=8.5)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(figs_dir / "fig1_domain_calibration.png")
    plt.close()

    # Figure 2: AUROC comparison across domains
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=300)
    dom_summary = df.groupby("domain", sort=False).apply(
        lambda g: pd.Series({
            "conf_risk_auroc": roc_auc_score(g["error"], g["confidence_risk"]),
            "check_risk_auroc": roc_auc_score(g["error"], g["check_no"])
        })
    ).reset_index()

    x = np.arange(len(dom_summary))
    w = 0.32
    ax.bar(x - w/2, dom_summary["conf_risk_auroc"], width=w, label="Confidence risk", color="#1f77b4")
    ax.bar(x + w/2, dom_summary["check_risk_auroc"], width=w, label="Self-check risk", color="#ff7f0e")
    ax.axhline(0.5, color="#1f77b4", linestyle="--", label="Chance AUROC")
    ax.set_xticks(x)
    ax.set_xticklabels(dom_summary["domain"], fontsize=9.5)
    ax.set_ylabel("AUROC (error as positive class)", fontsize=10)
    ax.set_title("Error-ranking performance varies by domain", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(figs_dir / "fig2_domain_auroc.png")
    plt.close()

    # Figure 3: Selective Risk vs Coverage Tradeoff
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=300)
    for dom in ["MMLU", "GSM8K", "ARC-Challenge"]:
        sub_sel = selective_df[(selective_df["held_out_domain"] == dom) & (selective_df["model"].str.startswith("Combined"))]
        ax.plot(sub_sel["actual_coverage"], sub_sel["accepted_accuracy"], marker="s", lw=1.8, label=f"{dom} (Combined LODO)")
        base_acc = sub_sel["unfiltered_baseline_accuracy"].iloc[0]
        ax.axhline(base_acc, color=colors[dom], linestyle=":", alpha=0.7)

    ax.set_xlabel("Empirical Coverage on Held-Out Domain", fontsize=10)
    ax.set_ylabel("Accepted Subset Accuracy", fontsize=10)
    ax.set_title("Selective Prediction: Accepted Accuracy vs. Coverage", fontsize=11, fontweight="bold")
    ax.legend(loc="lower left", fontsize=8.5)
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(figs_dir / "fig3_risk_coverage_curve.png")
    plt.close()

    print(f"Reproducible analysis complete. Results exported to {out_dir.resolve()}")

if __name__ == "__main__":
    main()
