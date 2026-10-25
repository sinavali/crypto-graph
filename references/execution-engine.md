# Execution Engine & Context Hygiene Protocol

This specification defines the foundational operational directives for all AI agents and developers interacting with the repository. Antigravity operates with maximum velocity, lowest latency, and highest reasoning quality when operations are batched, output is bounded, and communication is lossless.

---

## 1. Prime Directive P0: Zero-Latency Execution Velocity

### 1.1 Compound Shell Commands (Eliminate Turn Latency)
Every back-to-back `run_command` incurs a full LLM inference roundtrip (4–8 seconds). Sequential tool execution is strictly prohibited when commands can be chained.
- **Forbidden (3 sequential roundtrips = ~20s delay):**
  1. `run_command("git status")`
  2. `run_command("git branch")`
  3. `run_command("git diff --stat")`
- **Mandated (1 roundtrip = ~3s):**
  ```bash
  git status && git branch --show-current && git diff --stat
  ```

### 1.2 Parallel Read & Inspection Calls
When inspecting multiple files or MCP resources, emit all independent tool calls in the **same turn**:
- In a single turn, issue:
  - `view_file` for File A
  - `view_file` for File B
  - `view_file` for File C
Antigravity executes these in parallel, returning all contents in a single payload. Never serialize independent reads across multiple turns.

### 1.3 One-Shot Discovery
Avoid multi-turn probe loops (`test -f`, then `ls`, then `cat`). Combine existence check and reading:
```bash
[ -f config/app.json ] && cat config/app.json | head -n 30 || echo "Not found"
```

---

## 2. Context Window & Token Hygiene Protocol

A polluted context window degrades model reasoning speed, introduces attention blindness, and wastes tokens. Follow these rules to keep context crisp, fast, and high-signal.

### 2.1 Bounded Terminal Command Output
Never run noisy commands directly into the terminal without bounds:
- **Build & Dependency Installs**: Redirect verbose output to temporary files:
  ```bash
  pnpm install --frozen-lockfile > /tmp/pnpm-install.log 2>&1 || cat /tmp/pnpm-install.log | tail -n 40
  cargo build > /tmp/cargo-build.log 2>&1 || cat /tmp/cargo-build.log | tail -n 40
  go build ./... > /tmp/go-build.log 2>&1 || cat /tmp/go-build.log | tail -n 40
  ```
- **Test Suites**: Run targeted test files or filters instead of the entire suite on small iterations:
  ```bash
  pnpm exec nx test <project-name>
  go test -run TestSpecificFunction ./...
  ```
- **Git Diffs**: Check `git diff --stat` first before requesting a raw diff across dozens of files.

### 2.2 Targeted File Inspection
- Never view an 800-line file in its entirety unless strictly necessary. Use `view_file` with `StartLine` and `EndLine` targeting the specific function, class, or section needed.
- Use `ast-grep` or targeted grep (`grep -rn "symbol" path/`) to find exact line numbers first.

---

## 3. Lossless High-Density Communication Protocol

- **Zero Conversational Overhead**:
  - Omit conversational greetings, affirmative fillers ("Certainly", "I'd be glad to help"), and exit pleasantries.
  - Begin immediately with the core action, finding, or solution.
- **Lossless Technical Fidelity**:
  - Never abbreviate, summarize, or truncate code, commands, paths, or configurations that must execute correctly.
  - Retain full error diagnostic context and safety considerations. Code changes remain exact and production-grade.
- **High-Density Output Structure**:
  - Use compact Markdown: bullet lists, structured key-value pairs, or concise tables.
  - Avoid echoing back user questions or re-stating obvious context.
  - Highlight decisions, state transitions, and root causes directly.
