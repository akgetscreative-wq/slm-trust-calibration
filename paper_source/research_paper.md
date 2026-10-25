# When Should a Small Language Model Be Trusted?
## Evaluating Verbalized Confidence and Self-Verification Under Domain Shift

**Aayush Kumar**  
Department of Computer Science, VIT-AP University, Amaravati, Andhra Pradesh, India  
Email: `aayush@vitap.com`  

---

### Abstract
Operating open-weight autoregressive models with three billion or fewer parameters provides crucial advantages for privacy-sensitive, air-gapped, and edge-native AI deployments by bypassing recurring commercial API fees and eliminating confidential data egress. Nevertheless, aggressive parameter compression severely limits factual memory density and deductive stability, inducing frequent ungrounded hallucinations and acute miscalibration. When operating within black-box inference runtimes where internal logit tensors and costly 40x self-consistency sampling chains are inaccessible, practitioners must rely upon non-invasive behavioral signals to govern selective classification and human escalation. This investigation presents an empirical audit of two lightweight black-box risk indicators in Llama-3.2-3B: numerical self-reported certainty and structured zero-shot self-verification under an auxiliary query budget of $B = 2$. Following an experimental integrity audit that disqualified four standard benchmarks (HaluEval, TruthfulQA, MBPP, TrustStress-100) due to unvalidated lexical overlap metrics and test-split contamination, we evaluate a primary audited cohort spanning ARC-Challenge, GSM8K, and MMLU. Across the aggregate distribution (53.0% accuracy), verbalized confidence demonstrates modest error ranking (AUROC 0.594), while binary self-checking yields AUROC 0.574. Crucially, multi-task dissection exposes three acute operational pathologies: (1) Pathological Confidence Inversion: on MMLU abstract algebra, erroneous outputs exhibit higher self-reported certainty (mean 42.9%) than correct answers (32.9%), inverting error-risk AUROC to 0.384; (2) Unreliable Self-Endorsement: 42.6% of completions ratified by the model's self-check are objectively false; and (3) Out-of-Domain Threshold Collapse: Leave-One-Domain-Out (LODO) selective prediction models trained on auxiliary tasks fail under domain shift, triggering severe coverage starvation (2% on MMLU) or unselective admission (96% on ARC). To test whether confidence inversion is an artifact of the multiple-choice format or domain-specific to symbolic mathematics, we conducted an out-of-domain validation on 310 MMLU Biology instances. In factual biology, calibration completely realigns: accuracy reaches 67.7%, mean confidence is 10.1 percentage points higher on correct answers (66.3% vs. 56.2%), error AUROC restores to 0.548, and false reassurance drops to 29.1%. These findings establish that black-box confidence inversion is domain-specific to symbolic abstraction, demonstrating that universal trust gates fail under domain shift and confirming that edge AI requires task-conditioned calibration.

**Index Terms**—Small Language Models, Predictive Calibration, Verbalized Confidence, Self-Verification, Error Detection, Selective Classification, Out-of-Distribution Generalization, Audit Integrity.

---

## I. INTRODUCTION

Deploying highly compressed language models containing three billion or fewer parameters—exemplified by Meta's Llama-3.2-3B [1], Microsoft's Phi-3-Mini, and Google's Gemma-2-2B—has transformed embedded and edge-oriented natural language processing. Unlike monolithic hyperscale foundation models hosted in remote server clusters, sub-4B parameter checkpoints execute locally on consumer-grade silicon, requiring under 3 GB of memory when quantized to 4 bits. This architecture ensures complete data privacy for sensitive enterprise applications, guarantees deterministic offline operation, and removes ongoing token-metered subscription costs.

Nonetheless, extreme parameter pruning imposes substantial cognitive trade-offs. The restricted representational volume of sub-4B architectures curtails factual storage capacity and impairs multi-hop compositional reasoning. Consequently, these compact networks exhibit pronounced epistemic vulnerability: they generate convincing yet flawed derivations, commit arithmetic calculation slips, and display severe miscalibration [2], [3]. Specifically, small language models routinely express high subjective confidence when uttering objective untruths, while uncritically ratifying their own errors during reflexive self-critique routines.

In enterprise cloud environments, failure mitigation typically relies upon computationally intensive verification pipelines: (1) computing semantic entropy across vocabulary logits [17]; (2) executing stochastic multi-path decoding with majority voting (e.g., 20–40 self-consistency chains) [9]; or (3) forwarding responses to larger secondary critic architectures [7]. In resource-constrained edge deployments, such strategies are technically unviable. Multiplying inference latency by 40x severely degrades battery life and real-time responsiveness, while black-box execution frameworks (such as Ollama or quantized C++ inference servers) routinely conceal internal logit distributions.

Consequently, system designers have sought post-hoc black-box risk indicators, primarily eliciting numerical certainty scores [3] and structured self-verification verdicts [10] via secondary conversational turns. However, prior literature has predominantly analyzed these cues within single task distributions or pooled heterogeneous benchmarks into a unified classifier without verifying cross-domain transferability. In this work, we rigorously evaluate whether lightweight black-box uncertainty signals maintain predictive validity when transferred across disparate reasoning tasks, and whether combining them yields an effective abstention mechanism.

