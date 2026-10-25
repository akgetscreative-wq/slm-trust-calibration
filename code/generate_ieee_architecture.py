"""
generate_ieee_architecture.py
Generates Figure 1 for the IEEE Research Manuscript:
Architecture of the Empirical Trust Calibration and Domain Shift Evaluation Framework.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_diagram():
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color palette (IEEE clean aesthetic)
    c_blue = '#EBF3FB'
    c_gen = '#D0E1F9'
    c_sig = '#FFF2CC'
    c_eval = '#FCE5CD'
    c_res = '#E2F0D9'
    border = '#2B3A42'

    # Title
    ax.text(50, 96, "SYSTEM ARCHITECTURE: ZERO-API TRUST CALIBRATION & DOMAIN-SHIFT EVALUATION",
            ha='center', va='center', fontsize=11, fontweight='bold', color='#111111')
    ax.text(50, 92, "Empirical Evaluation of Black-Box Error Detection in Llama 3.2 3B under Fixed Inference Budget (B = 2)",
            ha='center', va='center', fontsize=8.5, fontstyle='italic', color='#555555')

    # Box 1: Input Query & Domain
    b1 = patches.FancyBboxPatch((3, 66), 18, 16, boxstyle="round,pad=0.8",
                               facecolor=c_blue, edgecolor=border, linewidth=1.2)
    ax.add_patch(b1)
    ax.text(12, 77, "Input Query (x)", ha='center', va='center', fontsize=9.5, fontweight='bold')
    ax.text(12, 72, "Domain Context (T)\n• ARC-Challenge (Science)\n• GSM8K (Math)\n• MMLU (Abstract Alg)", 
            ha='center', va='center', fontsize=7.5)

    # Box 2: Primary Generation
    b2 = patches.FancyBboxPatch((26, 66), 22, 16, boxstyle="round,pad=0.8",
                               facecolor=c_gen, edgecolor=border, linewidth=1.2)
    ax.add_patch(b2)
    ax.text(37, 77, "Primary Generation", ha='center', va='center', fontsize=9.5, fontweight='bold')
    ax.text(37, 71, "Llama-3.2-3B-Instruct\n(4-bit Q4_K_M GGUF)\nGreedy Decoding (T=0.0)\nCandidate Answer y", 
            ha='center', va='center', fontsize=7.5)

    # Arrow 1 -> 2
    ax.annotate('', xy=(26, 74), xytext=(21, 74),
                arrowprops=dict(arrowstyle="->", lw=1.3, color='#333333'))

    # Box 3: Fixed Budget Uncertainty Extraction (B=2 calls)
    b3 = patches.FancyBboxPatch((53, 62), 44, 24, boxstyle="round,pad=0.8",
                               facecolor=c_sig, edgecolor='#B45F06', linewidth=1.3, linestyle='--')
    ax.add_patch(b3)
    ax.text(75, 82, "Fixed-Budget Signal Extraction (B = 2 Additional Forward Passes)", 
            ha='center', va='center', fontsize=9, fontweight='bold', color='#B45F06')
    ax.text(75, 75, "1. Verbalized Confidence: s_conf in [0, 100] -> Normalized Risk: r_conf = 1 - (s_conf / 100)\n"
                    "2. Structured Self-Check: Strict JSON {'verdict': 'YES'|'NO'} -> Binary Risk: r_check in {0, 1}\n"
                    "Feature Vector: z = [r_conf, r_check]^T (Strict Zero Logit Access Required)", 
            ha='center', va='center', fontsize=7.5, family='monospace')

    # Arrow 2 -> 3
    ax.annotate('', xy=(53, 74), xytext=(48, 74),
                arrowprops=dict(arrowstyle="->", lw=1.3, color='#333333'))

    # Fork down to Evaluation & Modeling
    ax.plot([75, 75], [62, 48], color='#333333', lw=1.3)
    ax.plot([26, 75], [48, 48], color='#333333', lw=1.3)
    ax.plot([26, 26], [48, 43], color='#333333', lw=1.3)
    ax.plot([75, 75], [48, 43], color='#333333', lw=1.3)

    # Box 4: LODO Cross-Validation
    b4 = patches.FancyBboxPatch((6, 22), 40, 21, boxstyle="round,pad=0.8",
                               facecolor=c_eval, edgecolor='#C55A11', linewidth=1.3)
    ax.add_patch(b4)
    ax.text(26, 39, "Leave-One-Domain-Out (LODO) Evaluation", ha='center', va='center', fontsize=9, fontweight='bold', color='#C55A11')
    ax.text(26, 32, "• Train on 2 domains (n=200); Test on held-out 3rd (n=100)\n"
                    "• StandardScaler fitted STRICTLY on Training Folds\n"
                    "• Models: Baseline Prior, Confidence-Only, Self-Check, Combined Logistic\n"
                    "• Key Finding: In-domain fit collapses out-of-domain", 
            ha='center', va='center', fontsize=7.5)

    # Box 5: Deployable Selective Prediction Policy
    b5 = patches.FancyBboxPatch((52, 22), 44, 21, boxstyle="round,pad=0.8",
                               facecolor=c_res, edgecolor='#385723', linewidth=1.3)
    ax.add_patch(b5)
    ax.text(74, 39, "Selective Prediction & Abstention Gate", ha='center', va='center', fontsize=9, fontweight='bold', color='#385723')
    ax.text(74, 32, "• Threshold tau fixed on Training Folds for target coverage (50%, 75%, 90%)\n"
                    "• Frozen Decision Policy:\n"
                    "    Accept answer if P_err <= tau_fixed; else Flag / Abstain\n"
                    "• Outcome: GSM8K lifts acc +9.0 pp, but MMLU suffers 2% coverage collapse", 
            ha='center', va='center', fontsize=7.5)

    # Arrow Down to Operational Decision
    ax.annotate('', xy=(26, 12), xytext=(26, 22), arrowprops=dict(arrowstyle="->", lw=1.3, color='#333333'))
    ax.annotate('', xy=(74, 12), xytext=(74, 22), arrowprops=dict(arrowstyle="->", lw=1.3, color='#333333'))

    # Box 6: Operational Routing Output
    b6 = patches.FancyBboxPatch((15, 2), 70, 10, boxstyle="round,pad=0.6",
                               facecolor='#F2F2F2', edgecolor='#555555', linewidth=1.1)
    ax.add_patch(b6)
    ax.text(50, 7, "Operational Action: [ACCEPT (High Stated Certainty) | FLAG FOR AUDIT | ABSTAIN]\n"
                   "(Empirical Caution: 42.6% of Affirmative Self-Checks were Erroneous; Confidence Inverts on MMLU)", 
            ha='center', va='center', fontsize=8, fontweight='bold', color='#222222')

    plt.tight_layout()
    plt.savefig('submission/results/figures/fig_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created submission/results/figures/fig_architecture.png successfully")

if __name__ == '__main__':
    create_diagram()
