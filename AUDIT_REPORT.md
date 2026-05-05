# Arkhe Market Codebase Audit Report

**Date:** April 6, 2026  
**Scope:** Full codebase review — bugs, dead code, wiring issues, fragility  
**Files reviewed:** 40+ source files across all modules

---

## CRITICAL BUGS (5 issues — will cause incorrect behavior or crashes)

### 1. Dead code after `return` in `command_center.py` (lines 177–199)

The function `_collect_cost_totals()` returns at line 177, but lines 179–199 contain the entire "Cost Analytics" UI rendering section that **never executes**. This means cost analytics are computed but never displayed. Additionally, the dead section references `show_table` (undefined) instead of `_show_table`.

**File:** `views/command_center.py`  
**Fix:** Remove the dead code. Wire cost analytics and live status into `render_command_center()` as proper function calls.

---

### 2. Session state key mismatch — Neural Score always shows 0.0

In `app.py` line 95, the neural score is stored as:
```python
st.session_state.neural_score = neural_score
```

But in `views/command_center.py` line 82, it's read as:
```python
st.session_state.get('system_neural_score', 0.0)
```

These are **different keys**. The command center always shows `0.0` for the neural score.

**Fix:** Change the command center to read `neural_score` instead of `system_neural_score`.

---

### 3. Entry Gate Threshold step size makes UI unusable

In `app.py` line 73:
```python
st.number_input("Entry Gate Threshold", ..., value=0.75, step=1.0)
```

The `step=1.0` on a value that ranges 0–1 makes fine-tuning impossible via the UI. Clicking the increment button jumps from 0.75 → 1.75 → 2.75, which are meaningless threshold values.

**Fix:** Change `step=1.0` to `step=0.05`.

---

### 4. Neural entry check called twice per cycle (wasted computation)

In `supervisor_agent.py`, `neural_entry_ok()` is called:
- First at line 150 inside `run_experts()` — result stored in panel but **ignored**
- Again at line 220 inside `run_once()` — this is the one actually used

Each call loads the ML model from disk, runs inference, and computes the gate. This doubles the neural overhead per symbol per cycle.

**Fix:** Remove the duplicate call from `run_experts()`.

---

### 5. ML model loaded from disk on every single score call

In `ml/inference/model_service.py`, `load_model()` calls `joblib.load()` **every time** `score_features()` is called. With 20 symbols and 2 neural calls per symbol (entry + exit), that's ~40 disk reads + pickle deserializations per loop cycle.

**Fix:** Cache the model in module-level variables after first load.

---

## HIGH-PRIORITY BUGS (5 issues — degraded behavior)

### 6. `_collect_cost_totals` and `_collect_live_status_rows` defined but never called

Both functions in `command_center.py` are fully implemented but never invoked from `render_command_center()`. The cost analytics section (gross vs net PnL, commission breakdown, execution drag) and live market status table are invisible to the user.

**Fix:** Call both functions and render their output at the bottom of the command center.

---

### 7. CooldownStore creates a new in-memory instance per SupervisorAgent

Each `SupervisorAgent.__init__()` creates `self.cooldowns = CooldownStore()`, which reads `states/cooldowns.json` into its own in-memory dict. If agent A writes a cooldown, agent B's in-memory copy is stale until the next restart. In practice this means cooldowns may not be shared properly across symbols.

**Fix:** Accept a shared `CooldownStore` instance via the constructor, created once in `MultiPortfolioAgent`.

---

### 8. Import-before-docstring in all three market view files

`crypto.py`, `stocks.py`, and `futures.py` all have:
```python
from ml.inference.symbol_scorer import score_symbol
from ml.inference.neural_gate import neural_gate
"""
views/crypto.py – ...
"""
```

The imports before the docstring prevent Python from recognizing the module docstring (it becomes a bare string expression). While not a crash, this breaks documentation tools and is a code smell.

**Fix:** Move imports below the docstring.

---

### 9. Unused imports in all three market view files

Each market view imports a live quotes function that is never called:
- `crypto.py`: `from data.live_quotes import get_crypto_quotes` — unused
- `stocks.py`: `from data.live_quotes import get_stock_quotes` — unused
- `futures.py`: `from data.live_quotes import get_futures_quotes` — unused

**Fix:** Remove the unused imports.

---

### 10. `requirements.txt` missing `plotly` and `joblib`

`ui/charts.py` imports `plotly.graph_objects` but `plotly` is not in `requirements.txt`. `joblib` is used in `ml/inference/model_service.py` — it ships with scikit-learn but should be listed explicitly for clarity.

**Fix:** Add `plotly` and `joblib` to requirements.txt.

---

## MODERATE ISSUES (6 issues — fragility, technical debt)

### 11. `neural_gate.py` default entry threshold is 100,000

```python
entry_threshold = float(st.session_state.get("entry_gate_threshold", 100000.0))
```

If session state hasn't been initialized yet (race condition on first load), this default of 100,000 will block every single entry. The sidebar does set it to 0.75, but any code path that runs before the sidebar renders will see 100,000.

**Fix:** Change default to `0.75` to match the sidebar default.

---

### 12. `feature_logger.py` uses deprecated `datetime.utcnow()`