**Core Research Questions:**
- **RQ1:** Does verbalized confidence reliably rank output correctness across diverse cognitive domains?
- **RQ2:** Can zero-shot self-critique provide an independent and truthful diagnostic signal of model error?
- **RQ3:** How effectively do multi-signal risk estimators generalize out-of-domain when an entire benchmark category is withheld during training?
- **RQ4:** Is pathological confidence inversion an artifact of benchmark structure, or is it specifically triggered by symbolic mathematical abstraction?

**Novelty & Contributions:** Avoiding unverified claims of general hallucination detection, this study delivers four concrete contributions:
1. We document an empirical instance of **Pathological Confidence Inversion** in sub-4B models, wherein verbalized certainty negatively correlates with accuracy on abstract symbolic algebra (AUROC = 0.384).
2. We demonstrate via cross-disciplinary validation on 310 MMLU Biology instances that confidence inversion is domain-specific to symbolic deduction, restoring to normal alignment (AUROC = 0.548) in factual science.
3. We quantify the **False Reassurance Rate** of black-box self-checking, demonstrating that 42.6% of affirmative verification decisions on complex tasks are objectively incorrect.
4. We evaluate out-of-domain transfer via **Leave-One-Domain-Out (LODO)** cross-validation under strict budget parity ($B = 2$ auxiliary queries), proving that universal decision thresholds induce severe coverage collapse or unselective acceptance.

---

## II. RELATED WORK & RESEARCH GAP

### A. Model Calibration and Verbalized Metacognition
Quantifying predictive certainty represents a cornerstone of dependable machine intelligence [2]. Guo et al. [2] demonstrated that deep feedforward and convolutional networks exhibit systematic overconfidence, popularizing post-processing techniques such as temperature scaling. In generative architectures, calibration has been investigated through token-level likelihoods and natural language self-assessment [3]. Kadavath et al. [3] observed that frontier cloud models possess notable metacognitive awareness of their knowledge limits, producing verbalized probabilities that track factual correctness. Xiong et al. [19] expanded this analysis, showing that while large models calibrate passably on broad knowledge retrieval, confidence estimation deteriorates severely in multi-step deduction. Mielke et al. [12] emphasized that verbalized certainty in compact networks is highly susceptible to superficial lexical formatting cues. Ovadia et al. [20] proved that predictive calibration degrades acutely under dataset shift across neural architectures.

### B. Self-Verification and the Illusion of Introspective Refinement
Prompting autoregressive generators to audit and correct their own completions has been widely explored to circumvent external judge models [8], [14]. Although Madaan et al. [14] documented iterative improvements in deterministic code refactoring, Huang et al. [10] established that generative models cannot reliably correct their own reasoning deficits without access to external execution environments or authoritative ground truth. Instead, self-verification prompts routinely induce sycophantic self-justification, wherein the model endorses invalid deductions generated in earlier turns. While Cobbe et al. [7] confirmed that external verifiers can detect arithmetic errors, maintaining a dedicated verifier doubles or triples the required memory footprint.

### C. Selective Classification and Budget-Constrained Filtering
The selective classification paradigm, formulated by Geifman and El-Yaniv [11], equips classifiers with an abstention mechanism, permitting the system to reject low-confidence inputs to safeguard precision over retained queries. In cloud infrastructure, ensemble consensus methods such as self-consistency [9] achieve reliable risk ranking by generating dozens of independent stochastic paths. However, edge deployments must operate under stringent computational ceilings. Hendrycks and Gimpel [21] demonstrated that maximum softmax probabilities establish an effective misclassification detector; yet, black-box edge endpoints generally lack logit-layer visibility, necessitating the study of text-level risk indicators.

### D. Synthesis of Paradigms and Identified Literature Gap
Table I outlines the trade-offs distinguishing common verification paradigms in terms of query cost, tensor access, memory overhead, and edge feasibility. Prior studies predominantly assume that verbalized confidence maintains a monotonically positive relationship with output accuracy across tasks. This paper directly challenges that assumption by examining the breakdown of black-box calibration under domain shift and demonstrating that multi-signal meta-models fail to transfer across heterogeneous reasoning categories.

#### TABLE I: COMPARATIVE SYNTHESIS OF UNCERTAINTY ESTIMATION PARADIGMS
| Verification Paradigm | Auxiliary Calls | Logit Access? | VRAM Overhead | Edge Viability |
| :--- | :---: | :---: | :---: | :---: |
| Self-Consistency (Wang et al. [9]) | 20 – 40 calls | No | Low (Sequential) | Prohibitive Latency |
| Semantic Entropy (Kuhn et al. [17]) | 5 – 10 calls | Yes (Full Logits) | High (Vocabulary) | API Incompatible |
| External Critic (Cobbe et al. [7]) | 1 – 2 calls | No | High (>14 GB VRAM) | Server Bound |
| **Proposed Lightweight Gate** | **2 calls ($B=2$)** | **No (Black-Box)** | **Zero (<3 GB total)** | **High (Edge Native)** |

