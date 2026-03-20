# crypto-strategy-lab

A paper-trading-first crypto strategy research system. Built for reproducibility, safety, and gradual improvement — not hype.

---

## What this is

A layered evaluation framework for testing, comparing, and refining rule-based crypto trading strategies. It starts with free paper trading and grows into a rigorous strategy lab over time.

**This is not a magic AI trader.** It is a research platform that:

- Runs multiple strategy variants safely, in parallel, with no real money at risk
- Logs every trade alongside the market conditions that produced it
- Scores and compares variants using multi-dimensional quality metrics
- Adds smarter selection and prediction layers only once the data justifies it
- Keeps all historical versions alive as benchmarks so progress is always measurable

The first milestone is not profit. It is correctness: the bot runs, logs are clean, and results are comparable.

---

## System layers

The system grows in six layers. Each one builds on the shared foundation below it — nothing is replaced, only extended.

| Layer | Name | Goal |
|-------|------|------|
| 0 | Baseline paper trader | Prove the engine runs and logs are clean |
| 1 | Static variant testing | Compare fixed parameter sets under the same conditions |
| 2 | Leaderboard & champion selection | Rank variants on evidence, not gut feel |
| 3 | Controlled refinement | Generate small mutations near successful variants |
| 4 | Regime awareness | Learn which variants work best in which market conditions |
| 5 | Prediction / confidence layer | Score setups based on historical outcomes |
| 6 | Optional live micro-allocation | Only after paper evidence is sustained and reproducible |

---

## Repository structure

```
/executor/      Freqtrade config and dry-run setup
/strategies/    Strategy definitions
/variants/      Parameter sets per variant
/schemas/       Trade log and market context schemas (shared data contract)
/metrics/       Scoring and reporting logic
/selector/      Champion/challenger selection
/refinement/    Controlled parameter mutation
/reports/       Generated output reports
/docs/          Architecture notes, setup guides, decision records
```

---

## Getting started

### Prerequisites

- Python 3.10+
- Git

### Setup

```bash
# Clone the repo
git clone https://github.com/f1cklepickle/crypto-strategy-lab.git
cd crypto-strategy-lab

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies (once requirements.txt exists)
pip install -r requirements.txt
```

### Secrets

```bash
# Copy the example env file — never commit .env
cp .env.example .env
```

Edit `.env` and fill in values only when needed. For paper trading (Layer 0–5), no API key is required.

---

## Security policy

- **No API keys are ever committed to this repo** — not even read-only ones
- All secrets live in `.env`, which is gitignored
- `.env.example` contains only placeholder values
- The virtual environment (`venv/`) is gitignored and never committed
- Freqtrade runtime data (`user_data/`, logs, databases) is gitignored
- Live trading permissions are never granted to any key until Layer 6 is reached and justified

See `docs/security.md` for full policy.

---

## Design philosophy

**Start boring.** No fancy AI first. One strategy, a few variants, reliable logs, good reports.

**Add complexity only after evidence.** Don't build predictive logic until there are enough logged outcomes to justify it.

**Make every decision explainable.** Which variant was active. Why it traded. Why it was promoted. Why it was pruned.

**Build like a lab, not a black box.** Every stage is a release. Older versions stay testable.

---

## Status

Currently in **pre-Layer 0** setup. Active issues tracked [here](https://github.com/f1cklepickle/crypto-strategy-lab/issues).

---

## License

MIT
