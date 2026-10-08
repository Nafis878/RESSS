# Certified alarm thresholds (CAT): definitions, results and proofs

The conformal order-statistic argument is established mathematics, specialized here to alarm trajectories; it is not a new general theorem. Numerical checks: `contrib/test_cat.py`
(unit tests T1–T7) and `contrib/cat_sim.py` (Parts A–C); results in `results/contrib/`.

## Setting

A unit has life $L$ (cycles) and, at cycles $t = 1, \dots, L-1$, a causal estimate $x_t$ (the smoothed output of a
regressor whose training does not involve this unit). For a threshold $\tau$ and debounce $k$ the alarm time is

$$t(\tau) = \min\{t : x_s \le \tau \text{ for } s = t-k+1, \dots, t\}\quad(\infty \text{ if no such } t).$$

A decision map $g$ (non-decreasing; $g(t)=t$ for decisions at every cycle, $g(t)=\max(\Delta T, \lceil t/\Delta T\rceil\Delta T)$
on a decision grid) and a lead time $\ell \ge 0$ define a **planned replacement** when $t(\tau) < \infty$ and
$g(t(\tau)) + \ell < L$ (with $g(t)=t$ this is "true remaining life at the alarm $> \ell$", the rule of
`rev_experiments.cost_of`; with the grid and $\ell=0$ it is the rule of `kam_fd001.grid_cost`). Otherwise the unit fails
before replacement (an **unplanned failure**), $F(\tau) = 1$.

## Lemma 1 (monotonicity)

Let $m_t = \min_{s \le t} \max(x_{s-k+1}, \dots, x_s)$ (debounced running minimum; $+\infty$ for $t<k$). Then
$t(\tau) = \min\{t : m_t \le \tau\}$, $t(\tau)$ is non-increasing in $\tau$, and $F(\tau)$ is non-increasing in $\tau$.

*Proof.* The alarm condition at $t$ is $\max(x_{t-k+1..t}) \le \tau$; the first $t$ at which it holds is the first $t$ at
which the running minimum of these window maxima is $\le \tau$. Because $m_t$ is non-increasing in $t$, the set
$\{t: m_t \le \tau\}$ is a terminal segment that grows with $\tau$, so its minimum does not increase. $g$ is
non-decreasing, so $g(t(\tau)) + \ell$ does not increase either, and a planned replacement at $\tau$ stays planned at every
$\tau' > \tau$. $\square$

## Lemma 2 (critical threshold)

Let $t_{\max} = \max\{t \le L-1 : g(t) + \ell < L\}$ (the last admissible alarm time; the admissible times form an initial
segment because $g$ is non-decreasing), and $\tau^* = m_{t_{\max}}$ ($+\infty$ if no time is admissible). Then
$$F(\tau) = \mathbf 1\{\tau < \tau^*\}\quad\text{for every }\tau.$$
On a finite threshold grid $\mathcal T$, with $\tau^*_{\mathcal T} = \min\{\tau \in \mathcal T : \tau \ge \tau^*\}$
($+\infty$ if none), $F(\tau) = \mathbf 1\{\tau < \tau^*_{\mathcal T}\}$ for $\tau \in \mathcal T$.

*Proof.* A replacement is planned iff $t(\tau) \le t_{\max}$, i.e. iff some $t \le t_{\max}$ has $m_t \le \tau$, i.e.
(monotonicity of $m$) iff $m_{t_{\max}} \le \tau$. On the grid, $\tau \ge \tau^*$ iff $\tau \ge \tau^*_{\mathcal T}$ for
$\tau \in \mathcal T$. $\square$

The critical threshold is the *lowest level the debounced estimate reaches before it is too late to act*. Checked
numerically in T2 (closed form = grid score from the alarm tables, leads 0–15, grids 1, 5, 10).

## Theorem 1 (standard conformal rank guarantee applied to a fixed alarm rule)

Let $S_1, \dots, S_{n+1}$ be almost surely finite critical thresholds (on $\mathcal T$ or continuous)
of $n$ calibration units and one new unit, computed with a rule (model, setting, $\ell$, $g$) that does not depend on these
$n+1$ units, and assume $(S_1, \dots, S_{n+1})$ is exchangeable (e.g. i.i.d. units). Let $\alpha \in (0,1)$,
$k = \lceil (n+1)(1-\alpha) \rceil \le n$ and $\hat\tau = S_{(k)}$, the $k$-th smallest calibration score. Then
$$P\{F_{n+1}(\hat\tau) = 1\} = P\{S_{n+1} > \hat\tau\} \le 1 - \frac{k}{n+1} \le \alpha,$$
and, if the scores are almost surely distinct, $P\{F_{n+1}(\hat\tau)=1\} = 1 - k/(n+1) > \alpha - 1/(n+1)$.