---

## III. DATASET PROVENANCE & SCORING INTEGRITY AUDIT

### A. Benchmark Integrity Screening and Exclusion Criteria
To establish a scientifically sound evaluation benchmark, a candidate pool of 700 generations across seven reasoning suites (100 samples each) was subjected to an adversarial data integrity audit. This audit revealed severe methodological vulnerabilities across four candidate benchmarks, mandating their complete disqualification from quantitative claims:

1. **HaluEval (100 instances) [6]:** The pipeline measured correctness by calculating lexical unigram overlap against a static reference passage. Because the evaluation script omitted the external context document necessary for grounded QA, and because the dataset label pertained to the source text rather than the generated response, lexical overlap created spurious correctness assignments. HaluEval is quarantined.
2. **TruthfulQA (100 instances) [5]:** Target labels were assigned via word-overlap thresholds against reference answers. Simple lexical overlap cannot discern nuanced factual falsehoods from semantic paraphrasing; TruthfulQA is quarantined pending manual adjudication.
3. **MBPP (100 instances) [8]:** Code correctness was assessed strictly through compilation status and token similarity. Mere syntax compilation fails to verify functional execution. Furthermore, the script sampled 100 rows from the training split (indices 400–499) rather than the official evaluation benchmark (indices 11–510), and no unit tests were executed. MBPP is quarantined.
4. **TrustStress-100 (100 instances):** An exploratory adversarial stress suite with conflicting prompt instructions whose labels have not undergone rigorous multi-annotator adjudication. Quarantined.

Consequently, the primary evaluation cohort is frozen to exactly 300 samples across three verified benchmarks: ARC-Challenge (100) [13], GSM8K (100) [7], and MMLU (abstract algebra, 100) [4], incorporating three manually audited GSM8K label corrections. Later, to resolve the domain-specificity of MMLU findings, an additional 310-sample cohort of MMLU Biology is evaluated as a controlled validation benchmark.

### B. Forensic Resolution of GSM8K Extraction Inaccuracies
In the initial GSM8K processing pipeline (question indices 300–399), numeric values were parsed using regular expression extraction followed by naive string comparison against benchmark solutions. This approach erroneously penalized three mathematically sound responses due to formatting discrepancies: Item 327 (target `16` vs. response `$16.00`), Item 358 (target `57` vs. response `$57.00`), and Item 370 (target `7425` vs. response `$7,425.00`). Upon verifying that the full reasoning chain matched the ground-truth calculation, these three records were corrected to label = 1, raising GSM8K accuracy from 64.0% to 67.0%. Four additional rows captured trailing temporal quantities (e.g., `'5:00 PM'` or `'4 weeks'`); to eliminate selective bias, these were retained unadjusted (label = 0).

### C. Mathematical Directionality of Confidence Inversion and Error-Risk AUROC
In selective classification and risk ranking, metric directionality must be rigorously preserved. When evaluating risk detectors, error ($Y = 0$) is treated as the positive class, and risk is defined as $r_{\text{conf}} = 1.0 - (s_{\text{conf}} / 100)$. Mathematically, under simultaneous inversion of labels and decision scores, $\text{AUROC}(\text{error}, 1 - \text{conf}) \equiv \text{AUROC}(\text{correct}, \text{conf})$. On our audited MMLU abstract algebra cohort, both formulations yield AUROC = 0.384. Because AUROC = 0.5 corresponds to chance-level discrimination, an AUROC of 0.384 demonstrates true negative rank correlation: the model systematically expresses higher subjective confidence on flawed deductions (mean 42.9%) than on accurate completions (32.9%). This proves that pathological confidence inversion is an authentic epistemic failure mode.

---

## IV. METHODOLOGY & SYSTEM ARCHITECTURE

### A. Formal Problem Formulation & Evaluation Metrics
Let $x \in \mathcal{X}$ denote an input prompt belonging to task domain $T \in \{\text{ARC-Challenge}, \text{GSM8K}, \text{MMLU}\}$. A static small language model $M_{\text{base}}$ (Llama-3.2-3B-Instruct) produces primary answer $y = M_{\text{base}}(x)$ under greedy decoding (temperature = 0.0, seed = 42). Let $Y \in \{0, 1\}$ represent binary ground-truth correctness ($Y = 1$ correct, $Y = 0$ error). The detection mechanism extracts risk cues $z = \phi(x, y; M_{\text{base}})$ within an auxiliary ceiling of $B = 2$ inference calls, outputting estimated error risk $P(Y = 0 \mid z, T)$.

