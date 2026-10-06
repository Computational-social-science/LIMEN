## B. Formal framework

This appendix states the protocol's machinery as mathematics. Everything here is formalized in Lean 4, core-only, with every theorem checked at the kernel level; the formal names are given so that each proposition can be located in the development. Nothing in this appendix is empirical: **no theorem can settle whether noise changes any of these quantities, and that is the empirical claim of the study (§B.5).**

### B.1 Definitions

A **trial** is a pair $o = (c, y) \in \mathcal{O}$ where $c \in \mathbb{N}$ is the reported confidence on a fixed integer scale and $y \in \{0,1\}$ indicates correctness against the item's constructive gold label. A **sample** is a finite list $T = [o_1, \dots, o_n]$.

**Definition 1 (the gate).** For a threshold $\tau$, the gate admits $o$ iff $c \ge \tau$:

$$\mathrm{Adm}_\tau(o) \;=\; [\,c \,\ge\, \tau\,].$$

**Definition 2 (accepted set, coverage).** With $|\cdot|$ the list length,

$$\mathrm{Accepted}_\tau(T) \;=\; \sum_{o \in T} \mathrm{Adm}_\tau(o), \qquad \mathrm{Cov}_\tau(T) \;=\; \frac{\mathrm{Accepted}_\tau(T)}{|T|}.$$

**Definition 3 (silent error and conditional error).** The silent error counts trials that are *both* admitted and wrong; the conditional error is its rate among admitted trials:

$$\mathrm{Risk}_\tau(T) \;=\; \sum_{o \in T} \bigl[\mathrm{Adm}_\tau(o) \wedge \lnot y_o\bigr], \qquad \mathrm{CondErr}_\tau(T) \;=\; \frac{\mathrm{Risk}_\tau(T)}{\mathrm{Accepted}_\tau(T)}.$$

The distinction between $\mathrm{Risk}_\tau$ (a count over the whole sample) and $\mathrm{CondErr}_\tau$ (a ratio whose denominator moves with $\tau$) is not cosmetic; it decides which estimator is available (§B.4).

**Definition 4 (discrimination).** For samples of correct and incorrect confidences $C = [c : (c,1) \in T]$ and $E = [c : (c,0) \in T]$, the ordered-pair count and the associated AUC are

$$W(C, E) \;=\; \sum_{c \in C} \#\{\,e \in E : e < c\,\}, \qquad \mathrm{AUC}(T) \;=\; \frac{W(C,E)}{|C| \cdot |E|}.$$

### B.2 What is assumed, and what is only defined

Two things are **assumed**, and they are the only assumptions.

**(A1) Exchangeability.** Within a unit (an item crossed with a seed), the two arm labels are exchangeable under the null that the manipulation does not change the joint distribution of $(c, y)$. This is what licenses an exact permutation distribution rather than an asymptotic one.

**(A2) Monotone confidence encoding.** If a collection of confidences is transformed by any strictly increasing map, the *ordering* relations among them are preserved. This is a property of the encoding, not a claim about calibration; §B.4 shows why the distinction matters.

Everything else is a **definition**, including $\mathrm{Adm}$, $\mathrm{Cov}$, $\mathrm{Risk}$, $\mathrm{CondErr}$ and $\mathrm{AUC}$. In particular, no assumption is made that confidence is calibrated, well-ordered, or comparable across arms.

### B.3 Propositions with proof outlines

**Proposition 1 (accepted set is monotone in the threshold).** *For $\tau_1 \le \tau_2$ and any $T$, $\mathrm{Accepted}_{\tau_2}(T) \le \mathrm{Accepted}_{\tau_1}(T)$.* Formal name `accepted_mono`. *Proof.* $c \ge \tau_2$ implies $c \ge \tau_1$ by transitivity, so each indicator is pointwise non-increasing; a sum of pointwise non-increasing indicators is non-increasing. The order relation on thresholds is also characterised as an equivalence, `admissible_iff_limen_le`.

**Proposition 2 (coverage is non-increasing in the threshold).** Formal name `coverage_mono`. *Proof.* Immediate from Proposition 1 after dividing by the positive constant $|T|$; recorded separately because coverage is a dependent variable and the division by a fixed denominator is what makes the `Nat`-arithmetic statement non-trivial in the formalization.

**Proposition 3 (the silent-error count is NON-INCREASING in the threshold).** *For $\tau_1 \le \tau_2$, $\mathrm{Risk}_{\tau_2}(T) \le \mathrm{Risk}_{\tau_1}(T)$.* Formal name `risk_mono`.

> **This proposition refuted the protocol.** The protocol originally asserted the *opposite* — that raising the threshold could only increase the silent-error count. The kernel proved otherwise, and the refutation is preserved in the development as `protocol_said_nondecreasing_is_FALSE` so that the error is visible rather than quietly corrected. The direction matters because it is the formal reason the original H1.2 could not hold: **a fixed-threshold silent-error rate cannot rise under a manipulation that deflates confidence**, since deflation moves trials out of the accepted set entirely.

