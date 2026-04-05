# CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STRIDER CI/CD PIPELINE                              │
│                         GitHub Actions Workflows                            │
└─────────────────────────────────────────────────────────────────────────────┘

                                   TRIGGERS
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Push to main/develop    Pull Request      Weekly Schedule    Manual       │
│         ↓                     ↓                  ↓              ↓          │
└─────────────────────────────────────────────────────────────────────────────┘

                              WORKFLOW EXECUTION
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │   BACKEND CI       │  │   FRONTEND CI      │  │   INTEGRATION      │   │
│  │                    │  │                    │  │                    │   │
│  │ 1. Type Check      │  │ 1. ESLint          │  │ 1. Docker Compose  │   │
│  │    └─ MyPy         │  │    └─ Code Style   │  │    └─ Full Stack   │   │
│  │                    │  │                    │  │                    │   │
│  │ 2. Tests           │  │ 2. Type Check      │  │ 2. Health Check    │   │
│  │    └─ Pytest       │  │    └─ TypeScript   │  │    └─ /health      │   │
│  │    └─ PostgreSQL   │  │                    │  │                    │   │
│  │                    │  │ 3. Build           │  │ 3. Integration     │   │
│  │ 3. Docker Build    │  │    └─ Vite         │  │    └─ API Tests    │   │
│  │    └─ Verify       │  │    └─ Artifacts    │  │                    │   │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│         ⏱ 2-3 min            ⏱ 1-2 min              ⏱ 3-4 min             │
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │  SECURITY SCAN     │  │   PR AUTOMATION    │  │    DEPLOYMENT      │   │
│  │                    │  │                    │  │                    │   │
│  │ 1. Dependencies    │  │ 1. Auto-label      │  │ 1. Build & Push    │   │
│  │    └─ pip-audit    │  │    └─ By Files     │  │    └─ Docker Img   │   │
│  │    └─ npm audit    │  │    └─ By Size      │  │                    │   │
│  │                    │  │                    │  │ 2. Deploy Backend  │   │
│  │ 2. Code Analysis   │  │ 2. Comment         │  │    └─ Template     │   │
│  │    └─ CodeQL       │  │    └─ Helpful      │  │                    │   │
│  │    └─ Python       │  │        Message     │  │ 3. Deploy Frontend │   │
│  │    └─ TypeScript   │  │                    │  │    └─ Template     │   │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│         ⏱ 3-5 min            ⏱ <30 sec              ⏱ Varies              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              QUALITY GATES
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  All Checks Pass ✅  →  Merge Allowed                                       │
│  Any Check Fails ❌  →  Merge Blocked                                       │
│                                                                             │
│  Required Checks (Recommended):                                            │
│  • Backend CI                                                              │
│  • Frontend CI                                                             │
│  • Security Scan                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                           OPTIMIZATION FEATURES
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ⚡ Smart Caching      │  Dependencies cached per lock file hash           │
│  📁 Path Filtering    │  Only run when relevant files change              │
│  🔄 Parallel Jobs     │  Independent workflows run simultaneously          │
│  🐳 Layer Caching     │  Docker layers cached for fast rebuilds           │
│  📦 Artifacts         │  Build outputs saved for 7 days                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                           WORKFLOW DEPENDENCIES
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Backend CI:                                                                │
│    Lint & Type Check  →  Tests  →  Docker Build                            │
│                                                                             │
│  Frontend CI:                                                               │
│    Lint & Type Check  →  Build  →  Upload Artifacts                        │
│                                                                             │
│  Security Scan:                                                             │
│    Backend Scan  ┐                                                          │
│    Frontend Scan ├─→  All parallel execution                               │
│    CodeQL        ┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              PATH FILTERS
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  backend/**            →  Triggers Backend CI                              │
│  frontend/**           →  Triggers Frontend CI                             │
│  Any file on main      →  Triggers Integration Test                        │
│  Any file              →  Triggers Security Scan                           │
│  .github/workflows/**  →  Triggers relevant CI                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                          DEPLOYMENT PLATFORMS
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Backend (Docker):          │  Frontend (Static):                          │
│  • GitHub Container Registry│  • GitHub Pages                              │
│  • AWS ECS/Fargate          │  • Netlify                                   │
│  • Google Cloud Run         │  • Vercel                                    │
│  • Azure Container Apps     │  • AWS S3 + CloudFront                       │
│  • Kubernetes               │  • Azure Static Web Apps                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                            SUCCESS METRICS
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ✅ 100% Automated testing on every commit                                 │
│  ✅ Security scanning with every push + weekly                             │
│  ✅ Type safety enforced (Python & TypeScript)                             │
│  ✅ Code quality gates before merge                                        │
│  ✅ Docker build verification                                              │
│  ✅ Integration testing with real services                                 │
│  ✅ Automated PR labeling and organization                                 │
│  ✅ Deployment templates ready to configure                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Reference

### File Locations
```
.github/
├── workflows/
│   ├── backend-ci.yml          # Backend: MyPy, Pytest, Docker
│   ├── frontend-ci.yml         # Frontend: ESLint, TSC, Vite
│   ├── full-integration.yml    # E2E: Docker Compose tests
│   ├── security-scan.yml       # Security: pip-audit, npm audit, CodeQL
│   ├── deploy.yml              # Deploy: Templates for all platforms
│   ├── pr-automation.yml       # PR: Auto-label, size, comments
│   └── README.md               # Detailed documentation
├── labeler.yml                 # Label configuration
├── QUICKSTART.md               # Quick start guide
└── IMPLEMENTATION-SUMMARY.md   # This summary
```

### Common Commands
```bash
# Push to trigger CI
git push origin main

# View workflow runs
open https://github.com/YOUR_USERNAME/strider/actions

# Manually trigger deployment
# GitHub → Actions → Deploy → Run workflow

# Check security alerts
# GitHub → Security → Dependabot alerts
```

### Status Badge Examples
```markdown
![Backend CI](https://github.com/USER/strider/workflows/Backend%20CI/badge.svg)
![Frontend CI](https://github.com/USER/strider/workflows/Frontend%20CI/badge.svg)
![Security](https://github.com/USER/strider/workflows/Security%20Scan/badge.svg)
```