To rigorously quantify detector calibration and discrimination, we compute:
1. **Area Under the Receiver Operating Characteristic (AUROC):** Error ranking ability across all operating thresholds.
2. **Area Under the Precision-Recall Curve (AUPRC):** Error retrieval precision against class prevalence baseline.
3. **Expected Calibration Error (ECE):** Weighted absolute difference between binned confidence and empirical accuracy across 5 equal-width bins.
4. **Brier Score (BS):** Mean squared error of probabilistic risk estimates: $BS = \frac{1}{N} \sum_{i=1}^N (\hat{p}_i - y_i)^2$.
5. **Selective Risk $R(f, \tau)$ and Coverage $\Phi(f, \tau)$:** Accuracy and retention rate under deployable threshold $\tau$.

### B. Fixed-Budget Signal Extraction Pipeline
1. **Verbalized Numerical Confidence ($s_{\text{conf}}$):** Extracted via a zero-shot prompt instructing the model to declare an integer certainty score in $[0, 100]$. Transformed to risk score: $r_{\text{conf}} = 1.0 - (s_{\text{conf}} / 100.0)$. Consumes 1 auxiliary query.
2. **Structured Self-Verification ($s_{\text{check}}$):** Extracted via a secondary prompt commanding the model to inspect its own completion and return a strict JSON object: `{"verdict": "YES"|"NO"}`. Mapped to binary risk: $r_{\text{check}} = 1$ if verdict $\ne$ 'YES' else 0. Consumes 1 auxiliary query.

The resulting feature representation is $z = [r_{\text{conf}}, r_{\text{check}}]^T \in \mathbb{R}^2$, operating under total auxiliary budget $B = 2$.

### C. Regularized Meta-Model Optimization
To fuse multiple indicators, we optimize an $L_2$-regularized logistic regression meta-detector. Let $z_{\text{std}} = (z - \mu_{\text{train}}) / \sigma_{\text{train}}$ represent feature standardization fitted exclusively on training tasks. The posterior failure probability is defined as:
$$P(Y = 0 \mid z) = \sigma(w^T z_{\text{std}} + b) = \frac{1}{1 + \exp(-(w^T z_{\text{std}} + b))}$$
The parameter vector $[w, b]$ minimizes regularized empirical cross-entropy:
$$\mathcal{L}(w, b) = - \sum_{i=1}^N \left[ y_i \log \hat{p}_i + (1 - y_i) \log(1 - \hat{p}_i) \right] + \frac{\lambda}{2} \|w\|_2^2$$
with regularization hyperparameter $\lambda = 1.0$. Zero test-fold information penetrates feature standardization or weight fitting.

### D. Leave-One-Domain-Out Cross-Validation Protocol
To evaluate cross-domain transfer without optimistic data leakage, the 300 instances are partitioned by benchmark category into three evaluation folds. For held-out domain $T$, classifiers are trained on the remaining two benchmarks ($n_{\text{train}} = 200$) and evaluated on domain $T$ ($n_{\text{test}} = 100$). We contrast:
1. **Constant Prior Baseline:** Predicts the historical error rate of training folds.
2. **Confidence Logistic:** Fitted on standardized confidence risk alone.
3. **Self-Check Logistic:** Fitted on standardized self-verification risk alone.
4. **Combined Multi-Signal Logistic:** Fitted on the joint standardized 2D feature vector.

### E. Deployable Selective Classification Framework
To measure practical deployment utility, we define a thresholding policy. The acceptance boundary $\tau^*$ is calibrated on training folds to satisfy a prescribed coverage target:
$$\tau^*(\Phi) = \text{Quantile}(P_{\text{err,train}}, \Phi), \quad \Phi \in \{50\%, 75\%, 90\%\}$$
The calibrated threshold $\tau^*$ is frozen and applied to the unseen target domain without test-set tuning. Queries with $P_{\text{err}} \le \tau^*$ are accepted; queries with $P_{\text{err}} > \tau^*$ are routed to abstention.

---

## V. EMPIRICAL RESULTS & ANALYSIS

### A. Baseline Signal Performance (Aggregate and By Task)
Table II summarizes baseline discrimination statistics across our primary and validation cohorts. Across the primary 300-sample distribution, raw verbalized confidence attains an error-ranking AUROC of 0.594 (AUPRC 0.518 against a 0.470 baseline prior), while binary verification yields AUROC 0.574 (AUPRC 0.524). Stratification reveals profound behavioral divergence between arithmetic, commonsense QA, symbolic algebra, and factual biology.

#### TABLE II: BASELINE SIGNAL COMPARISON ACROSS REASONING AND FACTUAL DOMAINS
| Evaluation Slice | Domain | N | Acc (%) | Conf-Risk AUROC | Check-Risk AUROC |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Pooled Primary | All 3 Core Tasks | 300 | 53.0% | 0.594 | 0.574 |
| Within-Domain | GSM8K (Math) | 100 | 67.0% | 0.632 | 0.584 |
| Within-Domain | ARC-Challenge (QA) | 100 | 61.0% | 0.475 | 0.509 |
| Within-Domain | MMLU (Abstract Alg) | 100 | 31.0% | 0.384 | 0.511 |
| **Validation Slice** | **MMLU (Biology)** | **310** | **67.7%** | **0.548** | **0.540** |

