# Polyglot Stack & Task Orchestrator Matrix (100% Agnosticism)

This document specifies the dynamic stack detection heuristics, language build manifests, compiler verification commands, and task orchestrator adapters across all supported programming languages and build systems.

---

## 1. Dynamic Stack Detector Heuristics

`ep` features an integrated `DynamicStackDetector` that inspects subproject roots to automatically classify the technology stack, language, and testing frameworks without requiring manual configuration:

| Language / Stack | Manifest Identifiers | Default Lint Target | Default Test Target | Default Build Target |
|---|---|---|---|---|
| **TypeScript / Node** | `package.json`, `tsconfig.json` | `eslint . --max-warnings 0 && tsc --noEmit` | `vitest run --coverage` | `tsup` / `tsc` / `next build` |
| **Go** | `go.mod` | `golangci-lint run ./...` | `go test -v -race -cover ./...` | `CGO_ENABLED=0 go build ./cmd/...` |
| **Rust** | `Cargo.toml` | `cargo clippy --all-targets -- -D warnings` | `cargo test --all-targets` | `cargo build --release` |
| **Dart / Flutter** | `pubspec.yaml` | `flutter analyze --fatal-infos` | `flutter test --coverage` | `flutter build apk` / `dart compile` |
| **PHP / Laravel** | `composer.json` | `phpstan analyse --level=8` | `pest --coverage` / `phpunit` | `composer dump-autoload -o` |
| **Python** | `pyproject.toml`, `requirements.txt` | `ruff check . && mypy .` | `pytest --cov=.` | `python -m build` |
| **C# / .NET** | `*.csproj`, `*.sln` | `dotnet format --verify-no-changes` | `dotnet test --collect:"XPlat Code Coverage"` | `dotnet build -c Release` |
| **Java** | `pom.xml`, `build.gradle` | `mvn checkstyle:check` / `gradle check` | `mvn test` / `gradle test` | `mvn package` / `gradle build` |
| **Kotlin** | `build.gradle.kts` | `gradle ktlintCheck` | `gradle test` | `gradle build` |
| **Swift** | `Package.swift` | `swiftlint --strict` | `swift test --enable-code-coverage` | `swift build -c release` |
| **Scala** | `build.sbt` | `sbt scalafix` | `sbt test` | `sbt package` |
| **Elixir** | `mix.exs` | `mix credo --strict` | `mix test --cover` | `mix compile` |
| **C / C++** | `CMakeLists.txt`, `Makefile` | `clang-tidy` | `ctest` | `cmake --build .` |

---

## 2. Universal Task DAG Orchestrator Adapter

To achieve 100% orchestrator agnosticism while preserving maximum feature fidelity:

```text
                        ┌────────────────────────────────────┐
                        │      ep Mechanical Task Runner     │
                        │ (Standard Target Contract Protocol)│
                        └─────────────────┬──────────────────┘
                                          │
          ┌───────────────────────────────┼──────────────────────────────┐
          ▼                               ▼                              ▼
┌──────────────────┐            ┌──────────────────┐           ┌──────────────────┐
│   Nx Adapter     │            │Turborepo Adapter │           │ Native DAG Runner│
│(nx affected/run) │            │ (turbo run ...)  │           │(ep run-many ...) │
└──────────────────┘            └──────────────────┘           └──────────────────┘
```

### 2.1 The Standard Target Contract
Regardless of which runner powers the monorepo, every project must satisfy the standard four targets:
1. **`lint`**: Strict static analysis with zero warnings permitted.
2. **`test`**: Value-driven unit and integration test suite with coverage collection.
3. **`build`**: Production compilation producing deterministic build artifacts.
4. **`audit`**: Automated security vulnerability scanning of third-party dependencies.

### 2.2 Orchestrator Resolution Order
When `ep run <target>` or `ep run-many -t <target>` is invoked:
1. **Nx**: If `nx.json` exists at the root, delegate to `pnpm exec nx run-many -t <target>`.
2. **Turborepo**: If `turbo.json` exists at the root, delegate to `pnpm exec turbo run <target>`.
3. **Make / Taskfile**: If `Makefile` or `Taskfile.yml` exists, delegate to `make <target>` or `task <target>`.
4. **Native `ep` DAG Runner**: If no external orchestrator is installed, `ep` parses all `project.json` or `package.json` files, topologically sorts dependency graphs, and executes targets in parallel subprocesses with topological order guarantees.