`datetime.utcnow()` is deprecated in Python 3.12+. The rest of the codebase correctly uses `datetime.now(timezone.utc)`.

**Fix:** Replace with `datetime.now(timezone.utc)`.

---

### 13. `run_loop.py` runs with `test_mode=False` but has no broker connections

The headless loop creates agents with `test_mode=False`, which triggers live-mode safety checks that will immediately block all trading (no broker connected, under minimum balance). This makes the loop script non-functional.

**Fix:** Change to `test_mode=True` or add a command-line flag.

---

### 14. `data.live_quotes` duplicates futures symbol mapping

`data/live_quotes.py` has its own `_yf_symbol_for_futures()` mapping that duplicates (and slightly diverges from) the `FUTURES_YF_MAP` in `data_feeds.py`. The `6E` mapping is `EURUSD=X` in live_quotes but `6E=F` in data_feeds.

**Fix:** Import and use the canonical `FUTURES_YF_MAP` from `data_feeds.py`.

---

### 15. No error handling for missing `arkhe_market_model.pkl`

If the ML model file doesn't exist, `score_features()` returns `None`, which propagates through `score_symbol()` → `neural_entry_ok()` → `neural_gate()`. In `neural_gate.py`, `score is None` returns `"unknown"`, and `neural_entry_ok` returns `allow: True` (gate unknown defaults to allow). This is actually correct fallback behavior but should be documented.

**Status:** Acceptable, no fix needed. Added documentation note.

---

### 16. `backtester.py` writes to `/tmp/bt_state.json` (non-portable)

The backtester hardcodes `/tmp/bt_state.json` which doesn't exist on Windows. Should use `tempfile` module.

**Fix:** Use `tempfile.mktemp()` or a configurable path.

---

## DEAD CODE (4 items)

| File | Item | Notes |
|------|------|-------|
| `coinbase_client.py` | Entire file | Placeholder, unused |
| `data_agent.py` | `DataAgent` class | Raises RuntimeError, unused |
| `agent_prompts.py` | `AGENT_PROMPTS` dict | Role descriptions, never referenced |
| `agent_prompts_v4.py` | Both prompts | Never imported or used |

These are harmless but add noise. Keep `agent_prompts.py` as documentation; the others can be removed.

---

## WIRING ISSUES SUMMARY

| Issue | Symptom | Severity |
|-------|---------|----------|
| Neural score key mismatch | Command center shows 0.0 | Critical |
| Cost analytics dead code | Fee breakdown invisible | Critical |
| Live status rows never rendered | Live eligibility invisible | High |
| Entry threshold step=1.0 | Cannot tune via UI | Critical |
| Model loaded every call | ~40 disk reads per cycle | High |
| Duplicate neural check | Double computation | Medium |
| Stale cooldown instances | Cooldowns may not cross-apply | Medium |

---

## FIXES APPLIED

All 16 issues have been addressed in the codebase:

| # | Issue | File(s) | Status |
|---|-------|---------|--------|
| 1 | Dead code after `return` — cost analytics never rendered | `views/command_center.py` | **Fixed** — moved rendering into `render_command_center()` |
| 2 | Neural score key mismatch (`system_neural_score` vs `neural_score`) | `views/command_center.py` | **Fixed** — reads `neural_score` |
| 3 | Entry gate threshold `step=1.0` on 0–1 range | `app.py` | **Fixed** → `step=0.05`, `max_value=1.0` |
| 4 | Duplicate `neural_entry_ok()` call per cycle | `supervisor_agent.py` | **Fixed** — removed from `run_experts()` |
| 5 | ML model loaded from disk every call (~40×/cycle) | `ml/inference/model_service.py` | **Fixed** — module-level caching |
| 6 | `_collect_cost_totals` and `_collect_live_status_rows` never called | `views/command_center.py` | **Fixed** — wired into render |
| 7 | CooldownStore creates stale per-agent instances | `supervisor_agent.py`, `multi_portfolio_agent.py` | **Fixed** — shared instance |
| 8 | Imports before module docstring | `views/crypto.py`, `stocks.py`, `futures.py` | **Fixed** — docstring first |
| 9 | Unused `get_*_quotes` imports | `views/crypto.py`, `stocks.py`, `futures.py` | **Fixed** — removed |
| 10 | Missing `plotly` and `joblib` in requirements.txt | `requirements.txt` | **Fixed** — added |
| 11 | Neural gate default threshold = 100,000 | `ml/inference/neural_gate.py` | **Fixed** → default `0.75` |
| 12 | Deprecated `datetime.utcnow()` | `ml/features/feature_logger.py` | **Fixed** → `datetime.now(timezone.utc)` |
| 13 | `run_loop.py` uses `test_mode=False` with no broker | `run_loop.py` | **Fixed** → `test_mode=True` |
| 14 | Duplicate futures symbol mapping (diverges for `6E`) | `data/live_quotes.py` | **Fixed** — imports from `data_feeds.FUTURES_YF_MAP` |
| 15 | Backtester hardcodes `/tmp/` (non-portable) | `backtester.py` | **Fixed** → `tempfile.gettempdir()` |
| 16 | Dead code files (coinbase_client, data_agent, agent_prompts) | Various | **Documented** — harmless, kept for reference |

All 79 Python files pass syntax validation.
