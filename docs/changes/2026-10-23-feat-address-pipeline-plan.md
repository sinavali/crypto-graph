---
title: "Change Surface: Address Input, Normalization, and Multi-Chain Adapter Contract"
author: "Enterprise Agent"
created_date: "2026-10-23"
target_branch: "feat/address-pipeline"
risk_level: "MEDIUM"
affected_projects:
  - "services/crypto-graph-api"
  - "apps/crypto-graph-web"
---

# Change Surface: Address Input, Normalization, and Multi-Chain Adapter Contract

## 1. Intent & Business Rationale
Establish the first real crypto-graph capability: accept a public wallet address, normalize/validate it, map it to a chain context, and expose a typed backend contract that the web frontend can render. This is explicitly an address-first pipeline. Multi-chain adapter interfaces are defined up front so later chain adapters and cross-chain aggregation can slot in without redesign. Persona resolution and profiling are intentionally deferred to follow-up issues so this Change Surface stays bounded.

## 2. Affected Monorepo Projects & Profiles
| Project Path | Architectural Profile | Responsibility in this Change |
|---|---|---|
| `services/crypto-graph-api` | Profile A (Backend DDD/Hexagonal) | Address input use-case, chain context value object, chain adapter port, normalize/validate logic, typed API boundary |
| `apps/crypto-graph-web` | Profile B (Web Applications) | Address input view, API client contract, loading/error/empty states, render-view entry for a single address summary |

## 3. Code Surface (Targeted Symbols & Files)

### Added Files
- `.gitignore`
- `.cursorrules`
- `.windsurfrules`
- `.github/CODEOWNERS`
- `AGENT.md`
- `PRODUCT_SKILL.md`
- `scripts/`
- `templates/`
- `references/`
- `libs/blockchain-contracts/`
- `libs/blockchain_contracts`
- `libs/__init__.py`
- `services/crypto-graph-api/`
- `services/crypto_graph_api`
- `services/__init__.py`
- `apps/crypto-graph-web/`
- `docs/changes/2026-10-23-feat-address-pipeline-plan.md`
- `docs/changes/2026-10-23-scaffold-initial-product-monorepo.md`

### Modified Files
- `services/crypto-graph-api/project.json`
- `services/crypto-graph-api/AGENT.md`
- `apps/crypto-graph-web/project.json`
- `apps/crypto-graph-web/AGENT.md`

## 4. Test Surface

### Unit & Domain Tests
- `services/crypto-graph-api/tests/unit/value-objects/test_address.py`: normalized form invariants, invalid input rejection, chain-context association
- `services/crypto-graph-api/tests/unit/value-objects/test_chain_context.py`: chain identifier semantics, equality, serialization to/from UTC-aware timestamps
- `services/crypto-graph-api/tests/unit/use-cases/test_lookup_address.py`: address lookup orchestration with port fakes, invalid address failure path, missing data failure path

### Integration Tests (Real Ephemeral Containers)
- `services/crypto-graph-api/tests/integration/adapters/test_mock_chain_adapter.py`: adapter port contract verification and timeout/failure behavior exercised against a controlled adapter implementation

### Failure & Resilience Tests
- Backend HTTP boundary: malformed address, oversized input, missing chain context, and adapter timeout/failure paths
- Frontend: empty input, invalid address, API failure, and retry state rendering

### UI State-Machine Tests (Profile B)
- Address input and summary must render explicit Loading, Empty, Error, and Success states

## 5. Invariants & Non-Negotiables Preserved
- [ ] Tier 1: Pure domain logic must not import web frameworks, ORMs, or external chain SDKs
- [ ] Tier 1: All stored/internal timestamps use UTC ISO-8601
- [ ] Tier 2: Profile A canonical layout observed (`domain/`, `application/`, `infrastructure/`)
- [ ] Tier 2: Profile B clean separation: components receive data via feature hooks/state, not direct fetches
- [ ] Tier 2: No dumping grounds; utilities live in domain-qualified modules
- [ ] Tier 2: File sizes stay within EP-OS ceilings; co-locate tightly coupled small value objects where appropriate
- [ ] Tier 2: Frontend must validate API responses with runtime schema validation, not raw `any`

## 6. Risk Matrix & Rollback Strategy
| Risk Description | Probability | Impact | Mitigation Strategy |
|---|---|---|---|
| Chain adapter surface chosen too narrowly for later multi-chain needs | Medium | High | Define chain adapter port first; implement a non-production mock adapter; defer real chain wiring to follow-up issues |
| Address normalization rules vary by chain | Medium | Medium | Capture chain-specific normalization behind the chain context value object instead of hardcoding one chain |
| Frontend blocks on backend before API contract is stable | Low | Medium | Freeze the typed API client contract early; render frontend against contract and mock responses |

### Rollback Strategy
- Revert new source files in `services/crypto-graph-api/src` and `apps/crypto-graph-web/src`
- Keep the project.json/AGENT.md changes if they are reused by later work; otherwise revert them too
- Delete the feature branch after merge or close the PR without merge
