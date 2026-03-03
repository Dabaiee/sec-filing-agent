# SEC Filing Intelligence Agent — Scoring & Optimization Loop

You are a project quality evaluator and optimizer. Your job is to score this open-source project against a rubric, identify weaknesses, fix them, and repeat until the score reaches 8.8+/10.

---

## How This Loop Works

Each iteration:
1. Read the ENTIRE codebase (all source files, tests, README, pyproject.toml, CI config)
2. Score every dimension against the rubric below
3. Identify the lowest-scoring dimensions
4. Fix the weakest areas (write code, update docs, add tests, etc.)
5. Git commit your changes
6. Re-score and print the updated scorecard
7. If total score >= 8.8 for BOTH tracks, output <promise>DONE</promise>
8. If not, continue to next iteration

---

## Scoring Rubric

### Track A: Open Source Project Quality (for GitHub stars / developer adoption)

| # | Dimension | Max | Criteria |
|---|-----------|-----|----------|
| 1 | README & First Impression | 1.5 | Has: one-line description, badges (PyPI, CI, license, Python version), Quick Start (3 lines or less), architecture diagram, feature list, usage examples (CLI + Python API), "How it works" section, comparison table vs competitors. Penalty: no GIF placeholder, no live demo link, wall of text |
| 2 | Installation & Onboarding | 1.0 | `pip install sec-filing-agent` works. Entry point `sec-agent` registered. First command works within 60 seconds of install. Clear error message if ANTHROPIC_API_KEY missing. Has `--help` with examples |
| 3 | Code Quality | 1.5 | Type hints everywhere. Pydantic models for all data. Async where appropriate. Clean module structure. No hardcoded values. ruff/mypy pass. Consistent code style. Meaningful variable names. Docstrings on public API |
| 4 | Test Coverage | 1.0 | Tests exist for all major modules. Mocked external calls (SEC API, LLM). Tests actually pass. Edge cases covered (invalid ticker, network error, malformed LLM response). pytest runs clean |
| 5 | Feature Completeness | 1.5 | Core: analyze 10-K, 10-Q, 8-K. Structured JSON output. Model routing. Terminal UI with progress. Bonus: diff/compare, trends, sector analysis, watchlist, Ollama support |
| 6 | Error Handling & UX | 1.0 | Never crashes with raw traceback. Helpful error messages. Graceful degradation (API timeout, rate limit, invalid input). Loading states visible. Cost/token tracking shown |
| 7 | CI/CD & Packaging | 1.0 | pyproject.toml complete (name, version, description, authors, license, entry points, dependencies). GitHub Actions CI (lint + test). Release workflow for PyPI. .gitignore correct. No secrets committed |
| 8 | Architecture & Extensibility | 1.5 | Clean separation: fetcher → classifier → router → analyzer → formatter. Easy to add new filing types or model backends. Dependency injection or config-based model selection. Plugin-friendly design |
| **Total** | | **10.0** | |

### Track B: Resume Portfolio Signal (for job interviews)

| # | Dimension | Max | Criteria |
|---|-----------|-----|----------|
| 1 | Technical Depth Visible | 2.0 | Someone reading the code can immediately see: multi-stage pipeline, model routing logic, structured output validation, retry logic, cost tracking. Architecture is evident from file structure alone |
| 2 | Production Patterns | 1.5 | Error handling, retry with backoff, input validation, rate limiting, caching, logging, config management. Code looks like it was written for production, not a hackathon |
| 3 | AI/LLM Engineering | 2.0 | Prompt templates separated from logic. Structured output with Pydantic validation. Model routing based on task complexity. Token/cost tracking. Retry on malformed LLM response. Multiple model backend support |
| 4 | System Design | 1.5 | Pipeline architecture clear. Components loosely coupled. Easy to understand data flow. Good abstraction boundaries. README or code comments explain WHY, not just WHAT |
| 5 | Developer Experience | 1.0 | Clean public API (`from sec_filing_agent import Agent`). Good CLI with --help. Examples directory with runnable scripts. Type hints enable IDE autocomplete |
| 6 | Documentation Quality | 1.0 | README explains architecture. Code has docstrings on public methods. Examples are self-explanatory. Configuration documented (env vars, CLI flags) |
| 7 | Testing Discipline | 1.0 | Tests are well-organized. Mocking strategy is clean. Test names describe behavior. Both happy path and error cases tested |
| **Total** | | **10.0** | |

---

## Scoring Output Format

After each evaluation, print this EXACT format:

```
═══════════════════════════════════════════════════
ITERATION [N] SCORECARD
═══════════════════════════════════════════════════

TRACK A: Open Source Quality
─────────────────────────────────────────────────
[1] README & First Impression:    X.X / 1.5  | [brief reason]
[2] Installation & Onboarding:    X.X / 1.0  | [brief reason]
[3] Code Quality:                 X.X / 1.5  | [brief reason]
[4] Test Coverage:                X.X / 1.0  | [brief reason]
[5] Feature Completeness:         X.X / 1.5  | [brief reason]
[6] Error Handling & UX:          X.X / 1.0  | [brief reason]
[7] CI/CD & Packaging:            X.X / 1.0  | [brief reason]
[8] Architecture & Extensibility: X.X / 1.5  | [brief reason]
─────────────────────────────────────────────────
TRACK A TOTAL:                    X.X / 10.0

TRACK B: Resume Portfolio Signal
─────────────────────────────────────────────────
[1] Technical Depth Visible:      X.X / 2.0  | [brief reason]
[2] Production Patterns:          X.X / 1.5  | [brief reason]
[3] AI/LLM Engineering:           X.X / 2.0  | [brief reason]
[4] System Design:                X.X / 1.5  | [brief reason]
[5] Developer Experience:         X.X / 1.0  | [brief reason]
[6] Documentation Quality:        X.X / 1.0  | [brief reason]
[7] Testing Discipline:           X.X / 1.0  | [brief reason]
─────────────────────────────────────────────────
TRACK B TOTAL:                    X.X / 10.0

TOP 3 WEAKNESSES TO FIX:
1. [Dimension]: [what's wrong] → [what to do]
2. [Dimension]: [what's wrong] → [what to do]
3. [Dimension]: [what's wrong] → [what to do]

═══════════════════════════════════════════════════
```

---

## Rules

1. **Be HARSH in scoring.** Do not inflate. A 7.0 means "good but has clear gaps." An 8.8 means "I would star this repo and use this in my own workflow."
2. **Read actual code, not just file names.** Open every .py file and evaluate the real implementation.
3. **Test actually pass.** Run `pytest` and verify. If tests fail, score 0 on Test Coverage.
4. **README is evaluated as a user sees it.** Not as a developer who knows the codebase.
5. **Each iteration: fix TOP 3 weaknesses**, then re-score. Do not try to fix everything at once.
6. **Commit after each fix round** with message: "score(vN): X.X/10 A, X.X/10 B — [what was fixed]"
7. **Never output <promise>DONE</promise> unless BOTH tracks are genuinely >= 8.8.** Check the math.
8. **If stuck on a dimension** (e.g., need API key to test), note it and focus on dimensions you CAN improve.
9. **Do not delete or break existing functionality** to improve scores. Only add or refactor.
10. **Maximum improvement per iteration: 3 fixes.** This prevents rushed, low-quality changes.

---

## Completion Criteria

Output <promise>DONE</promise> ONLY when:
- Track A total >= 8.8
- Track B total >= 8.8
- All tests pass
- No ruff/mypy errors
- Git history shows incremental improvement commits
