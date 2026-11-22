# Dynamic leverage slope for ESP

Code: `hy/dynamic_slope.py`. Tests: `tests/test_dynamic_slope.py`.
Methodology 7.2. Related decision page: `docs/decisions/2026-10-22-esp-peer-groups.md`.

**Status: standalone.** `hy.peers` and `scripts/backtest_peers.py` do not use this module yet.
Section 7 says what to do before you connect it.

## 1. The problem

ESP is the log spread of a bond minus the median log spread of its peers.
Some of that gap comes from leverage: a bond with more debt than its peers pays more.

Two ways exist to remove leverage from the gap:

1. **Divide** the spread by leverage (spread per turn, E13). This forces the slope to 1: spreads must rise one for one with leverage.
2. **Regress** ESP on excess leverage, then subtract the fitted part (`esp_lev`, `esp_mlev`). This estimates the slope.

The data says the slope is near 0.11, not 1. So division removes too much, and every highly levered issuer looks rich.
The regression is the better form. But the current regression has three limits:

| Limit | Effect |
|---|---|
| One slope for all bonds | A BB bond and a CCC bond get the same slope. Structural models say the CCC slope is steeper. |
| A new slope each month, from that month only | The slope jumps with noise. The median is +0.11, but 13% of months give a negative slope. |
| Subtract and discard | The decision page found that the part of the gap that leverage explains also predicts return. The current version throws it away. |

This module fixes all three, in four parts.

## 2. Part 1: one slope per rating class

**What it does.** For each month t and rating class k, fit an OLS line of ESP on excess leverage XL:

```
ESP_i = a(k, t) + b_raw(k, t) * XL_i + e_i        (bonds i in class k at month t)
```

**Why.** A firm near default is more sensitive to more debt. So the market charges more per unit of leverage in CCC than in BB.
One pooled slope averages over that difference.

**The standard error.** The bonds of one issuer share the same XL and usually the same error.
A plain standard error treats them as separate facts and so is too small.
The code clusters the standard error by issuer (`gvkey`). With four bonds per issuer, the clustered error is about twice the plain one. A test checks this.

**Minimum size.** A class needs 30 bonds and 10 issuers in the month. Otherwise it gets no own slope that month (`MIN_ROWS`, `MIN_ISSUERS`).

## 3. Part 2: pull each class slope toward the mean of all classes

**What it does.** A small class gives a noisy slope. The code pulls each class slope toward the mean of all classes.
The pull is strong when the class slope is noisy, and weak when it is precise:

```
w(k, t)      = tau2 / (tau2 + se(k, t)^2)
b_pool(k, t) = w * b_raw(k, t) + (1 - w) * mu(t)
```

- `se` is the clustered standard error from part 1.
- `mu` is the mean slope over classes, with weights 1 / (se^2 + tau2).
- `tau2` is how much the true class slopes differ from each other, beyond their noise.

**How tau2 is estimated.** The code uses the DerSimonian-Laird moment estimate. It compares the spread of the class slopes with the spread that their standard errors alone predict.
With only three or four rating classes, one month gives a very noisy tau2, often zero.
So the code averages the monthly estimates over all months up to t, then floors the result at zero.
A first version used one month only. It pulled the BB slope from 0.05 up to 0.10 on test data. The average over past months fixes this.

**Edge cases.**
- tau2 = 0: every class gets `mu`. The data shows no real difference between classes.
- A class has no own slope that month: it gets `mu`.

**What to expect.** A class with a precise slope keeps it. A class with a noisy slope moves toward the mean. A test checks both.

## 4. Part 3: a filter through time that uses only the past

**What it does.** The slope moves through time, but not as fast as the monthly noise suggests.
A local-level Kalman filter updates the slope each month:

```
b_dyn(t) = b_dyn(t-1) + K(t) * (b_pool(t) - b_dyn(t-1))
K(t)     = (P + q) / (P + q + v(t))
```

