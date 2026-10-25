# Monorepo Task Orchestration Specification (Nx Reference Standard)

This specification governs the unified orchestration of polyglot codebases using a deterministic DAG task orchestrator, with **Nx** serving as the standard enterprise reference engine. All projects—regardless of language or runtime—must conform to standard target contracts to enable deterministic dependency graphs, affected task execution, and distributed caching.

---

## 1. Monorepo Architecture Overview

Every product repository is a single monorepo. Native package managers (Cargo, Go modules, Composer, NuGet, Pub, Gradle, Swift Package Manager, PNPM) manage toolchains locally within subprojects, while the root orchestrator (Nx, or compatible DAG engines like Turborepo/Bazel via target adaptation) manages orchestration, task graphs, and CI caching at the root:

```text
monorepo-root/
├── nx.json                           # Root task pipeline configuration
├── package.json                      # Root workspace tooling
├── pnpm-workspace.yaml / pnpm-lock   # Workspace lockfile
├── AGENT.md                          # Root Enterprise Governance Manifest
├── apps/                             # End-user applications (Web, Mobile, Core APIs)
│   ├── web-portal/project.json       # Profile B (Web Application)
│   ├── mobile-client/project.json    # Profile C (Mobile Client)
│   └── order-service/project.json    # Profile A (Backend Service)
├── libs/                             # Shared libraries & contracts
│   ├── core-contracts/project.json   # Profile D (OpenAPI / Protobuf)
│   └── domain-types/project.json     # Profile D (Pure Shared Types)
```

---

## 2. Standard Nx Target Contracts

Every `project.json` file in the monorepo must implement four standard targets:
1. `lint`: Static analysis, type checking, style formatting verification.
2. `test`: Unit, integration, and failure test execution.
3. `build`: Compilation and production artifact packaging.
4. `audit`: Project-specific architectural and security auditing.

Optional standard targets include:
- `serve`: Local development server execution.
- `e2e`: End-to-end integration and browser/mobile workflow execution.

### Target Contract Invariant
Running `nx affected -t <target>` in CI must succeed across all languages without requiring CI scripts to know whether a project is Go, Dart, Rust, PHP, or TypeScript.

---

## 3. Polyglot Delegation via `nx:run-commands`

Nx delegates execution to native language toolchains using the standard `@nx/powerpack:run-commands` or `nx:run-commands` executor:

### 3.1 Profile A: Go Service Example (`services/auth-service/project.json`)
```json
{
  "name": "auth-service",
  "$schema": "../../node_modules/nx/schemas/project-schema.json",
  "projectType": "application",
  "sourceRoot": "services/auth-service/src",
  "tags": ["scope:backend", "profile:a", "lang:go"],
  "targets": {
    "lint": {
      "executor": "nx:run-commands",
      "options": {
        "command": "golangci-lint run ./...",
        "cwd": "services/auth-service"
      }
    },
    "test": {
      "executor": "nx:run-commands",
      "options": {
        "command": "go test -v -race -coverprofile=coverage.out ./...",
        "cwd": "services/auth-service"
      },
      "outputs": ["{projectRoot}/coverage.out"]
    },
    "build": {
      "executor": "nx:run-commands",
      "options": {
        "command": "CGO_ENABLED=0 go build -o bin/auth-service ./src/main.go",
        "cwd": "services/auth-service"
      },
      "outputs": ["{projectRoot}/bin"]
    },
    "audit": {
      "executor": "nx:run-commands",
      "options": {
        "command": "govulncheck ./...",
        "cwd": "services/auth-service"
      }
    }
  }
}
```

### 3.2 Profile A: .NET Core Service Example (`services/billing-service/project.json`)
```json
{
  "name": "billing-service",
  "projectType": "application",
  "tags": ["scope:backend", "profile:a", "lang:dotnet"],
  "targets": {
    "lint": {
      "executor": "nx:run-commands",
      "options": {
        "command": "dotnet format --verify-no-changes",
        "cwd": "services/billing-service"
      }
    },
    "test": {
      "executor": "nx:run-commands",
      "options": {
        "command": "dotnet test --collect:\"XPlat Code Coverage\"",
        "cwd": "services/billing-service"
      }
    },
    "build": {
      "executor": "nx:run-commands",
      "options": {
        "command": "dotnet publish -c Release -o dist",
        "cwd": "services/billing-service"
      },
      "outputs": ["{projectRoot}/dist"]
    },
    "audit": {
      "executor": "nx:run-commands",
      "options": {
        "command": "dotnet list package --vulnerable --include-transitive",
        "cwd": "services/billing-service"
      }
    }
  }
}
```

### 3.3 Profile C: Flutter Mobile App Example (`apps/mobile-client/project.json`)
```json
{
  "name": "mobile-client",
  "projectType": "application",
  "tags": ["scope:mobile", "profile:c", "lang:dart"],
  "targets": {
    "lint": {
      "executor": "nx:run-commands",
      "options": {
        "command": "flutter analyze --fatal-infos",
        "cwd": "apps/mobile-client"
      }
    },
    "test": {
      "executor": "nx:run-commands",
      "options": {
        "command": "flutter test --coverage",
        "cwd": "apps/mobile-client"
      },
      "outputs": ["{projectRoot}/coverage"]
    },
    "build": {
      "executor": "nx:run-commands",
      "options": {
        "command": "flutter build apk --release",
        "cwd": "apps/mobile-client"
      },
      "outputs": ["{projectRoot}/build/app/outputs/flutter-apk"]
    },
    "audit": {
      "executor": "nx:run-commands",
      "options": {
        "command": "flutter pub outdated --prereleases",
        "cwd": "apps/mobile-client"
      }
    }
  }
}
```

---

## 4. Root `nx.json` Orchestration & Pipelines

The root `nx.json` defines task dependencies across the dependency graph:

```json
{
  "$schema": "./node_modules/nx/schemas/nx-schema.json",
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["production", "^production"],
      "cache": true
    },
    "test": {
      "dependsOn": ["build"],
      "inputs": ["default", "^production"],
      "cache": true
    },
    "lint": {
      "inputs": ["default"],
      "cache": true
    },
    "audit": {
      "inputs": ["default"],
      "cache": true
    }
  },
  "namedInputs": {
    "default": ["{projectRoot}/**/*", "sharedGlobals"],
    "production": [
      "default",
      "!{projectRoot}/**/?(*.)+(spec|test).[jt]s?(x)",
      "!{projectRoot}/tests/**/*",
      "!{projectRoot}/.eslintrc.json"
    ],
    "sharedGlobals": []
  }
}
```

---

## 5. Architectural Boundary Enforcement

Nx enforces architectural boundaries using tagging rules. In `eslint.config.js` or Nx module boundary linting:
1. `scope:backend` cannot import `scope:frontend` or `scope:mobile`.
2. `scope:frontend` and `scope:mobile` cannot import internal backend implementations; they must depend strictly on `scope:shared` (Profile D contracts).
3. `profile:d` (Contracts) cannot import applications or platform-specific libraries.

Running `nx affected -t lint` automatically verifies that no rogue cross-boundary imports have violated this topology.