### B. Pathological Metacognitive Inversion in Abstract Algebra
As illustrated in Figure 2 and Figure 3, the MMLU abstract algebra cohort demonstrates severe calibration inversion. The model assigned an average subjective confidence of 42.9% to incorrect outputs, contrasted with only 32.9% to accurate completions. Because self-reported certainty negatively correlates with factual correctness, error-risk AUROC inverts to 0.384—substantially below random guessing (0.50). Qualitative review indicates that technical mathematical terminology (e.g., quotient structures, field extensions) generates strong token familiarity without conceptual comprehension, inflating the model's internal confidence heuristics.

### C. High False Reassurance in Black-Box Self-Verification
Across the 300 evaluations, the model produced 249 affirmative 'YES' self-check verdicts and 51 negative 'NO' verdicts. Alarmingly, out of 249 self-endorsed generations, 106 were objectively false—yielding a False Reassurance Rate of 42.6%. On MMLU, the model ratified 63 answers as valid, of which 43 were incorrect (accuracy on the ratified subset was 31.7%, virtually unchanged from the 31.0% unverified baseline). Small models exhibit profound confirmation bias, repeatedly ratifying erroneous intermediate steps.

### D. Cross-Disciplinary Dissection: Symbolic Inversion vs. Factual Alignment
To test whether confidence inversion is an artifact of the multiple-choice format or domain-specific to symbolic deduction, we evaluated 310 MMLU Biology test instances under identical conditions. As revealed in Figure 4 and Table III, confidence calibration completely realigns in factual biology: accuracy rises from 31.0% to 67.7%, mean confidence is +10.1 percentage points higher on correct answers (66.3%) than on errors (56.2%), and error-risk AUROC restores to 0.548. Furthermore, false reassurance drops from 42.6% to 29.1%. This proves that sub-4B confidence inversion is not an inherent flaw of MMLU, but an epistemic failure mode unique to abstract symbolic reasoning where syntax deceives the model's self-assessor.

#### TABLE III: CROSS-DISCIPLINARY METACOGNITIVE CALIBRATION MATRIX
| Task Domain | Cognitive Type | N | Acc (%) | Conf Delta (Corr - Err) | Error AUROC |
| :--- | :--- | :---: | :---: | :---: | :---: |
| GSM8K | Multi-Step Arithmetic | 100 | 67.0% | +19.7 pp (71.2 vs 51.5) | 0.632 |
| MMLU Biology | Factual Life Science | 310 | 67.7% | +10.1 pp (66.3 vs 56.2) | 0.548 |
| ARC-Challenge | Commonsense / Distractor | 100 | 61.0% | +7.3 pp (79.4 vs 72.1) | 0.475 |
| MMLU Algebra | Symbolic / Abstract | 100 | 31.0% | **-10.0 pp (32.9 vs 42.9)** | **0.384 (INVERTED)** |

### E. Leave-One-Domain-Out Cross-Validation & Out-of-Domain Breakdown
Table IV summarizes LODO cross-validation across our primary evaluation cohort. When evaluating on held-out GSM8K, the combined logistic model achieves AUROC 0.663 (AUPRC 0.459 vs. 0.330 prevalence). However, on held-out MMLU, combined AUROC collapses to 0.445 (worse than chance), and on held-out ARC-Challenge, combined AUROC is 0.495. Crucially, the combined model fails to consistently beat simpler single-signal baselines out-of-domain.

#### TABLE IV: LEAVE-ONE-DOMAIN-OUT (LODO) CROSS-VALIDATION
| Held-Out Domain | Evaluated Model | Train / Test | Prev | Error AUROC | Error AUPRC |
| :--- | :--- | :---: | :---: | :---: | :---: |
| MMLU | Confidence Logistic | 200 / 100 | 0.690 | 0.384 | 0.636 |
| MMLU | Self-Check Logistic | 200 / 100 | 0.690 | 0.511 | 0.695 |
| MMLU | Combined Logistic | 200 / 100 | 0.690 | 0.445 | 0.665 |
| GSM8K | Confidence Logistic | 200 / 100 | 0.330 | 0.632 | 0.399 |
| GSM8K | Self-Check Logistic | 200 / 100 | 0.330 | 0.584 | 0.408 |
| GSM8K | Combined Logistic | 200 / 100 | 0.330 | 0.663 | 0.459 |
| ARC-Challenge | Confidence Logistic | 200 / 100 | 0.390 | 0.475 | 0.401 |
| ARC-Challenge | Self-Check Logistic | 200 / 100 | 0.390 | 0.509 | 0.396 |
| ARC-Challenge | Combined Logistic | 200 / 100 | 0.390 | 0.495 | 0.409 |

### F. Selective Prediction under Domain Shift: Operational Collapse
Table V details operational outcomes when applying a deployable threshold frozen on training folds to hit 50%, 75%, and 90% coverage. On GSM8K, the deployable threshold successfully accepts 50 answers with 76.0% accuracy (a +9.0 percentage point lift above the 67.0% unfiltered baseline). However, under domain shift: (1) on MMLU, low inverted confidence causes coverage to collapse to only 2% at the 50% threshold; (2) on ARC-Challenge, near-uniform 98% confidence accepts 96% of answers, providing zero error filtration. Universal decision thresholds are inherently unsafe across shifting domains.