*Proof.* By Lemma 2, $F_{n+1}(\hat\tau) = \mathbf 1\{S_{n+1} > S_{(k)}\}$. If $S_{n+1} > S_{(k)}$, at least $k$ of
$S_1,\dots,S_n$ are strictly smaller than $S_{n+1}$. Among $n+1$ numbers, at most $n+1-k$ can each exceed at least $k$
of the others strictly (sort them; only those in positions $k+1, \dots, n+1$ can). Let $A_j$ be the event that $S_j$
strictly exceeds at least $k$ of the other $n$ scores; $\sum_j \mathbf 1_{A_j} \le n+1-k$, and by exchangeability
$P(A_j)$ does not depend on $j$, so $P(A_{n+1}) \le (n+1-k)/(n+1)$. Since $k \ge (n+1)(1-\alpha)$, this is
$\le \alpha$. With distinct scores, $S_{n+1} > S_{(k)}$ iff the rank of $S_{n+1}$ among all $n+1$ is $> k$, which by
exchangeability has probability exactly $(n+1-k)/(n+1)$, and $k < (n+1)(1-\alpha) + 1$ gives $> \alpha - 1/(n+1)$. $\square$

If $k > n$ (i.e. $\alpha < 1/(n+1)$) no finite order statistic certifies the level: **a certificate requires
$\alpha \ge 1/(n+1)$**. If $S_{(k)} = +\infty$ no threshold in the grid certifies it. Both cases are reported as "not
certifiable"; the implementation then falls back to the largest threshold, which carries no guarantee.

**Corollary 1 (selection above the certified threshold).** For any $\tau'$ with $\tau' \ge \hat\tau$, even chosen from the
data, $F_{n+1}(\tau') \le F_{n+1}(\hat\tau)$ pointwise (Lemma 1), so $P\{F_{n+1}(\tau')=1\} \le \alpha$. In particular
CAT-c, which minimises the training cost rate over $\tau \ge \hat\tau$, keeps the guarantee.

**Corollary 2 (cost per renewal).** With cost 1 for a planned and $\rho$ for an unplanned replacement, the expected cost of
the next renewal cycle is $1 + (\rho-1)P(F=1) \le 1 + (\rho-1)\alpha$. (No bound on the long-run cost *rate* follows,
because the expected cycle length depends on the threshold.)

**Corollary 3 (earliest of K, CAT-KMIN).** Let model $j$ ($j=1..K$) be trained without calibration fold $j$ and without the
new unit, $\hat\tau_j$ the certified threshold at level $\alpha$ from fold $j$ (scores under model $j$), and the alarm the
earliest of the $K$ alarms. The combined replacement is planned if any member's is (the earliest alarm leaves the most
time, $g$ is non-decreasing), so $F \le \min_j F_j$ and $P(F=1) \le \min_j P(F_j=1) \le \alpha$. Each member needs
$\alpha \ge 1/(n_j+1)$ with $n_j$ the size of fold $j$.

**Scope of the implementation.** CAT-CF calibrates on inner out-of-fold scores and applies the threshold to a refitted
model, so exchangeability of scores is not established. CAT-SPLIT and CAT-KMIN also select $(cap, span, debounce)$ using
the calibration units' outcomes and therefore are not exact implementations of the fixed-rule theorem. An exact SPLIT
design must fix all model, preprocessing and alarm settings without using its held-out calibration units. An exact KMIN
design must do so separately for each member. Bonferroni can protect selection over $G$ fixed rules if every member
already has valid scores; it cannot repair refitting. The implementation uses $G=36$, requiring $n \ge 36/\alpha-1$
for that finite order statistic, although the plan's illustrative count was 27.

With $+\infty$ scores, the rank bound controls the joint event that a finite certificate is issued and the new score
exceeds it. It does not establish risk conditional on certification succeeding. Maximum-threshold fallbacks, no
admissible action times and infeasible threshold domains must be reported separately; they inherit no general bound.
The empirical binomial screening is descriptive, because the overlapping cross-validation fits induce dependence.

## Theorem 2 (fragility of plain cost minimisation as a selection effect)

Let $G$ settings each have grid critical thresholds $S_i(g)$, and let plain minimisation choose $(\hat g, \hat\tau)$ with
the lowest training cost rate over all settings and grid thresholds. Suppose some setting has a finite zero-failure
threshold on the training units ($\max_i S_i(g) < \infty$ for some $g$). Then:

