#!/usr/bin/env python3
"""
trust_evaluator.py - Lightweight Answer-Risk Estimator for Llama 3.2 3B
Experimental Decision Support Utility (Exploratory Research Prototype)

CAUTION:
This utility produces exploratory error-risk estimates based on model self-reports.
It is NOT a factual verifier or safety guarantee. In empirical testing, 42.6% of
self-endorsed answers were incorrect, and confidence inverted on symbolic tasks.
"""

import sys
import argparse
import numpy as np

# Coefficients fitted on the pooled 300-row primary exploratory dataset
# (ARC-Challenge, GSM8K, MMLU Abstract Algebra)
# Model: LogisticRegression(class_weight='balanced') on StandardScaler(confidence_risk, check_no)
# Feature 1: confidence_risk = 1.0 - (confidence / 100.0)
# Feature 2: check_no = 1 if self_check != 'YES' else 0

SCALER_MEAN = np.array([0.35266667, 0.17000000])
SCALER_SCALE = np.array([0.27964648, 0.37563280])
COEF = np.array([0.56942634, 0.38052189])
INTERCEPT = -0.12648712

# Deployable frozen risk threshold: median risk (50% target coverage policy)
FROZEN_ACCEPTANCE_THRESHOLD = 0.468

def estimate_answer_risk(confidence: float, self_check: str) -> dict:
    """
    Estimates posterior error probability and generates an operational routing verdict.
    
    Args:
        confidence: Stated verbalized confidence on 0-100 scale (float or int).
        self_check: Stated self-verification verdict ('YES', 'NO', or 'UNSURE').
        
    Returns:
        dict containing:
            - error_probability: estimated failure probability in [0, 1]
            - action_verdict: 'ACCEPT (Low Stated Risk)' or 'FLAG FOR VERIFICATION'
            - disclaimer: prominent warning regarding false reassurance and inversion
    """
    # 1. Input sanitization
    try:
        conf_val = float(confidence)
        if not (0.0 <= conf_val <= 100.0):
            raise ValueError(f"Confidence must be between 0 and 100; got {confidence}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid confidence input: {e}")

    check_str = str(self_check).strip().upper()
    check_no_val = 0.0 if check_str == "YES" else 1.0

    # 2. Feature transformation
    conf_risk = 1.0 - (conf_val / 100.0)
    raw_feats = np.array([conf_risk, check_no_val])
    scaled_feats = (raw_feats - SCALER_MEAN) / SCALER_SCALE

    # 3. Logistic prediction
    logit = float(np.dot(COEF, scaled_feats) + INTERCEPT)
    prob_error = float(1.0 / (1.0 + np.exp(-logit)))

    # 4. Routing policy under frozen threshold
    if prob_error <= FROZEN_ACCEPTANCE_THRESHOLD:
        verdict = "ACCEPT (Low Stated Risk)"
        action_note = "Model expressed high confidence and affirmative self-check. Caution: 42.6% of affirmative checks failed in empirical testing."
    else:
        verdict = "FLAG FOR HUMAN VERIFICATION"
        action_note = "Model expressed elevated uncertainty or negative self-check. Independent verification recommended."

    return {
        "input_confidence": conf_val,
        "input_self_check": check_str,
        "estimated_error_probability": round(prob_error, 4),
        "decision_threshold": FROZEN_ACCEPTANCE_THRESHOLD,
        "action_verdict": verdict,
        "action_guidance": action_note,
        "scientific_disclaimer": (
            "WARNING: This estimate is derived from model self-reports, not ground truth. "
            "Evaluations on Llama 3.2 3B demonstrate that confidence can invert on symbolic reasoning "
            "(MMLU AUROC = 0.384) and that self-checking frequently exhibits confirmation bias."
        )
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate answer risk for Llama 3.2 3B completions.")
    parser.add_argument("--confidence", type=float, required=True, help="Verbalized confidence (0-100)")
    parser.add_argument("--self-check", type=str, required=True, help="Self-check verdict (YES / NO / UNSURE)")
    args = parser.parse_args()

    res = estimate_answer_risk(args.confidence, args.self_check)
    print("\n" + "="*70)
    print(" LLAMA 3.2 3B ANSWER-RISK ESTIMATOR (EXPERIMENTAL PROTOTYPE)")
    print("="*70)
    print(f" Input Confidence:       {res['input_confidence']:.1f}%")
    print(f" Input Self-Check:       {res['input_self_check']}")
    print(f" Estimated Error Risk:   {res['estimated_error_probability']*100:.1f}% (Threshold: {res['decision_threshold']*100:.1f}%)")
    print(f" Recommended Action:     {res['action_verdict']}")
    print(f" Operational Guidance:   {res['action_guidance']}")
    print("-" * 70)
    print(f" Scientific Disclaimer:\n {res['scientific_disclaimer']}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
