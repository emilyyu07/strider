# CI/CD Pipeline Documentation

This document explains the GitHub Actions CI/CD pipeline setup for the Strider project.

## Overview

The CI/CD pipeline consists of 5 main workflows:

1. **Backend CI** - Tests and builds the Python FastAPI backend
2. **Frontend CI** - Tests and builds the React TypeScript frontend
3. **Full Integration** - End-to-end testing with Docker Compose
4. **Security Scan** - Dependency and code vulnerability scanning
5. **Deploy** - Deployment automation (template for your infrastructure)

## Workflows Explained

### 1. Backend CI (`backend-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches (only when backend files change)
- Pull requests to `main` or `develop` (only when backend files change)

**Jobs:**

#### a. Lint and Type Check
- **Purpose:** Ensure code quality and type safety
- **Steps:**
  1. Checkout code from repository
  2. Set up Python 3.11 with pip caching
  3. Install dependencies from `requirements.txt`
  4. Run MyPy for static type checking

**How to implement:** MyPy checks for type errors. Configure it by creating `mypy.ini` in the backend folder if you need custom rules.

#### b. Test
- **Purpose:** Run automated tests with a PostgreSQL database
- **Steps:**
  1. Spin up PostgreSQL service container (using the same image as production)
  2. Checkout code
  3. Set up Python with dependency caching
  4. Install dependencies
  5. Run pytest with environment variables for database connection

**How to implement:** Add tests in `backend/tests/` directory. Pytest will automatically discover and run them.

#### c. Build Docker
- **Purpose:** Verify the Docker image builds successfully
- **Steps:**
  1. Checkout code
  2. Set up Docker Buildx (for advanced builds)
  3. Build Docker image without pushing
  4. Use GitHub Actions cache to speed up builds

**How to implement:** The workflow uses your existing `backend/Dockerfile`. No changes needed unless you modify the Dockerfile location.

---

### 2. Frontend CI (`frontend-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches (only when frontend files change)
- Pull requests to `main` or `develop` (only when frontend files change)

**Jobs:**

#### a. Lint and Type Check
- **Purpose:** Ensure code quality and type safety
- **Steps:**
  1. Checkout code
  2. Set up Node.js 20 with npm caching
  3. Install dependencies with `npm ci` (clean install)
  4. Run ESLint for code linting
  5. Run TypeScript compiler in check mode (no output files)

**How to implement:** Your existing ESLint config and TypeScript setup will be used automatically.

#### b. Build
- **Purpose:** Create production build and verify no errors
- **Steps:**
  1. Checkout code
  2. Set up Node.js with caching
  3. Install dependencies
  4. Run production build
  5. Upload build artifacts for 7 days (useful for debugging)

**How to implement:** Uses your existing `npm run build` script from package.json.

---

### 3. Full Integration Test (`full-integration.yml`)

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch

**Purpose:** Test the entire application stack together using Docker Compose

**Steps:**
1. Checkout code
2. Create `.env` file with test configuration
3. Start PostgreSQL and backend services using Docker Compose
4. Wait for services to become healthy
5. Check backend health endpoint
6. Run integration tests inside the Docker container
7. Show logs if anything fails
8. Clean up all containers and volumes

**How to implement:** 
- Add a `/health` endpoint to your FastAPI backend
- Place integration tests in your backend that test API endpoints with the database

---

### 4. Security Scan (`security-scan.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Scheduled weekly (Mondays at 9 AM UTC)

**Jobs:**

#### a. Backend Dependency Scan
- **Purpose:** Find known vulnerabilities in Python packages
- **Tool:** `pip-audit`
- **How it works:** Checks all packages in `requirements.txt` against vulnerability databases

#### b. Frontend Dependency Scan
- **Purpose:** Find known vulnerabilities in npm packages
- **Tool:** `npm audit`
- **How it works:** Checks for moderate and higher severity vulnerabilities

#### c. CodeQL Analysis
- **Purpose:** Static code analysis to find security issues
- **Languages:** Python and JavaScript/TypeScript
- **How it works:** GitHub's semantic code analysis engine scans for common security vulnerabilities and coding errors

**How to implement:** No setup needed. These run automatically. Review the Security tab in your GitHub repository for findings.

---

### 5. Deploy (`deploy.yml`)

**Triggers:**
- Push to `main` branch
- Git tags starting with `v` (e.g., `v1.0.0`)
- Manual workflow dispatch