(a) there is $\bar\rho < \infty$ such that for $\rho > \bar\rho$ the selected policy has no training failure and
$\hat\tau = \max_{i \le n} S_i(\hat g)$ whenever the training cost rate strictly decreases as $\tau$ decreases among
zero-failure thresholds (later alarms, longer use), and in any case $\hat\tau \ge \max_{i\le n} S_i(\hat g)$;

(b) if the $n+1$ score vectors $(S_i(1), \dots, S_i(G))$ are exchangeable,
$$P\{F_{n+1} = 1\} \le \sum_{g=1}^{G} P\{S_{n+1}(g) > \max_{i\le n} S_i(g)\} \le \frac{G}{n+1},$$
and for $G = 1$ with a.s. distinct scores and selection exactly at the zero-failure edge, $P\{F_{n+1}=1\} = 1/(n+1)$ exactly. Above that edge only the upper bound follows.

*Proof.* (a) A threshold with $f \ge 1$ training failures has training cost rate at least $(n-1+\rho)/U_{\max}$, where
$U_{\max}$ is the largest total use over all settings and thresholds; a zero-failure threshold has rate $n/U$ with
$U \ge U_{z} > 0$. For $\rho > \bar\rho = n U_{\max}/U_z - n + 1$ every zero-failure threshold is cheaper, so the minimiser
has zero training failures, i.e. $\hat\tau \ge S_i(\hat g)$ for all $i$ (Lemma 2). Among the zero-failure thresholds of a
setting the cost rate is $n/U(\tau)$ and $U$ is non-increasing in $\tau$ (Lemma 1), so the smallest such threshold,
$\max_i S_i(\hat g)$, is a minimiser (the unique one if $U$ is strictly decreasing). (b) $F_{n+1} = 1$ iff
$S_{n+1}(\hat g) > \hat\tau$, which implies $S_{n+1}(\hat g) > \max_{i\le n} S_i(\hat g)$, so the event lies in the union over
$g$; each event in the union is "the new unit is the strict maximum of $n+1$ exchangeable scores", probability
$\le 1/(n+1)$ (equal with distinct scores). $\square$

Interpretation: for one setting with distinct exchangeable scores, selecting the exact zero-training-failure edge fails
a new unit with probability $1/(n+1)$; selecting above the edge can reduce this probability. Searching $G$ settings gives
the stated union-bound upper limit, not a universal inflation factor. Equality requires the relevant maximum-score
events to be disjoint and selection to expose their union; independent events alone do not attain the bound exactly.
The simulation quantifies the correlated and independent examples. For finite $\rho$ the minimiser may accept training failures, and then no bound of this
form holds. CAT replaces "no training failure" by an explicit order statistic, and Corollary 1 lets cost tuning operate
only above it.

## Per-time-step conformal bounds give no unit-level guarantee

Even a valid per-time-step lower bound $x_t - q_{1-\alpha}$ with marginal coverage $\ge 1-\alpha$ for a specified random
(unit, cycle) pair does not establish an alarm-level guarantee. The implemented baseline pools residuals $x_t-r_t$ over
all cycles of calibration units; those dependent cycles do not automatically satisfy pointwise conformal exchangeability,
so even its pointwise finite-sample coverage is not guaranteed here. An alarm
at the first cycle where the bound is $\le \ell$ is a threshold policy with $\tau = \ell + q$; its unit-level failure
probability is $P(S > \ell + q)$, which is not controlled by $\alpha$ in either direction because the residual distribution
over all cycles is not the distribution of the critical threshold. In both simulation models it was far below $\alpha$
(≈ 0) with thresholds 4–20 times those of CAT (Part A), i.e. extremely early replacement. No theorem is claimed.

## Secondary: interval for M (Kamariotis et al.)

$M = R/R_p - 1$, $R = \sum C_i/\sum T_i$, $R_p = \sum C_{p,i}/\sum T_{p,i}$ (grid-perfect policy on the same units). With
$\psi_i = [(C_i - R T_i)/\bar T - (R/R_p)(C_{p,i} - R_p T_{p,i})/\bar T_p]/R_p$, the first-order (delta-method) expansion gives
$\hat M - M \approx n^{-1}\sum_i \psi_i$ and $\widehat{\mathrm{Var}}(\hat M) = \sum_i \psi_i^2/n^2$; $\sum_i \psi_i = 0$
exactly. This is a standard ratio-estimator linearisation (asymptotic, i.i.d. units, finite second moments), not a new
theorem. It gives zero width for the perfect policy, whose $M$ is 0 by definition, whereas their Eq. 7 does not. In the
coverage study (Part C) it did **not** improve coverage: when $M$ is driven by rare failures, every first-order interval
and the percentile bootstrap undercovered badly at $n = 20$ and $n = 100$.
