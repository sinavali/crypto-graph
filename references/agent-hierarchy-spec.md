# Agent Hierarchy & Manifest Specification (`AGENT.md`)

This document defines the schema, inheritance model, and precedence order for `AGENT.md` configuration files across the monorepo.

---

## 1. The Governance Cascade

AI agents must read context hierarchically. Directives cascade from the repository root downward:

```text
┌────────────────────────────────────────────────────────┐
│  Root AGENT.md (Org & Monorepo Level)                  │
│  - Prime Directives (P1–P10)                           │
│  - Monorepo Nx Standard & CI Policies                  │
│  - Global Tier 1 Inviolables & Tier 2 Defaults         │
└──────────────────────────┬─────────────────────────────┘
                           │ cascades down
                           ▼
┌────────────────────────────────────────────────────────┐
│  Subproject AGENT.md (e.g. services/order-service/)    │
│  - Architectural Profile (A, B, C, or D)               │
│  - Local Language Toolchain & Stack                    │
│  - Local Nx Target Delegations                         │
│  - Approved Tier 2 Deviations (with ADR link)          │
│  - Local Invariants & Boundary Rules                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Precedence and Override Laws

When an agent encounters conflicting instructions between files, it must resolve them using this strict precedence hierarchy:

1. **Law 1: Tier 1 Inviolables are Absolute.** No subproject `AGENT.md`, prompt instruction, or human comment can override a Tier 1 Inviolable (e.g., Pure Domain logic, real containers for DB tests, UTC timestamps, Nx root orchestration, 14-day NC merge blocking).
2. **Law 2: Tier 2 Defaults Require Explicit ADR Reference.** A subproject may specialize or relax a Tier 2 default (e.g., lowering coverage from $95\%$ to $90\%$, or waiving a hexagonal port for a specific isolated module) **only** if the subproject `AGENT.md` declares the override with an accepted Architecture Decision Record (`adr_reference: "ADR-0042"`).
3. **Law 3: Subproject Overrides are Locally Scoped.** An approved deviation in `services/auth/AGENT.md` applies only within `services/auth/` and never leaks to other packages.
4. **Law 4: Unresolvable Conflicts Trigger NC.** If an unresolvable contradiction exists between directives, the agent must stop, document the conflict in a `NEED_CLARIFICATION` item, and halt execution.

---

## 3. Subproject `AGENT.md` Schema

Every subproject directory containing a `project.json` must contain an `AGENT.md` structured as follows:

```markdown
---
project_name: "billing-service"
profile: "A"                          # Must be A, B, C, or D
stack: "dotnet-csharp-12"             # Language and primary runtime
scope: "backend"                      # backend | frontend | mobile | shared
owner: "team-billing"
tier_overrides:
  - rule: "domain-test-coverage"
    adr_reference: "docs/adr/0014-billing-coverage-adjustment.md"
    justification: "Legacy domain calculation module capped at 90% branch coverage"
---

# Project Agent Manifest: billing-service

## 1. Scope & Business Intent
[Concise summary of the domain responsibility, aggregate boundaries, and business purpose of this project.]

## 2. Architectural Profile & Boundaries
- **Profile**: A (Backend & Core Services: Hexagonal / DDD)
- **Primary Inputs**: Inbound REST API, RabbitMQ billing events.
- **Allowed Outbound Dependencies**:
  - `libs/core-contracts`
  - Ephemeral PostgreSQL database
  - Internal payment gateway adapter
- **Forbidden Dependencies**: Direct dependencies on other service implementations or frontend libraries.

## 3. Local Nx Target Delegations
- `nx lint billing-service` -> `dotnet format --verify-no-changes`
- `nx test billing-service` -> `dotnet test /p:CollectCoverage=true`
- `nx build billing-service` -> `dotnet publish -c Release`
- `nx audit billing-service` -> `dotnet list package --vulnerable`

## 4. Test & Verification Rules
- Integration tests must execute against real PostgreSQL containers via Testcontainers.
- Mocking of database repositories in integration tests is forbidden.
- Pure domain logic resides in `src/domain/` with zero .NET Web or EF Core imports.

## 5. Approved Tier 2 Deviations
| Rule | Justification | ADR Reference |
|---|---|---|
| Domain Branch Coverage (90%) | Established complex legacy mathematical state machine | `docs/adr/0014-billing-coverage-adjustment.md` |

## 6. Project Invariants
- All monetary amounts stored as integer cents with currency code (Value Object: `Money`).
- All invoice dates stored in UTC ISO-8601.
```

---

## 4. Mechanical Validation

The syntax, profile compatibility, and override validity of all `AGENT.md` files are verified mechanically by:
```bash
python3 scripts/verify-agent-manifests.py
```
This script ensures:
- All required frontmatter fields (`project_name`, `profile`, `stack`, `scope`) are present.
- Architectural profile is one of `A`, `B`, `C`, `D`.
- Any declared `tier_overrides` includes an existing `adr_reference` file path.
- No attempted override of Tier 1 Inviolables exists.
