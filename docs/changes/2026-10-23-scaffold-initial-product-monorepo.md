---
title: "Change Surface: Initial EP-OS Product Scaffold"
author: "Enterprise Agent"
created_date: "2026-10-23"
target_branch: "main"
risk_level: "LOW"
affected_projects:
  - "services/crypto-graph-api"
  - "apps/crypto-graph-web"
---

# Change Surface: Initial EP-OS Product Scaffold

## 1. Intent & Business Rationale
Establish an EP-OS governed polyglot monorepo for crypto-graph with a Python backend service and a TypeScript render-view web frontend. This scaffold sets governance contracts, promotion topology, and mechanical verification gates, not application behavior.

## 2. Affected Monorepo Projects & Profiles
| Project Path | Architectural Profile | Responsibility in this Change |
|---|---|---|
| `services/crypto-graph-api` | Profile A (Backend DDD/Hexagonal) | Python backend service scaffolded under EP-OS Profile A contracts |
| `apps/crypto-graph-web` | Profile B (Web Applications) | Render-view frontend scaffolded under EP-OS Profile B contracts |

## 3. Code Surface (Targeted Symbols & Files)

### Added Files
- `services/crypto-graph-api/project.json`
- `services/crypto-graph-api/AGENT.md`
- `services/crypto-graph-api/src/`
- `services/crypto-graph-api/tests/`
- `apps/crypto-graph-web/project.json`
- `apps/crypto-graph-web/AGENT.md`
- `apps/crypto-graph-web/src/`
- `apps/crypto-graph-web/tests/`
- `docs/changes/2026-10-23-scaffold-initial-product-monorepo.md`
- `docs/releases/`
- `docs/adr/`
- `.github/CODEOWNERS`
- `.github/workflows/`
- `.ep/`

### Modified Files
- `README.md` (planned future update)
- `PRODUCT_SKILL.md` (existing repo-level skill)

## 4. Test Surface
This scaffold does not yet implement application logic, so no application test files are declared in this Change Surface.

### Unit & Domain Tests
- None in this scaffold; declared in future Change Surfaces for `services/crypto-graph-api` and `apps/crypto-graph-web`.

### Integration Tests (Real Ephemeral Containers)
- None in this scaffold; future backend Change Surfaces will use ephemeral containers for datastore adapters.

### Failure & Resilience Tests
- None in this scaffold; future adapter Change Surfaces will include timeout, retry, and circuit-breaker failure paths.

### Governance / Mechanical Verification Tests
- `python3 scripts/ep.py verify`
- `python3 scripts/ep.py surface check-diff --strict`
- `python3 scripts/ep.py migration check`
- `python3 scripts/ep.py nc check --max-age 14`
- `python3 scripts/ep.py audit` (against declared Change Surface)

## 5. Invariants & Non-Negotiables Preserved
- [x] Tier 1: Single monorepo governed by EP-OS and project.json target contracts
- [x] Tier 1: Promotion branches `main`, `test`, `stage`, `prod` present
- [x] Tier 1: Zero-dependency client-side git hooks installed
- [x] Tier 1: CODEOWNERS declares ownership
- [x] Tier 2: Profile-based project manifests created for backend and frontend
- [x] Tier 2: Product operating skill (`PRODUCT_SKILL.md`) generated

## 6. Risk Matrix & Rollback Strategy
| Risk Description | Probability | Impact | Mitigation Strategy |
|---|---|---|---|
| Promotion branch push fails against remote protections | Low | Medium | Doctor `--heal` configured publishing; fallback to local-only topology if remote rejects |

### Rollback Strategy
- Remove newly created project directories and revert the documentation/CODEOWNERS additions.
- Re-run `python3 scripts/ep.py doctor --heal` if promotion topology must be repaired.
