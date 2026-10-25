---
title: "Change Surface: Admin Configuration Engine, Multi-Tenancy, Built-in Captcha, and Investigation Management"
author: "Antigravity Pair Programmer"
created_date: "2026-10-25"
target_branch: "feat/address-pipeline"
risk_level: "MEDIUM"
affected_projects:
  - "libs/blockchain-contracts"
  - "services/crypto-graph-api"
  - "apps/crypto-graph-web"
---

# Change Surface: Admin Configuration Engine, Multi-Tenancy, Built-in Captcha, and Investigation Management

## 1. Intent & Business Rationale
Extend the crypto-graph platform to support multi-tenant isolation, user authentication with a zero-external-dependency built-in SVG captcha, a comprehensive Admin configuration dashboard capable of dynamically managing all system parameters (RPC pools, circuit thresholds, heuristic weights, graph rendering options, security policies), persona profile administration (inspecting, overriding labels/tags, manual wallet linking), and user investigation management (watchlists, saved graphs, search history).

## 2. Affected Monorepo Projects & Profiles
| Project Path | Architectural Profile | Responsibility in this Change |
|---|---|---|
| `libs/blockchain-contracts` | Profile D (Contracts) | Add Tenant, User, Session, CaptchaChallenge, and SystemConfig schemas |
| `services/crypto-graph-api` | Profile A (Backend DDD) | Add Auth, Captcha, ConfigService, SQLite schema migrations, Admin and Investigation API routers |
| `apps/crypto-graph-web` | Profile B (Web SSR) | Add Admin pages (config, personas, tenants), Auth pages (login, register), Captcha rendering, and investigation drawer |

## 3. Code Surface (Targeted Symbols & Files)

### Added Files
- `.gitignore`
- `.cursorrules`
- `.windsurfrules`
- `.github/`
- `scripts/`
- `templates/`
- `references/`
- `libs/`
- `services/`
- `apps/`
- `libs/blockchain-contracts/`
- `libs/blockchain-contracts/src/auth_models.py`
- `libs/blockchain-contracts/src/config_models.py`
- `services/crypto-graph-api/`
- `services/crypto-graph-api/src/domain/captcha.py`
- `services/crypto-graph-api/src/domain/config_service.py`
- `services/crypto-graph-api/src/domain/auth_service.py`
- `services/crypto-graph-api/src/domain/entity_registry.py`
- `services/crypto-graph-api/src/infrastructure/auth_router.py`
- `services/crypto-graph-api/src/infrastructure/admin_router.py`
- `services/crypto-graph-api/src/infrastructure/investigation_router.py`
- `apps/crypto-graph-web/`
- `apps/crypto-graph-web/src/templates/admin/config.html`
- `apps/crypto-graph-web/src/templates/admin/personas.html`
- `apps/crypto-graph-web/src/templates/admin/tenants.html`
- `apps/crypto-graph-web/src/templates/auth/login.html`
- `apps/crypto-graph-web/src/templates/auth/register.html`
- `apps/crypto-graph-web/src/templates/partials/investigation_panel.html`
- `services/crypto-graph-api/tests/test_auth_and_captcha.py`
- `services/crypto-graph-api/tests/test_config_service.py`
- `services/crypto-graph-api/tests/test_admin_router.py`
- `apps/crypto-graph-web/tests/test_admin_and_auth_web.py`
- `docs/changes/2026-10-25-feat-admin-multitenant-config.md`

### Modified Files
- `libs/blockchain-contracts/src/__init__.py`
- `libs/blockchain-contracts/src/models.py`
- `libs/blockchain-contracts/src/fixtures.py`
- `libs/blockchain-contracts/tests/test_contracts.py`
- `services/crypto-graph-api/src/infrastructure/sqlite_storage.py`
- `services/crypto-graph-api/src/infrastructure/rpc_rotator.py`
- `services/crypto-graph-api/src/domain/analytics.py`
- `services/crypto-graph-api/src/domain/clustering.py`
- `services/crypto-graph-api/src/application/use_cases.py`
- `apps/crypto-graph-web/src/app.py`
- `apps/crypto-graph-web/src/templates/index.html`
- `apps/crypto-graph-web/src/static/style.css`
- `apps/crypto-graph-web/src/static/app.js`

## 4. Test Surface

### Unit & Domain Tests
- `services/crypto-graph-api/tests/test_auth_and_captcha.py`: Password hashing, session lifecycle, SVG captcha challenge generation and validation.
- `services/crypto-graph-api/tests/test_config_service.py`: Dynamic config retrieval, update, validation, and hot reload.
- `services/crypto-graph-api/tests/test_admin_router.py`: Admin RBAC protection, RPC pool updating, persona profile editing, manual wallet linking.

### Web & Integration Tests
- `apps/crypto-graph-web/tests/test_admin_and_auth_web.py`: Sign in, sign up flow with captcha validation, admin dashboard rendering, watchlist and investigation saving.

## 5. Invariants & Non-Negotiables Preserved
- [x] Tier 1: Zero external dependencies for captcha (pure Python SVG generator).
- [x] Tier 1: Multi-tenant data segregation enforced at repository and query layers.
- [x] Tier 1: All stored timestamps strictly UTC ISO-8601.
- [x] Tier 1: Embedded SQLite WAL mode, zero external database daemons.
- [x] Tier 2: Domain logic test coverage $\ge 90\%$.
