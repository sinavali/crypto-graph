# Polyglot Static Analysis & Strict Typing Matrix

Code must be strictly typed, statically verifiable, and self-documenting across all monorepo projects. Suppressing compiler or static analysis warnings without an approved Architecture Decision Record (ADR) is strictly prohibited.

---

## 1. Monorepo Standard: Nx Task Delegation

Every `project.json` must implement a standard `lint` target. In CI and local verification, static analysis is triggered via:
```bash
# Verify affected projects
pnpm exec nx affected --target=lint

# Verify a specific project
pnpm exec nx lint <project-name>
```

---

## 2. Language-Specific Directives & Compiler Flags

### 2.1 TypeScript & JavaScript (Profile B: Web & Node Services)
- **Zero `any`**: Untyped `any` is strictly banned. Use `unknown` with runtime type narrowing (Zod, Valibot, or custom type guards).
- **Strict Verification Command**:
  ```bash
  pnpm exec tsc --noEmit
  ```
- **Compiler Invariants (`tsconfig.json`)**:
  - `"strict": true`
  - `"noImplicitAny": true`
  - `"strictNullChecks": true`
  - `"noUncheckedIndexedAccess": true`
- All boundary payloads (HTTP request bodies, URL query params, webhook events) must be validated with runtime schemas before reaching domain logic.

### 2.2 Go (Profile A: Backend & Microservices)
- **Standard Toolchain Command**:
  ```bash
  golangci-lint run ./...
  govulncheck ./...
  ```
- **Linters Enforced (`.golangci.yml`)**:
  - `errcheck`: All error return values must be explicitly handled; zero `_ = err` ignores.
  - `govet`: Struct tags, shadow variables, atomic alignment.
  - `staticcheck`: Static code correctness.
  - `gosec`: Security audits (SQL injection, weak cryptography, hardcoded credentials).
- **Struct Tag Integrity**: Struct tags for serialization (`json:`, `db:`, `yaml:`) must be typed and explicitly declared.

### 2.3 Rust (Profile A: High-Performance Services & Core Libraries)
- **Standard Toolchain Command**:
  ```bash
  cargo clippy --all-targets --all-features -- -D warnings
  cargo audit
  ```
- **Compiler Invariants**:
  - `#![deny(clippy::unwrap_used)]`: No panicking `.unwrap()` in production paths; use typed `Result<T, DomainError>` with `?`.
  - `#![deny(unsafe_code)]`: `unsafe` blocks are prohibited in domain logic.

### 2.4 Dart & Flutter (Profile C: Mobile Clients)
- **Standard Toolchain Command**:
  ```bash
  flutter analyze --fatal-infos
  ```
- **Analysis Invariants (`analysis_options.yaml`)**:
  - `always_declare_return_types: true`
  - `avoid_dynamic_calls: true`
  - `prefer_const_constructors: true`
  - Immutable state models using `@immutable` or `freezed`.

### 2.5 PHP & Laravel (Profile A: Legacy & Lerd Services)
- **Standard Toolchain Command**:
  ```bash
  vendor_run bin="phpstan" args=["analyse", "--level=8"]
  ```
- **Language Invariants**:
  - Every new PHP file must declare strict types:
    ```php
    <?php
    declare(strict_types=1);
    ```
  - Method parameters and return types must be fully declared (`: void`, `?Type`).
  - Arrays must declare PHPStan array shapes: `@param array{id: int, name: string} $data`.

---

## 3. The Zero-Suppression Rule

1. Using ignore comments (`@ts-ignore`, `@ts-nocheck`, `//nolint`, `#[allow(...)]`, `@phpstan-ignore`) is strictly classified as a **blocking defect** during audit.
2. In exceptional brownfield cases where a third-party library has broken types, an ignore comment is permitted **only** if tagged with an accepted ADR reference:
   ```typescript
   // @ts-expect-error [ADR-0024]: Legacy vendor SDK payload lacks generic typing
   ```