**Jobs:**

#### a. Deploy Backend
- **Current state:** Template with commented examples
- **Options provided:**
  - GitHub Container Registry (GHCR)
  - AWS ECS/Fargate
  - Google Cloud Run
  - Azure Container Apps
  - Kubernetes
  - Docker on VM

**How to implement:**
1. Choose your deployment platform
2. Uncomment the relevant section
3. Add required secrets to GitHub repository settings
4. Modify the deployment steps for your infrastructure

#### b. Deploy Frontend
- **Current state:** Template with commented examples
- **Options provided:**
  - GitHub Pages
  - Netlify
  - Vercel
  - AWS S3 + CloudFront
  - Azure Static Web Apps

**How to implement:**
1. Choose your hosting platform
2. Uncomment the relevant section
3. Add required secrets/tokens to GitHub repository settings
4. Configure domain and environment settings

---

## Required GitHub Secrets

Depending on which deployment options you enable, you'll need to add these secrets in **Settings > Secrets and variables > Actions**:

### For Container Registry (Backend):
- `GITHUB_TOKEN` - Automatically provided by GitHub

### For Netlify (Frontend):
- `NETLIFY_AUTH_TOKEN` - Your Netlify personal access token
- `NETLIFY_SITE_ID` - Your Netlify site ID

### For Vercel (Frontend):
- `VERCEL_TOKEN` - Your Vercel authentication token
- `VERCEL_ORG_ID` - Your Vercel organization ID
- `VERCEL_PROJECT_ID` - Your Vercel project ID

### For AWS:
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

---

## How Path Filtering Works

Each workflow only runs when relevant files change:

```yaml
paths:
  - 'backend/**'        # Only backend changes trigger backend CI
  - 'frontend/**'       # Only frontend changes trigger frontend CI
```

This saves CI minutes and speeds up feedback.

---

## Caching Strategy

All workflows use caching to speed up builds:

- **Python:** Caches pip packages based on `requirements.txt` hash
- **Node.js:** Caches npm packages based on `package-lock.json` hash
- **Docker:** Uses GitHub Actions cache for Docker layers

**Result:** Subsequent runs are 2-5x faster.

---

## Manual Workflow Execution

You can manually trigger the deployment workflow:
1. Go to **Actions** tab in GitHub
2. Select **Deploy** workflow
3. Click **Run workflow**
4. Choose the branch
5. Click **Run workflow**

---

## Best Practices Implemented

1. ✅ **Fail Fast:** Lint and type-check before running tests
2. ✅ **Isolation:** Each job runs in a clean environment
3. ✅ **Caching:** Dependencies are cached for speed
4. ✅ **Service Containers:** Tests run against real PostgreSQL
5. ✅ **Path Filtering:** Only relevant workflows run on file changes
6. ✅ **Security Scanning:** Automated vulnerability detection
7. ✅ **Artifact Upload:** Build outputs saved for debugging
8. ✅ **Proper Cleanup:** Docker resources cleaned up after tests

---

## Next Steps

1. **Enable CodeQL:** Go to Security > Code scanning > Set up CodeQL
2. **Configure Deployment:** Uncomment and configure the deployment section you need
3. **Add Secrets:** Add required secrets for your deployment platform
4. **Create Health Endpoint:** Add `/health` endpoint to backend for monitoring
5. **Add More Tests:** Expand test coverage in both frontend and backend
6. **Set Branch Protection:** Require CI to pass before merging PRs

---

## Troubleshooting

### If backend tests fail:
- Check PostgreSQL service is running
- Verify DATABASE_URL environment variable
- Review pytest output for specific errors

### If frontend build fails:
- Check for TypeScript errors
- Verify all dependencies are in package.json
- Review build logs for missing environment variables

### If Docker build fails:
- Verify Dockerfile syntax
- Check that all required files exist
- Review build logs for missing dependencies

---

## Workflow Status Badges

Add these to your main README.md:

```markdown
![Backend CI](https://github.com/YOUR_USERNAME/strider/workflows/Backend%20CI/badge.svg)
![Frontend CI](https://github.com/YOUR_USERNAME/strider/workflows/Frontend%20CI/badge.svg)
![Security Scan](https://github.com/YOUR_USERNAME/strider/workflows/Security%20Scan/badge.svg)
```

Replace `YOUR_USERNAME` with your GitHub username or organization name.
