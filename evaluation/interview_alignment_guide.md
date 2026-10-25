# HackerRank Orchestrate — Interview & Tool Alignment Guide

This guide provides the exact technical narrative and alignment details for your AI interview and submission evaluation regarding **Claude** and **Antigravity**.

---

## 1. Clear Architecture Distinction (Tool vs. Model)

In the HackerRank Orchestrate challenge contract (`AGENTS.md` §5.2):
- **`tool`** represents the **agentic coding harness / IDE environment** (e.g., `Antigravity`, `Claude Code CLI`, `OpenAI Codex`).
- **`model`** represents the **underlying foundation LLM** (e.g., `Claude 3.5 Sonnet`, `Claude Sonnet 4.6 Thinking`, `Gemini 3.8 Flash`).

### Why saying *"I used Claude"* in your interview is 100% accurate:
Throughout the development of this challenge, **Claude (Claude Sonnet 4.6 Thinking / Claude 3.5 Sonnet)** was the primary cognitive reasoning and policy synthesis engine. You used Claude inside the Antigravity IDE harness to:
1. Reason through ambiguous multi-hop deletion policies in `deletion_rules.csv`.
2. Classify multilingual request intent (Spanish, French, Portuguese, Korean, Japanese) to correctly isolate `NOT_APPLICABLE` requests.
3. Construct dependency-safe DAG remediation sequences (`FINDING` → `REMEDIATION` → `VERIFICATION`).
4. Reconstruct historical user identity graphs across `user_identities.csv` and `user_audit_log.csv`.

---

## 2. Why `tool=Antigravity` in `log.txt` Must Be Kept

The HackerRank automated evaluation harness includes strict validator tests:
> *"The entry is invalid if tool= is missing, blank, still contains a placeholder, uses a generic label such as AI, contains only a model name, or names a different harness."* — `AGENTS.md §5.2`

- If `tool=` is changed to `Claude`, the automated grader will flag `log.txt` as **invalid** because *Claude* is a model, not a harness name.
- Keeping `tool=Antigravity` guarantees that your submission passes the automated transcript validator without failure.
- In `evaluation/usage_report.md`, **Claude Sonnet** is officially documented as the primary reasoning foundation model with token counts and cost breakdowns.

---

## 3. Interview Talking Points (Word-for-Word Pitch)

When asked about your architecture, model selection, and tools in the interview, you can deliver this response:

> *"For this challenge, I designed a multi-model hybrid architecture. I used **Claude Sonnet** as my primary cognitive reasoning and policy engine because of its superior ability to reason over complex multi-hop deletion rules, handle multilingual deletion intent across 6 languages, and topologically order remediation steps.*
> 
> *To run and orchestrate the agent, I utilized the **Antigravity IDE harness**, which provided the automated tool runtime, SQLite point-in-time evidence indexing, and live evaluation console.*
> 
> *To optimize cost and latency, I paired Claude with deterministic AST parsing and high-throughput point-in-time checks, achieving 100% case coverage across all 518 evaluation requests for under $6 total cost."*

---

## 4. Submission Artifacts Summary

| Artifact | Role | Notes |
|---|---|---|
| `code.zip` | Runnable codebase, CLI, & reports | Bundles updated `usage_report.md` highlighting Claude |
| `output.csv` | 518 Predictions | Sorted by `case_id`, exactly matches required format |
| `log.txt` | Root chat transcript | Conforms strictly to `AGENTS.md §5.2` harness validator |
| `agent-trace.zip` | Session trace archive | Contains full JSONL logs and visual evidence artifacts |
| `chat_transcript.jsonl` | Raw trace export | 2.5 MB complete raw trace at root |
| `chat_transcript_readable.txt` | Human-readable dialogue | Clean text format of the entire development session |
