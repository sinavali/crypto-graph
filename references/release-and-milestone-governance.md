# Release, Milestone & Versioning Governance Specification

This document defines the Hybrid Dual-Tier SemVer architecture, Milestone tracking, automated production release triggering, and the strict Human-Only Production Merge Policy across all enterprise monorepos.

---

## 1. Hybrid Dual-Tier Versioning Architecture

Polyglot enterprise products consist of multiple independent subprojects (backend services, web portals, mobile clients, shared contracts) that ship together to form a cohesive customer-facing Product. 

To balance cross-project cohesion with independent package evolvability, EP-OS implements a **Hybrid Dual-Tier Versioning Model**:

```text
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Customer-Facing Product Release (e.g. v2.4.0)       │
│ Coordinates cross-service features, API schemas & milestones│
├─────────────────────────────────────────────────────────────┤
│ Tier 2: Subproject Package SemVer                           │
│ - services/auth: v1.8.2 (Cargo.toml / go.mod)              │
│ - apps/web-portal: v3.1.0 (package.json)                    │
│ - apps/mobile: v2.4.0 (pubspec.yaml)                        │
│ - libs/contracts: v2.0.0 (OpenAPI 3.1 / SemVer breaking)    │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Product-Level Release Tags
- Format: `v<MAJOR>.<MINOR>.<PATCH>` (e.g. `v2.4.0`).
- Generated exclusively upon a merged Pull Request into the `prod` branch.
- Accompanied by an automated Release manifest (`docs/releases/vX.Y.Z.md`) aggregating all merged Change Surfaces and ADRs since the previous release.

### 1.2 Subproject SemVer Directives
Each project's `AGENT.md` defines its local SemVer rules:
- **MAJOR**: Incompatible API breaks, schema column drops, protocol changes.
- **MINOR**: Backward-compatible new capabilities, new ports, non-breaking schema additions.
- **PATCH**: Bug fixes, performance optimizations, internal refactors without behavioral drift.

### 1.3 Ambiguity Resolution & Human Escalation
When an AI agent is evaluating a version bump:
1. The agent consults `AGENT.md` and the diff summary.
2. If the change's impact on downstream clients is ambiguous (e.g. subtle behavior alteration, payload shape ambiguity), the agent **must not guess**.
3. The agent must pause and explicitly escalate to the human user:
   > "Ambiguous version classification: The modifications in `services/auth` alter authentication token claims. Please confirm whether this should be classified as a MINOR addition or a MAJOR breaking change."

---

## 2. Milestone Governance

Milestones represent high-level delivery epics or target release cycles (e.g. `M12-Enterprise-SSO`, `Q4-Compliance-Hardening`).

### 2.1 Milestone Manifests (`docs/milestones/`)
Every milestone is defined in a structured manifest:
```markdown
# Milestone: M12-Enterprise-SSO
- **Target Product Version**: `v2.5.0`
- **Due Date**: `2026-11-15`
- **Assigned Subprojects**: `services/auth`, `apps/web-portal`, `libs/contracts`
- **Associated Branches**:
  - `feat/sso-saml-auth`
  - `feat/sso-admin-ui`
- **Status**: IN_PROGRESS
```

### 2.2 Mechanical Milestone Verification
Before a PR targeting `stage` or `prod` is eligible for approval, `ep milestone check` verifies that:
1. All declared subproject dependencies in the milestone are green.
2. No blocking defects or unresolved NC items remain linked to the milestone.

---

## 3. Strict Human-Only Production Merge Policy

In enterprise organizations, deploying to the `prod` branch affects live customer data, financial transactions, and compliance posture. Therefore:

### 3.1 The Inviolable Rule: Agents Never Merge to `prod`
- AI agents are strictly permitted to **prepare, test, verify, and create Pull Requests targeting `prod`**.
- AI agents are **mechanically forbidden from executing merge operations into `prod`**.
- Any execution of `gh pr merge prod`, `git merge prod`, or `glab mr merge prod` by an agent process triggers an immediate termination error.

### 3.2 Automated Configuration Hardening
When `ep pr create-prod` executes:
1. It validates that the PR target branch is `prod` or `release/*`.
2. It verifies that **Auto-Merge is forcibly disabled**.
3. It verifies that **Auto-Delete Source Branch is disabled** for production releases.
4. It sets the required human approver team (e.g. `engineering-leads`, `security-board`).

### 3.3 Post-Merge Automated Release Hook
When a human operator merges the approved PR into `prod`:
1. The CI pipeline triggers `ep release finalize --prod`.
2. A cryptographic git release tag is stamped (`vX.Y.Z`).
3. Release notes are generated directly from the aggregated `CHANGE_SURFACE.md` entries.
