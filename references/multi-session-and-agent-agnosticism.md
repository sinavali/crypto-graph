# Multi-Session Concurrency & Agent Agnosticism Specification

This document establishes the universal protocol for multi-session workspaces, cross-platform agent memory persistence, manifest projection, and tool capability access gates across all agentic AI systems (Antigravity, Claude Code, Cursor, Windsurf, Roo, Codex, Aider, OpenHands).

---

## 1. Multi-Session Workspace Concurrency

Enterprise monorepos frequently host multiple autonomous agents or human-agent pairs working concurrently across distinct subprojects (e.g. Agent 1 on `services/billing`, Agent 2 on `apps/portal-web`). To prevent collision, cross-contamination, and race conditions, the following rules are non-negotiable:

### 1.1 Session Namespace Isolation
Every agent session operates within an isolated session directory:
```text
.ep/sessions/<session_id>/
├── 0001_state.json
├── 0002_state.json
└── current.json -> symlink to latest state
```
- `<session_id>` is alphanumeric with hyphens (e.g. `agent-billing-104`, `claudecode-web-882`).
- Checkpoints are saved as zero-padded sequential integers (`0001`, `0002`, `0003`...). This guarantees that native lexical sorting (`sorted(os.listdir(...))`) always matches exact chronological execution history.

### 1.2 Global Session Registry (`.ep/sessions/registry.json`)
The registry maintains real-time active session leases:
```json
{
  "active_sessions": {
    "agent-billing-104": {
      "subproject": "services/billing",
      "branch": "feat/billing-tax-calc",
      "worktree": "../worktrees/billing-tax-calc",
      "last_heartbeat": "2026-10-17T02:00:00Z",
      "latest_seq": 4,
      "mode": "implement"
    }
  }
}
```
- **Boundary Collisions**: If an agent attempts to declare a Change Surface modifying files in a subproject currently leased by another active session, `ep surface check-diff` issues a blocking concurrency collision warning.

### 1.3 Rolling Retention & Pruning
To prevent repository bloat, `ep session save` enforces an automatic rolling retention limit:
- Maximum retained checkpoints per session: **15 states**.
- When `seq > 15`, checkpoints older than `seq - 15` are automatically pruned.

---

## 2. Universal Agent Manifest Projection

While `AGENT.md` is the canonical root and subproject architectural specification for EP-OS, external agent platforms look for platform-specific instruction files. The monorepo maintains a unified projection engine (`ep manifest sync`) that automatically mirrors `AGENT.md` into all platform files:

```text
               ┌────────────────────────┐
               │    Canonical Source    │
               │        AGENT.md        │
               └───────────┬────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      ▼                    ▼                    ▼
┌───────────┐      ┌───────────────┐     ┌──────────────┐
│ CLAUDE.md │      │ .cursorrules  │     │.windsurfrules│
└───────────┘      └───────────────┘     └──────────────┘
```

1. **`CLAUDE.md`** (Claude Code / Anthropic):
   - Mirrored at repository root and inside subprojects.
   - Contains executive project constraints, build/test commands, and mandatory `ep` CLI toolchains.
2. **`.cursorrules` & `.cursor/rules/`** (Cursor IDE):
   - Injects the 10-Dimension Audit rules, forbidden patterns, and strict typing mandates into Cursor's prompt engine.
3. **`.windsurfrules`** (Windsurf / Cascade):
   - Injects Change Surface boundaries and pre-implementation test-driven development workflows.
4. **`.copilot-instructions.md`** (GitHub Copilot):
   - Configures repository-level architectural invariants for Copilot completions.

---

## 3. Preflight Capability & Access Refusal Protocol

Enterprise-Product is a complete engineering operating system that relies on deterministic mechanical verification. It strictly forbids agents from "hallucinating" verification or skipping gates due to missing host permissions.

### 3.1 Preflight Capability Inspection (`ep preflight`)
Upon initial activation in any workspace, the agent must verify:
1. **Shell Execution**: Ability to spawn subprocesses (`bash` / `sh`).
2. **VCS Core**: `git` installed, working tree status queryable.
3. **Runtime Engine**: Python 3.10+ available in PATH.
4. **Filesystem Read/Write**: Unrestricted write access to the workspace directory.

### 3.2 The Access Refusal Protocol
- **Case A: Capabilities Granted**: The agent operates normally across all 7 operational modes.
- **Case B: Missing Privileges (Resolvable)**:
  - If read-only or restricted execution is detected, `ep preflight` outputs a set of deterministic, repeatable manual command instructions for the human operator to run.
  - The agent must inform the user:
    > "Warning: The current agent platform lacks required execution capabilities. The following instructions must be executed manually. Note that agent session contexts are ephemeral and forgettable, so this procedure must be re-run manually on every turn."
- **Case C: Total Refusal / Inability to Verify**:
  - If the user or platform refuses to provide tool execution or run the manual verification sequence, the agent **must refuse engagement**:
    > "Refusing engagement: Enterprise-Product engineering standards require mechanical test and audit verification. Without execution capabilities or human verification runs, production-readiness cannot be guaranteed. Halting operations on this Product."