*Proof.* By case analysis on whether a trial is bad at the higher threshold. If $c \ge \tau_2$ and $y = 0$ then $c \ge \tau_1$, so the same trial is bad at the lower threshold and contributes no increase; if not, it contributes nothing at either. Induction over the list.

**Proposition 4 (existence and optimality of a least admissible threshold).** *There is a total order in which a least admissible threshold exists (`admissible_exists`, `top_admissible`), and the most lenient admissible threshold maximises coverage (`least_admissible_maximises_coverage`) while admitting at least as many trials as any other admissible choice (`least_admissible_is_at_least_as_good`).* *Proof.* Admissibility is downward closed by Proposition 1, so the admissible set is an initial segment of the threshold order; its maximum is the least restrictive choice, and Proposition 1 gives the coverage comparison.

**Corollary 4.1 (`clean_pins_at_floor`).** *If the clean arm's silent-error count already satisfies the budget at the lowest admissible threshold, the selector returns that floor for every sample size and every budget.* The selection rule therefore reports **a design constant rather than an estimate** whenever the clean arm is at the floor, which is why the dev-fitted threshold cannot be read as a quantity the data discovered.

**Proposition 5 (small-$N$ degeneracy).** *If the error budget is $\varepsilon$ and $N$ is a sample size with $\lfloor \varepsilon N \rfloor = 0$, the minimum admissible threshold is the all-reject threshold.* Formal names `budget_collapses_to_zero_on_small_dev`, `empty_dev_is_degenerate`. *Proof.* The budget admits zero errors; any threshold admitting a wrong trial violates it; by Proposition 3 the count is non-increasing in $\tau$, so the admissible set shrinks to the single all-reject point. At $\varepsilon = 0.05$ this bites below $N = 20$. `the_threshold_below_the_limen_keeps_only_the_error` records the adjacent pathology: one step below the admissible threshold the retained set is precisely the errors.

**Proposition 6 (accuracy is not diagnostic of understanding).** *Two samples can have identical correctness profiles and different confidence profiles, and the gate's reading of them differs.* Formal names `acc_is_not_diagnostic_of_understanding`, `one_movement_three_readings`, `acc_defers_wrong_mono`, `cond_error_complements_cond_accuracy`. *Proof.* Construct two samples agreeing on $y$ and differing in $c$; the gate admits different subsets, so any quantity computed on the admitted set separates them while accuracy — a function of $y$ alone — does not.

**Corollary 6.1 (the conditional quantities are complements).** `CondErr` and the conditional accuracy among admitted trials sum to one, so the two carry the same information and must not both be counted as evidence. This is the declared dependency that the Holm family must respect.

### B.4 The scale-free result, and why it is load-bearing

**Theorem 7 (scale-free discrimination).** *For any $f : \mathbb{N} \to \mathbb{N}$ that is strictly increasing, and any correct and incorrect confidence lists $C$ and $E$,*

$$W\bigl(f(C), f(E)\bigr) \;=\; W(C, E).$$

Formal name `winsAux_map_of_strictMono`. The kernel reports that this theorem **depends on no axioms at all**, which is a stricter bar than the no-`sorry` discipline applied elsewhere.

*Proof outline.* By induction on $C$. For the inductive step it suffices that the inner count is preserved, `countLt_map`: the number of entries of $f(E)$ strictly below $f(c)$ equals the number below $c$. That in turn needs the order-reflecting property of a strictly increasing map on $\mathbb{N}$, `lt_of_map_lt`: from $f(a) < f(b)$ infer $a < b$. This is proved by trichotomy — $a = b$ makes the images equal, and $a > b$ reverses the inequality by strict monotonicity — so the map reflects order as well as preserving it, and the two predicates agree elementwise.

**Why it matters.** H1.2′ is measured by the AUC, and the AUC is this count divided by a constant. The theorem says the estimand **reads only the ordering of confidences and never their values**, so no strictly increasing miscalibration of the instrument's confidence scale can move it. That is not a convenience: the instrument's own library warns that some confidences are substituted with a constant and are uncalibrated, and an estimand that bounds a *rate* at an absolute threshold would rest precisely on the calibration the warning puts in doubt. The theorem is the formal discharge of the claim that H1.2′ is robust to that warning — and it is the reason the replacement hypothesis was chosen over the two alternatives that were measured and rejected.

### B.5 What is not proved

Nothing in this appendix says that noise changes $\mathrm{Acc}$, $\mathrm{Cov}$, $\mathrm{Risk}$ or $\mathrm{AUC}$. Those are statements about a particular instrument on a particular task, and no theorem can settle them; they are the empirical content of the study, tested by the exact permutation procedure of §D.1 and reported in §D.4. What the formalization does is different and narrower: it fixes what the quantities *are*, proves the relationships that hold by definition, and supplies one theorem — Theorem 7 — that a design choice depends on.
