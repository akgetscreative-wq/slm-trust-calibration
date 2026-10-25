# When Should a Small Language Model Be Trusted?
### Evaluating Verbalized Confidence and Self-Verification Under Domain Shift

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Format: IEEE Conference](https://img.shields.io/badge/Format-IEEE%20Conference%20(8%20Pages)-orange.svg)](paper/research_paper.pdf)
[![Model: Llama-3.2-3B](https://img.shields.io/badge/Model-Meta%20Llama--3.2--3B-purple.svg)](https://huggingface.co/meta-llama/Llama-3.2-3B)

Official open-source research and replication repository for the IEEE conference paper:  
**"When Should a Small Language Model Be Trusted? Evaluating Verbalized Confidence and Self-Verification Under Domain Shift"**  
Author: **Aayush Kumar**, Department of Computer Science, VIT-AP University (`aayush@vitap.com`).

---

## 📄 Research Paper

The complete, submission-ready 8-page IEEE conference research paper is available in both formats:
- **PDF Version:** [`paper/research_paper.pdf`](paper/research_paper.pdf)
- **Word Document:** [`paper/research_paper.docx`](paper/research_paper.docx)

---

## 🔬 Core Empirical Findings

This study evaluates two non-invasive black-box uncertainty indicators in **Llama-3.2-3B** under an auxiliary query budget of $B = 2$: **numerical verbalized confidence** ($s_{\text{conf}} \in [0, 100]$) and **structured zero-shot self-verification** ($s_{\text{check}} \in \{\text{YES}, \text{NO}\}$).

1. **Pathological Confidence Inversion on Symbolic Mathematics:**
   On MMLU Abstract Algebra ($N=100$), confidence displays severe inversion: the model assigned an average subjective confidence of **$42.9\%$ to incorrect answers**, contrasted with only **$32.9\%$ to correct completions**. This inverts error-risk AUROC to **$0.384$** (substantially below random guessing).
2. **Resolution via MMLU Biology Validation:**
   Evaluating 310 MMLU Biology instances under identical conditions proves that confidence inversion is domain-specific to symbolic deduction: in factual biology, accuracy rises to **$67.7\%$**, mean confidence is **$+10.1\text{ pp}$** higher on correct answers ($66.3\%$ vs. $56.2\%$), error AUROC restores to **$0.548$**, and false reassurance drops to $29.1\%$.
3. **High False Reassurance Rate ($42.6\%$):**
   Across the primary reasoning cohort, the model endorsed 249 responses as valid, of which **106 were objectively false**.
4. **Out-of-Domain Threshold Collapse:**
   In Leave-One-Domain-Out (LODO) cross-validation, static decision thresholds fitted on auxiliary domains fail under domain shift: collapsing MMLU coverage to $2\%$ (coverage starvation) while unselectively admitting $96\%$ of ARC-Challenge responses without error filtration.

---

## 📊 Summary Results Table

| Domain | Cognitive Type | N | Accuracy (%) | Conf Delta (Corr - Err) | Error AUROC | Error AUPRC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **GSM8K** | Multi-Step Arithmetic | 100 | 67.0% | +19.7 pp (71.2 / 51.5) | 0.632 | 0.399 |
| **MMLU Biology** | Factual Life Science | 310 | 67.7% | +10.1 pp (66.3 / 56.2) | 0.548 | 0.354 |
| **ARC-Challenge** | Commonsense / QA | 100 | 61.0% | +7.3 pp (79.4 / 72.1) | 0.475 | 0.401 |
| **MMLU Algebra** | Symbolic / Abstract | 100 | 31.0% | **-10.0 pp (32.9 / 42.9)** | **0.384 (Inverted)** | 0.636 |

---

## 📂 Repository Structure

```text
.
├── README.md                            # Repository documentation & guide
├── LICENSE                              # MIT License
├── requirements.txt                     # Python dependencies
├── audit_status.md                      # Audit log certifying provenance & quarantine checks
├── paper/
│   ├── research_paper.pdf               # Final 8-page IEEE conference paper (PDF)
│   └── research_paper.docx              # Editable IEEE conference Word document
├── notebooks/
│   ├── LLM_Trust_Calibration_Research.ipynb   # Colab notebook: Primary benchmark inference
│   └── MMLU_Biology_Validation_Colab.ipynb    # Colab notebook: GPU Biology validation
├── code/
│   ├── reproduce_analysis.py            # Standalone deterministic evaluation script
│   ├── trust_evaluator.py               # Interactive CLI risk-scoring demo
│   ├── generate_ieee_architecture.py    # Architecture diagram generator (Fig. 1)
│   ├── generate_comparative_figures.py  # Cross-disciplinary figure generator (Fig. 3 & Fig. 4)
│   └── build_final_ieee_manuscript.py   # Automated IEEE manuscript compiler
├── data/
│   ├── approved_analysis_data.csv       # Primary audited 300 instances
│   ├── correction_log.csv               # Confirmed GSM8K label corrections (IDs 327, 358, 370)
│   ├── dataset_manifest.csv             # Manifest of included & quarantined datasets
│   └── human_review.csv                 # Flagged boundary cases
└── results/
    ├── final_metrics.csv                # Baseline evaluation metrics
    ├── fold_metrics.csv                 # Leave-One-Domain-Out cross-validation results
    ├── selective_prediction_coverage.csv# Selective accuracy vs. target coverage
    ├── failure_cases.csv                # Catalog of 89 failure cases across 4 archetypes
    └── figures/
        ├── fig_architecture.png         # Fig. 1: System architecture
        ├── fig1_domain_calibration.png  # Fig. 2: Calibration curves
        ├── fig2_domain_auroc.png        # Fig. 3: Error AUROC across 4 domains
        ├── fig5_symbolic_vs_factual_calibration.png # Fig. 4: Metacognitive contrast
        └── fig3_risk_coverage_curve.png # Fig. 5: Risk-coverage trade-off curves
```

---

## 🚀 Quickstart & Reproduction

### 1. Installation
Install runtime dependencies (no GPU required):
```bash
git clone https://github.com/akgetscreative-wq/slm-trust-calibration.git
cd slm-trust-calibration
pip install -r requirements.txt
```

### 2. Reproduce All Metrics and Tables
Recompute all baseline metrics, cross-validation folds, and selective prediction coverage sweeps:
```bash
python code/reproduce_analysis.py --data data/approved_analysis_data.csv --out results
python code/generate_comparative_figures.py
```

### 3. Run the Interactive Risk Evaluator
Test the black-box risk estimator with custom certainty and verification verdicts:
```bash
# High confidence, confirmed self-check -> Accepted
python code/trust_evaluator.py --confidence 90 --self-check YES

# Low confidence, rejected self-check -> Abstain / Human Escalation
python code/trust_evaluator.py --confidence 30 --self-check NO
```

### 4. Rebuild the IEEE Research Paper (DOCX & PDF)
Recompile the 8-page IEEE conference document from scratch:
```bash
python code/build_final_ieee_manuscript.py
```

---

## 📓 Google Colab Notebooks

All original model inference runs on **Llama-3.2-3B** were executed using Google Colab on an **NVIDIA Tesla T4 GPU (16 GB)**:
- **`notebooks/LLM_Trust_Calibration_Research.ipynb`**: Original 37-cell notebook running Ollama, prompt extraction, and scoring.
- **`notebooks/MMLU_Biology_Validation_Colab.ipynb`**: Factual biology validation running 310 items under budget parity $B = 2$.

---

## 📜 Citation

If you find this work or dataset useful in your research, please cite:

```bibtex
@inproceedings{kumar2026slmtrust,
  author    = {Kumar, Aayush},
  title     = {When Should a Small Language Model Be Trusted? Evaluating Verbalized Confidence and Self-Verification Under Domain Shift},
  booktitle = {IEEE Conference Proceedings},
  year      = {2026},
  url       = {https://github.com/akgetscreative-wq/slm-trust-calibration}
}
```

---

## ⚖️ License
This project is licensed under the [MIT License](LICENSE).
