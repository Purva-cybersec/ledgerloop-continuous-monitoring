# LedgerLoop Continuous Monitoring

Turning controls into code. This project takes controls from my [SOC 2 Type II simulation](https://github.com/Purva-cybersec/soc2-type2-audit-simulation) and checks them automatically against **every record**, instead of a sample. It is built step by step; this is a work in progress.

## Status

| Step | What | Status |
|---|---|---|
| 1 | Python checker for control 7 (terminated users' access removed within 24 hours) | Done |
| 1b | Run checks automatically in GitHub Actions; scan Terraform with Checkov | Planned |
| 2 | AI agent that drafts exception write-ups, with a human approving | Planned |
| 3 | Questionnaire assistant that answers from policy, with citations | Planned |

## About the red X

The check in GitHub Actions is expected to fail. The simulated data contains
four planted exceptions for control 7, so the pipeline reports a failure, which
is the control working as designed. A real pipeline would alert the control
owner in the same way. 

## Run it

```
python checks/control7_termination_access.py
```

Only Python 3.9 or newer is needed. No extra packages.

## How it works

1. `data/hr_terminations.csv` holds the HR termination records (the system of record).
2. `data/entitlements.csv` lists which systems each person had an account in (Okta, AWS, GitHub).
3. `data/removals.csv` holds when each account was removed.
4. The checker joins the three, applies the 24-hour rule, and writes `results/control7_all_results.csv` and `results/control7_exceptions.csv`.

## Limits, stated plainly

- **All data is simulated** and derived from the population in the SOC 2 simulation. No real company data is used.
- **No live connections.** The checker reads exported files. A production version would pull from the HR, Okta, AWS, and GitHub APIs.
- **Identity matching is simplified.** Records are joined on employee ID. Real systems often identify the same person differently (work email, username, service account), which is a harder problem this version does not solve.
- **A learning project**, not a replacement for GRC platforms such as Vanta or Drata.