- `v(t)` is the variance of this month's `b_pool`. A noisy month has a large v, so K is small and the slope moves little.
- `q` is how much the true slope can move in one month. A large q lets the slope follow changes fast.
- `P` is the filter's own variance. It shrinks as months accumulate.

**Point in time.** `b_dyn(t)` uses months up to t only. It never looks forward. A test changes all data after month 30 and checks that every value before month 30 stays the same.

**How to set q.** Use `estimate_q` on the training months only. It uses the fact that for this model, var(change in b_pool) = q + 2 * mean(v).
Never estimate q on the test months.
If `estimate_q` returns 0, the data shows no real movement of the slope. The filter then gives a running precision-weighted mean of the past slopes.

**What to expect.** On test data with a constant true slope, the filter cuts the month-to-month noise of the raw slope by more than three times.
One month's filtered value still has an error band. Read `sqrt(P)` from the slope table to see it.

### Part 3b (optional): does the slope steepen when spreads are wide?

`state_slope` fits, on months before t only:

```
b(s) = a + c * m(s)         (weights 1 / variance of b(s))
b_state(t) = a_t + c_t * m(t)
```

`m` is the spread state: the index spread over its expanding mean. It is feature F0b in PositioningWork (`spec/research/regime_features`).
If c > 0, the market prices leverage more steeply in stress. This is a test of a claim, not a default part.
It needs 24 past months before it gives a value.

## 5. Part 4: split ESP into two signals

**What it does.** Keep both parts of the gap. Do not throw one away:

```
priced_lev = b * XL            (the part of the gap that excess leverage explains)
resid_esp  = ESP - priced_lev  (the rest: the book's relative value)
```

The two parts add back to ESP exactly. A test checks this.

**Why.** The decision page found that the leverage control halves the ESP edge.
So the market does not fully price leverage, or leverage carries a premium. Either way, `priced_lev` may predict return.
Scores for both parts tell you where the edge is. One subtraction cannot tell you that.

## 6. How to call it

```python
from hy.dynamic_slope import dynamic_esp, estimate_q, pool_slopes, class_slopes

# rows: one row per bond and month, with month, rclass, gvkey, esp, xlev
# (from hy.peers.peer_signals: esp_<level> and xlev_<level>, or xmlev_<level> for market leverage)
train = rows[rows.month < cut]
p = pool_slopes(class_slopes(train))
q = estimate_q(p.groupby("month")["mu"].first(), p.groupby("month")["v"].mean())

out, slopes = dynamic_esp(rows, q=q)
# out: rows plus b_dyn, priced_lev, resid_esp
# slopes: per month and class, b_raw, se, tau2, mu, w, b_pool, v, b_dyn, P, K
```

The module works with either leverage measure. Pass `x="xmlev"` for market leverage.

## 7. Before you connect it to the backtest

Do these in order. Each step is one decision.

1. **Record the plan first.** Write the grid in a plan file before any run: the classes, the q rule, the horizons, and the pass rule.
2. **Pass rule.** `resid_esp` passes if it beats plain ESP beyond spread at 12 months (+0.096, t 2.6), with t ≥ 2. Use the same rule as `esp_lev` and `esp_mlev`.
3. **Score `priced_lev` as its own signal.** If it predicts return, report it. Do not call it noise.
4. **Compare like for like.** Score `esp_lev`, `esp_mlev` and the new `resid_esp` on the same rows and months.
5. **Write a decision page.** The repo needs one per design decision. This module does not have one yet.

## 8. Known limits

1. **Few classes.** Three or four rating classes give a weak estimate of tau2. The average over months helps, but early months stay noisy.
2. **Linear inside a class.** Each class still has one straight line. A curve inside a class (for example, a monotone spline) is a possible next step.
3. **The slope is fitted on the same month it is used.** This matches `esp_lev`. Bond spreads at month t are known at t, so this is not look-ahead. But the slope and the ESP come from the same data.
4. **q is fixed per run.** The filter does not learn q as it runs. Set it on the training fold.
5. **Synthetic tests only.** The tests use made-up data with known slopes. No test on the TRACE panel exists yet.
