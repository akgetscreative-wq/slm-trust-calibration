"""
generate_comparative_figures.py
Generates publication-quality IEEE comparative figures including the landmark
Symbolic (Algebra) vs. Factual (Biology) confidence calibration contrast.
"""

import matplotlib.pyplot as plt
import numpy as np
import os

os.makedirs('submission/results/figures', exist_ok=True)

# 1. Figure: Confidence Alignment Delta Across Domains
# Showing Mean Confidence for Correct vs Incorrect answers
domains = ['GSM8K\n(Arithmetic)', 'MMLU Biology\n(Factual Science)', 'ARC-Challenge\n(Commonsense QA)', 'MMLU Algebra\n(Symbolic Math)']
conf_correct = [71.2, 66.3, 79.4, 32.9]
conf_wrong = [51.5, 56.2, 72.1, 42.9]
deltas = [c - w for c, w in zip(conf_correct, conf_wrong)]

x = np.arange(len(domains))
width = 0.35

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 3.4), dpi=300)

# Panel A: Correct vs Incorrect Confidence
rects1 = ax1.bar(x - width/2, conf_correct, width, label='Correct Answers', color='#1f77b4', edgecolor='black', linewidth=0.8)
rects2 = ax1.bar(x + width/2, conf_wrong, width, label='Incorrect Answers', color='#d62728', edgecolor='black', linewidth=0.8)

ax1.set_ylabel('Mean Self-Reported Confidence (%)', fontsize=9, fontweight='bold')
ax1.set_title('(a) Confidence by Ground-Truth Correctness', fontsize=9.5, fontweight='bold', pad=8)
ax1.set_xticks(x)
ax1.set_xticklabels(domains, fontsize=7.5)
ax1.set_ylim(0, 100)
ax1.legend(loc='upper right', fontsize=8, frameon=True)
ax1.grid(True, linestyle='--', alpha=0.5)

# Value annotations
for rect in rects1:
    h = rect.get_height()
    ax1.annotate(f'{h:.1f}%', xy=(rect.get_x() + rect.get_width()/2, h),
                xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=7, fontweight='bold')
for rect in rects2:
    h = rect.get_height()
    ax1.annotate(f'{h:.1f}%', xy=(rect.get_x() + rect.get_width()/2, h),
                xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=7)

# Panel B: Metacognitive Alignment Delta (Correct - Incorrect)
colors = ['#2ca02c' if d > 0 else '#d62728' for d in deltas]
bars = ax2.bar(domains, deltas, color=colors, width=0.5, edgecolor='black', linewidth=0.8)
ax2.axhline(0, color='black', linewidth=1.0, linestyle='-')
ax2.set_ylabel('Alignment Delta: Conf(Corr) - Conf(Err) (pp)', fontsize=9, fontweight='bold')
ax2.set_title('(b) Metacognitive Calibration Directionality', fontsize=9.5, fontweight='bold', pad=8)
ax2.set_xticks(range(len(domains)))
ax2.set_xticklabels(domains, fontsize=7.5)
ax2.set_ylim(-16, 26)
ax2.grid(True, linestyle='--', alpha=0.5)

for bar in bars:
    yval = bar.get_height()
    va = 'bottom' if yval >= 0 else 'top'
    offset = 2 if yval >= 0 else -10
    label = f'+{yval:.1f} pp' if yval > 0 else f'{yval:.1f} pp\n(INVERTED)'
    ax2.annotate(label, xy=(bar.get_x() + bar.get_width()/2, yval),
                xytext=(0, offset), textcoords="offset points", ha='center', va=va, fontsize=7.5, fontweight='bold')

plt.tight_layout()
out_path = 'submission/results/figures/fig5_symbolic_vs_factual_calibration.png'
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
print(f'Saved {out_path} successfully')

# 2. Update AUROC comparison plot to include Biology
plt.figure(figsize=(4.2, 3.2), dpi=300)
all_domains = ['GSM8K\n(Math)', 'MMLU Bio\n(Science)', 'ARC\n(QA)', 'MMLU Alg\n(Algebra)']
conf_aurocs = [0.632, 0.548, 0.475, 0.384]
check_aurocs = [0.584, 0.540, 0.509, 0.511]

x = np.arange(len(all_domains))
w = 0.35

plt.bar(x - w/2, conf_aurocs, w, label='Verbalized Conf Risk', color='#1f77b4', edgecolor='black', linewidth=0.8)
plt.bar(x + w/2, check_aurocs, w, label='Binary Self-Check Risk', color='#ff7f0e', edgecolor='black', linewidth=0.8)

plt.axhline(0.50, color='red', linestyle='--', linewidth=1.2, label='Random Chance (0.50)')
plt.ylabel('Error-Ranking AUROC', fontsize=9, fontweight='bold')
plt.title('Error Discrimination AUROC by Task Category', fontsize=9.5, fontweight='bold', pad=8)
plt.xticks(x, all_domains, fontsize=8)
plt.ylim(0.25, 0.75)
plt.legend(loc='lower left', fontsize=7.5, frameon=True)
plt.grid(True, linestyle='--', alpha=0.5)

for i, v in enumerate(conf_aurocs):
    plt.text(i - w/2, v + 0.015, f'{v:.3f}', ha='center', fontsize=7, fontweight='bold')
for i, v in enumerate(check_aurocs):
    plt.text(i + w/2, v + 0.015, f'{v:.3f}', ha='center', fontsize=7)

plt.tight_layout()
out_auroc = 'submission/results/figures/fig2_domain_auroc.png'
plt.savefig(out_auroc, dpi=300, bbox_inches='tight')
plt.close()
print(f'Saved {out_auroc} successfully')