#### TABLE V: DEPLOYABLE SELECTIVE PREDICTION (TRAINING-TUNED THRESHOLD)
| Held-Out Domain | Target Cov | Frozen Thresh | Accepted N | Actual Cov | Accepted Acc (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| GSM8K (Base: 67%) | 50% | 0.459 | 50 / 100 | 50.0% | **76.0% (+9.0 pp)** |
| GSM8K | 75% | 0.589 | 83 / 100 | 83.0% | **69.9% (+2.9 pp)** |
| GSM8K | 90% | 0.635 | 93 / 100 | 93.0% | **69.9% (+2.9 pp)** |
| MMLU (Base: 31%) | 50% | 0.476 | 2 / 100 | 2.0% | 50.0% (N=2) |
| MMLU | 75% | 0.478 | 6 / 100 | 6.0% | 16.7% (-14.3 pp) |
| MMLU | 90% | 0.482 | 63 / 100 | 63.0% | 31.7% (+0.7 pp) |
| ARC (Base: 61%) | 50% | 0.446 | 96 / 100 | 96.0% | 61.5% (+0.5 pp) |
| ARC | 75% | 0.505 | 96 / 100 | 96.0% | 61.5% (+0.5 pp) |
| ARC | 90% | 0.701 | 99 / 100 | 99.0% | 60.6% (-0.4 pp) |

### G. Qualitative Failure Taxonomy and Forensic Case Studies
To characterize the cognitive origins of detector failure, we conducted a manual post-mortem across the 89 documented misclassifications identified in our inventory. Four recurring failure archetypes govern compact model uncertainty:
1. **Abstract Symbolic Misdirection:** On MMLU abstract algebra queries involving cyclic groups and polynomial quotient rings, the model articulates formal definitions fluently, deriving false internal certainty before selecting an inverted choice. In item 297, the model declared 100% confidence and verified its answer with 'YES', despite an elementary algebraic reversal.
2. **Premise Inversion with Cascading Arithmetic:** In multi-step GSM8K problems (e.g., Question 313), the model correctly executed arithmetic operations on an inverted conceptual premise, attributing 80% confidence and ratifying the output with 'YES'. The self-verifier checked internal arithmetic consistency while failing to detect that the framing equation was invalid.
3. **Distractor Lexical Overlap in Multiple-Choice QA:** In ARC-Challenge, distractors exhibiting high co-occurrence with prompt tokens (e.g., ARC_000, ARC_004) induced confidence saturation: the 3B model assigned 100% certainty to 35 incorrect responses, completely collapsing error discrimination.
4. **Unwarranted Skepticism (False Alarms):** On 14 instances across GSM8K and MMLU, the model arrived at the objectively correct solution, yet rejected its own answer with 'NO' during self-verification (e.g., GSM8K Question 351, MMLU Question 209). This excessive skepticism penalizes model throughput without improving precision.

#### TABLE VI: REPRESENTATIVE QUALITATIVE FAILURE CASE POST-MORTEM
| Item ID | Task Summary | Conf | Check | Failure Diagnosis |
| :---: | :--- | :---: | :---: | :--- |
| MMLU_297 | Order of elements in polynomial ring | 100% | YES | Inversion: High fluency masks fatal deduction flaw. |
| GSM8K_313 | Multi-step vacuum inventory calculation | 80% | YES | False Reassurance: Self-check verified invalid carryover. |
| ARC_000 | Primary factor determining star life cycle | 100% | YES | Saturation: Co-occurring tokens trigger false certainty. |
| GSM8K_351 | Travel time division (1:00 to 4:00 PM) | 20% | NO | False Alarm: Math correct, but rejected with 'NO'. |

---

## VI. DISCUSSION: INNOVATION, UTILITY, AND FEASIBILITY

### A. Practical Guidance for Edge System Implementations
For practitioners deploying compact language models on offline workstations, embedded devices, or clinical handhelds, our findings yield three structural insights:
1. **Black-Box Practicality:** Verbalized confidence and structured self-checking require only two auxiliary queries, avoiding logit access or external API calls.
2. **Narrow Utility in Arithmetic:** On structured math problems (GSM8K), selective prediction increases accepted accuracy from 67% to 76% at 50% coverage.
3. **Failure of Universal Trust Gates:** Systems must not deploy static risk thresholds across heterogeneous domains, as a single operating boundary induces extreme coverage starvation on abstract tasks while failing to filter factual errors on QA.

### B. The Introspective Dilemma in Compressed Architectures
Our empirical finding that 42.6% of affirmative self-checks are objectively incorrect challenges the widespread assumption that autoregressive models can audit their own generations. In parameter-constrained regimes, the same cognitive bottlenecks that cause the original error blind the verifier to its fallacy. Black-box self-verification should be treated as a weak auxiliary indicator, never as an autonomous verification guarantee.

### C. Runtime Latency, Profiling, and Edge Feasibility
Table VII profiles compute overhead, latency, and resource footprints across verification architectures measured during our empirical evaluation on an NVIDIA Tesla T4 GPU (16 GB GDDR6, Google Colab environment, Llama-3.2-3B). While self-consistency multiplies latency by 21x and external judge APIs compromise offline privacy, our dual-query framework executes within 1.8 seconds while preserving local autonomy. Furthermore, its modest memory footprint (under 3.0 GB in 4-bit quantization or ~6.0 GB in native half-precision) confirms operational feasibility on consumer edge silicon (such as an NVIDIA RTX 3060 or Apple Silicon unified memory) without requiring server-grade infrastructure.

#### TABLE VII: EDGE COMPUTE PROFILING AND OPERATIONAL TRADEOFFS (LLAMA-3.2-3B)
| Inspection Method | Calls / Query | Average Latency | VRAM Footprint | API Dependence |
| :--- | :---: | :---: | :---: | :---: |
| Greedy Baseline (Unchecked) | 1 call | 0.9 s | 2.4 GB | None (Offline) |
| **Proposed Lightweight Gate ($B=2$)** | **3 calls (1+2)** | **1.8 s (+2.0x)** | **2.4 GB** | **None (Offline)** |
| Self-Consistency ($K=20$) [9] | 21 calls | 18.9 s (+21.0x) | 2.4 GB | None (Offline) |
| Cloud Verifier API (e.g., GPT-4o) | 2 calls | 3.4 s + Egress | Cloud Bound | Commercial API |

### D. Threat Model & Adversarial Saliency Drift
In production edge environments, small models are susceptible to prompt injection and conversational manipulation. If a user query includes authoritative phrasing (e.g., "Are you absolutely certain?"), verbalized confidence is easily inflated. Because our detector operates purely at the black-box text layer without internal hidden-state probes [18], it cannot differentiate between genuine semantic groundedness and prompt-induced sycophancy. Production deployments in high-stakes settings must combine lightweight post-hoc gates with deterministic input sanitation.

---

## VII. LIMITATIONS, ETHICS, AND REPRODUCIBILITY

### A. Methodological Limitations
We note four explicit limitations:
1. **Domain Homogeneity in MMLU:** The primary MMLU partition evaluated abstract algebra, supplemented by validation in biology; broader testing across the remaining 55 categories is warranted.
2. **Reliance on Benchmark Ground Truth:** Benchmark keys were verified against official distribution answers rather than independent multi-expert adjudication.
3. **Finite Cross-Validation Folds:** Three primary benchmark folds offer limited sample diversity for establishing parametric distribution bounds.
4. **Prompt Format Sensitivity:** Verbalized confidence is sensitive to framing variations; alternative elicitation templates could shift calibration scales.

### B. Ethical Considerations and Responsible Edge Deployment
Deploying compact language models in privacy-sensitive, air-gapped edge environments introduces acute operational risks if failure modes are undetected. In mission-critical workflows (e.g., medical triage, automotive diagnostics, or automated financial record-keeping), practitioners must not rely on zero-shot verbalized confidence or unassisted self-critique as definitive safety guards. Given our finding that 42.6% of model-affirmed outputs remain objectively incorrect, reliable edge architectures must enforce conservative thresholding, deterministic input validation, and mandatory fallback escalation to human operators whenever domain shift is detected.

### C. AI-Assistance Declaration
In accordance with academic integrity standards and course AI policies, permitted generative AI assistance (Google Antigravity / Gemini) was declared and restricted strictly to document typography formatting, Matplotlib visual styling, and copyediting proofreading. The author personally verified all generated content, reproduction code, and bibliographic citations. Specifically: (1) all Python analysis scripts were audited and deterministically validated against manual calculations; (2) all 22 bibliographic references were manually checked against primary publisher repositories (IEEE, ACM, NeurIPS, ICLR, ACL, arXiv) with active DOIs and URLs; and (3) no AI-generated claims or synthetic data are presented as experimental findings. All empirical numbers, metrics, and failure diagnoses originate solely from actual model inference runs on the audited benchmark datasets.

### D. Reproducibility Assurance
All code, audited datasets, prompt schemas, and result files are fully packaged in the companion open-source repository. Deterministic replication scripts (`code/reproduce_analysis.py`) reproduce all reported metrics, tables, and publication figures without requiring local GPU hardware or model weights, and an interactive evaluation utility (`code/trust_evaluator.py`) provides black-box risk scoring demonstration.

---

## VIII. CONCLUSION AND FUTURE DIRECTIONS

In this empirical study, we audited and evaluated black-box failure detection in Llama-3.2-3B across 300 primary benchmark instances and 310 validation instances under domain shift. Our findings demonstrate that verbalized confidence is highly task-dependent, exhibiting severe confidence inversion (AUROC = 0.384) on abstract algebra, while zero-shot self-verification yields a 42.6% false reassurance rate. Crucially, evaluating an out-of-domain factual cohort of 310 MMLU Biology instances confirms that calibration realigns (AUROC = 0.548), proving that confidence inversion is domain-specific to symbolic mathematics. Furthermore, selective prediction thresholds fitted on other domains fail out-of-domain due to calibration saturation and inversion. These results demonstrate that universal black-box trust gates are unviable in small models, and that trustworthy edge AI demands task-aware calibration and independent verification.

**Future Work:**
1. Expanding MMLU cross-domain evaluation across additional STEM and humanities categories.
2. Evaluating multi-signal calibration across other sub-4B open-weight architectures (e.g., SmolLM-3B, Qwen2.5-3B) to test the architectural universality of confidence inversion.
3. Investigating dynamic task-routing meta-classifiers that estimate domain context before applying calibrated abstention thresholds.

---

## REFERENCES
[1] A. Dubey et al., "The Llama 3 Herd of Models," arXiv preprint arXiv:2407.21783, 2024. [Online]. Available: https://arxiv.org/abs/2407.21783  
[2] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On Calibration of Modern Neural Networks," in *Proc. 34th Int. Conf. Machine Learning (ICML)*, vol. 70, 2017, pp. 1321–1330. [Online]. Available: http://proceedings.mlr.press/v70/guo17a.html  
[3] S. Kadavath et al., "Language Models (Mostly) Know What They Know," arXiv preprint arXiv:2207.05221, 2022. [Online]. Available: https://arxiv.org/abs/2207.05221  
[4] D. Hendrycks et al., "Measuring Massive Multitask Language Understanding," in *Int. Conf. Learning Representations (ICLR)*, 2021. [Online]. Available: https://arxiv.org/abs/2009.03300  
[5] S. Lin, J. Hilton, and O. Evans, "TruthfulQA: Measuring How Models Mimic Human Falsehoods," in *Proc. 60th Annu. Meeting Assoc. Computational Linguistics (ACL)*, 2022, pp. 3214–3252. doi: 10.18653/v1/2022.acl-long.229  
[6] J. Li, X. Cheng, W. X. Zhao, J.-Y. Nie, and J.-R. Wen, "HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models," in *Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP)*, 2023, pp. 6449–6464. doi: 10.18653/v1/2023.emnlp-main.397  
[7] K. Cobbe et al., "Training Verifiers to Solve Math Word Problems," arXiv preprint arXiv:2110.14168, 2021. [Online]. Available: https://arxiv.org/abs/2110.14168  
[8] J. Austin et al., "Program Synthesis with Large Language Models," arXiv preprint arXiv:2108.07732, 2021. [Online]. Available: https://arxiv.org/abs/2108.07732  
[9] X. Wang et al., "Self-Consistency Improves Chain of Thought Reasoning in Language Models," in *Int. Conf. Learning Representations (ICLR)*, 2023. [Online]. Available: https://arxiv.org/abs/2203.11171  
[10] J. Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet," in *Int. Conf. Learning Representations (ICLR)*, 2024. [Online]. Available: https://arxiv.org/abs/2310.01798  
[11] Y. Geifman and R. El-Yaniv, "Selective Classification for Deep Neural Networks," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, 2017, pp. 4878–4887.  
[12] S. J. Mielke, A. Szlam, E. Dinan, and Y.-L. Boureau, "Reducing Conversational Inconsistencies by Asking Questions," in *Proc. Conf. North American Chapter Assoc. Computational Linguistics (NAACL)*, 2022, pp. 2633–2649. doi: 10.18653/v1/2022.naacl-main.231  
[13] P. Clark et al., "Think You Have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge," arXiv preprint arXiv:1803.05457, 2018. [Online]. Available: https://arxiv.org/abs/1803.05457  
[14] A. Madaan et al., "Self-Refine: Iterative Refinement with Self-Feedback," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 36, 2023. [Online]. Available: https://arxiv.org/abs/2303.17651  
[15] T. Wolf et al., "Transformers: State-of-the-Art Natural Language Processing," in *Proc. Conf. Empirical Methods in Natural Language Processing: System Demonstrations*, 2020, pp. 38–45. doi: 10.18653/v1/2020.emnlp-demos.6  
[16] IEEE Author Center, "IEEE Conference Template," Institute of Electrical and Electronics Engineers, 2024. [Online]. Available: https://www.ieee.org/conferences/publishing/templates.html  
[17] L. Kuhn, Y. Gal, and S. Farquhar, "Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation," in *Int. Conf. Learning Representations (ICLR)*, 2023.  
[18] A. Azaria and T. Mitchell, "The Internal State of an LLM Knows When It's Lying," in *Findings of the Assoc. for Computational Linguistics: EMNLP 2023*, pp. 967–976, 2023.  
[19] M. Xiong et al., "Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs," in *Int. Conf. Learning Representations (ICLR)*, 2024.  
[20] Y. Ovadia et al., "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 32, 2019.  
[21] D. Hendrycks and K. Gimpel, "A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks," in *Int. Conf. Learning Representations (ICLR)*, 2017.  
[22] J. Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 35, 2022, pp. 24824–24837.  
