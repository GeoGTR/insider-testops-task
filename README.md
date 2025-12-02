# Insider TestOps - Kubernetes Test Automation

Selenium-based end-to-end test automation system deployed on Kubernetes using Helm charts. Tests run in isolated containers with dynamic Chrome node scaling and remote WebDriver communication.

## System Architecture

### Components

**Test Controller (Job)**
- Executes pytest test suite
- Manages test lifecycle and reporting
- Communicates with Chrome nodes via Remote WebDriver protocol
- Runs as Kubernetes Job with single execution

**Chrome Nodes (Deployment)**
- Provides Selenium Standalone Chrome instances
- Exposes WebDriver server on port 4444
- Scales dynamically based on node_count parameter (1-5)
- Stateless browser service for parallel test execution

**Service Discovery**
- Kubernetes Service provides stable DNS endpoint
- ClusterIP service routes traffic to available Chrome pods
- Built-in load balancing across multiple Chrome instances

### Inter-Pod Communication

Test Controller connects to Chrome nodes using Selenium's Remote WebDriver pattern over HTTP:

```
Test Controller Pod
    |
    | HTTP POST /session
    v
chrome-node-service:4444 (Kubernetes Service)
    |
    | DNS resolution + Load balancing
    v
Chrome Node Pod(s)
    |
    | WebDriver commands execution
    v
Browser actions + responses
```

Configuration is injected via ConfigMap containing the Chrome service URL. The Test Controller uses standard Selenium Remote WebDriver client, while Chrome nodes run Selenium Standalone Server.

## Prerequisites

### Local Development
- Docker Desktop with Kubernetes enabled
- kind (Kubernetes in Docker) for local cluster
- Helm 3.x
- Python 3.9+
- kubectl configured

### AWS Deployment
- AWS account with EKS access
- EC2 instance (t3.small or larger recommended)
- kubectl and aws-cli configured
- Docker Hub account for image hosting

## Project Structure

```
insider-testops-task/
├── tests/                          # Test suite
│   ├── conftest.py                 # Pytest fixtures and configuration
│   ├── test_insider_home.py        # Homepage validation tests
│   ├── test_insider_careers.py     # Career page navigation tests
│   ├── test_qa_jobs.py             # QA jobs filtering and verification
│   └── pages/                      # Page Object Model
│       ├── base_page.py
│       ├── home_page.py
│       ├── careers_page.py
│       └── qa_jobs_page.py
├── helm/insider-tests/             # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml                 # Default configuration (local)
│   ├── values-aws.yaml             # AWS-specific overrides
│   └── templates/
│       ├── _helpers.tpl            # Template library functions
│       ├── chrome-node-deployment.yaml
│       ├── chrome-node-service.yaml
│       ├── test-controller-job.yaml
│       ├── configmap.yaml
│       └── NOTES.txt
├── scripts/
│   └── deploy_and_run.py           # Automated deployment script
├── Dockerfile.test-controller      # Test runner container
├── Dockerfile.chrome-node-x86      # Chrome browser container (x86)
├── Dockerfile.chrome-node-arm      # Chrome browser container (ARM)
├── pytest.ini                      # Pytest configuration
└── requirements.txt                # Python dependencies
```

## Test Suite

### Test Cases

1. **Homepage Validation** (`test_insider_home.py`)
   - Verifies Insider homepage loads correctly
   - Validates page title and URL

2. **Career Page Navigation** (`test_insider_careers.py`)
   - Navigates Company > Careers
   - Verifies Locations, Teams, and Life at Insider sections

3. **QA Jobs Filtering** (`test_qa_jobs.py`)
   - Opens Quality Assurance careers page
   - Filters by Location: Istanbul, Turkey
   - Filters by Department: Quality Assurance
   - Verifies job listings presence

4. **Job Details Verification** (`test_qa_jobs.py`)
   - Validates Position field contains "Quality Assurance"
   - Validates Department field contains "Quality Assurance"
   - Validates Location field contains "Istanbul, Turkey"

5. **Lever Application Redirect** (`test_qa_jobs.py`)
   - Clicks "View Role" button
   - Verifies redirect to Lever application form
   - Validates destination URL

### Page Object Model

Tests use Page Object Model pattern for maintainability:

- `BasePage`: Common methods (find_element, click, wait)
- `HomePage`: Homepage interactions
- `CareersPage`: Career page navigation
- `QAJobsPage`: Job filtering and verification

## Local Deployment

### Step 1: Create Local Kubernetes Cluster

Using kind (Kubernetes in Docker):

```bash
kind create cluster --name insider-testops
kubectl config use-context kind-insider-testops
```

### Step 2: Build Docker Images

```bash
# Build Test Controller
docker build -t insider-test-controller:latest -f Dockerfile.test-controller .

# Build Chrome Node (ARM for Apple Silicon)
docker build -t insider-chrome-node:latest -f Dockerfile.chrome-node-arm .
# Build Chrome Node (x86 for Intel/AMD)
docker build -t insider-chrome-node:latest -f Dockerfile.chrome-node-x86 .
```

# Load images into kind cluster
```bash
kind load docker-image insider-test-controller:latest --name insider-testops
kind load docker-image insider-chrome-node:latest --name insider-testops
```

### Step 3: Deploy with Helm

```bash
# Deploy with default configuration
helm install insider-tests ./helm/insider-tests \
  --namespace insider \
  --create-namespace

# Or use automated script
python3 scripts/deploy_and_run.py \
  --node-count 2 \
  --namespace insider \
  --helm-chart-path ./helm/insider-tests
```

### Step 4: Monitor Execution

```bash
# Check pod status
kubectl get pods -n insider

# View test logs
kubectl logs -f job/insider-tests-test-controller-1 -n insider

# Check Chrome node status
kubectl get deployment insider-tests-chrome-node -n insider
```

### Step 5: Cleanup

```bash
helm uninstall insider-tests --namespace insider
```

## AWS EKS Deployment

### Step 1: Build Multi-Architecture Images

```bash
# Build and push x86 images to Docker Hub
docker buildx build --platform linux/amd64 \
  -t geogtr/insider-test-controller:latest \
  -f Dockerfile.test-controller \
  --push .

# Build and push Chrome Node x86 image
docker buildx build --platform linux/amd64 \
  -t geogtr/insider-chrome-node:latest \
  -f Dockerfile.chrome-node-x86 \
  --push .
```

### Step 2: Create EKS Cluster

```bash
# Create EKS cluster (if not exists)
eksctl create cluster \
  --name insider-testops \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.small \
  --nodes 1 \
  --nodes-min 1 \
  --nodes-max 2

# Configure kubectl
aws eks update-kubeconfig --name insider-testops --region us-east-1
```

### Step 3: Deploy to EKS

```bash
# Switch to EKS context
kubectl config use-context <eks-context-name>

# Deploy with AWS-specific values
python3 scripts/deploy_and_run.py \
  --node-count 1 \
  --namespace insider \
  --helm-chart-path ./helm/insider-tests \
  --values-file ./helm/insider-tests/values-aws.yaml
```

### Step 4: Verify Deployment

```bash
# Check cluster resources
kubectl get all -n insider

# View test execution
kubectl logs job/insider-tests-test-controller-1 -n insider

# Check Chrome nodes
kubectl get pods -l app.kubernetes.io/component=chrome-node -n insider
```

## Configuration

### Helm Values

**values.yaml** (Local development):
```yaml
chromeNode:
  nodeCount: 1
  image:
    repository: insider-chrome-node
    tag: latest
    pullPolicy: IfNotPresent
```

**values-aws.yaml** (Production):
```yaml
chromeNode:
  nodeCount: 1
  image:
    repository: geogtr/insider-chrome-node
    tag: latest
    pullPolicy: Always  # Always pull latest from registry
```

### Environment Variables (ConfigMap)

- `CHROME_SERVICE_URL`: Chrome node service endpoint
- `APP_BASE_URL`: Application under test URL
- `RUNNING_IN_CONTAINER`: Container execution flag

### Resource Limits

**Chrome Node**:
- Requests: 512Mi memory, 500m CPU
- Limits: 1Gi memory, 1000m CPU

**Test Controller**:
- Requests: 256Mi memory, 250m CPU
- Limits: 512Mi memory, 500m CPU

## Python Deployment Script

The `deploy_and_run.py` script provides automated deployment and monitoring:

**Features**:
- Helm chart installation with custom parameters
- Dynamic node count configuration (1-5)
- Pod readiness monitoring with timeout
- Test execution tracking
- Log retrieval and display
- Optional cleanup on completion

**Usage**:
```bash
python3 scripts/deploy_and_run.py \
  --node-count 3 \
  --namespace insider \
  --wait-timeout 300 \
  --cleanup \
  --values-file ./helm/insider-tests/values-aws.yaml
```

**Arguments**:
- `--node-count`: Number of Chrome nodes (1-5, default: 2)
- `--namespace`: Kubernetes namespace (default: default)
- `--wait-timeout`: Pod ready timeout in seconds (default: 300)
- `--cleanup`: Remove resources after execution
- `--helm-chart-path`: Path to Helm chart directory
- `--values-file`: Custom Helm values file

## Docker Images

### Test Controller Image

Based on `python:3.9-slim` with:
- pytest and selenium packages
- Test suite and page objects
- Non-root user (UID 1000) for security
- Working directory: `/app`

### Chrome Node Image

Uses `selenium/standalone-chrome:124.0` providing:
- Chrome browser 124.0
- Selenium Server
- WebDriver endpoint on port 4444
- Headless mode support

## Security

**Container Security**:
- Non-root user execution (UID 1000)
- Dropped ALL capabilities
- seccomp profile: RuntimeDefault
- Read-only root filesystem disabled (Chrome requires /tmp write)

**Network Security**:
- ClusterIP service (internal only)
- No external ingress
- Pod-to-pod communication within namespace

## GitHub Actions CI/CD

This project includes automated workflows for continuous integration and deployment.

### Build and Push Workflow

Automatically builds and pushes Docker images to Docker Hub on every commit to main or develop branches.

**Triggered on:**
- Push to main/develop branches
- Pull requests to main

**Actions:**
- Builds Test Controller and Chrome Node images for linux/amd64 platform
- Pushes to Docker Hub registry (geogtr/insider-test-controller, geogtr/insider-chrome-node)
- Automatic tagging: branch name, commit SHA, and latest

### Run Tests Workflow

Manual workflow for executing tests on AWS EKS cluster directly from GitHub Actions.

**Manual Trigger:** Actions tab > Run Tests on Kubernetes > Run workflow

**Parameters:**
- **node_count**: Number of Chrome nodes (1-5)
- **namespace**: Kubernetes namespace (default: insider)
- **cleanup**: Cleanup resources after tests (true/false)

**Prerequisites:**
GitHub repository secrets must be configured:
- `AWS_ROLE_ARN`: IAM role ARN for OIDC authentication
- `DOCKER_PASSWORD`: Docker Hub access token

**Workflow Steps:**
1. Sets up Python, kubectl, and Helm
2. Authenticates to AWS using OIDC
3. Configures kubectl for EKS cluster
4. Executes deployment script with selected parameters
5. Captures test results and generates summary
6. Displays results in GitHub Actions summary with:
   - Configuration details
   - Test pass/fail counts
   - Execution duration
   - Pod status
   - Full test output (collapsible)

**Example Summary Output:**
```
Test Execution Summary
Configuration:
- Chrome Nodes: 1
- Namespace: insider
- Cleanup: true

Results:
- Passed: 5
- Failed: 0
- Duration: 98.26s

✅ All tests passed!
```

This workflow enables team members to run tests on-demand without local environment setup or AWS access.

## Troubleshooting

### Common Issues

**ImagePullBackOff**:
```bash
# Check image exists and is accessible
docker manifest inspect geogtr/insider-test-controller:latest

# Verify pull policy
kubectl describe pod <pod-name> -n insider | grep -A5 "Image"
```

**Connection Refused to Chrome Service**:
```bash
# Verify service exists
kubectl get svc chrome-node-service -n insider

# Check endpoints
kubectl get endpoints chrome-node-service -n insider

# Test DNS resolution
kubectl exec <test-pod> -n insider -- nslookup chrome-node-service
```

**Tests Failing**:
```bash
# View full test logs
kubectl logs job/insider-tests-test-controller-1 -n insider

# Check Chrome node logs
kubectl logs deployment/insider-tests-chrome-node -n insider
```

**Pod Not Ready**:
```bash
# Describe pod for events
kubectl describe pod <pod-name> -n insider

# Check resource constraints
kubectl top nodes
kubectl top pods -n insider
```

## Performance Considerations

**Scaling Guidelines**:
- 1 Chrome node: Single test execution
- 2-3 Chrome nodes: Parallel test execution (recommended)
- 4-5 Chrome nodes: Maximum parallelization (requires adequate cluster resources)

**Resource Planning**:
- Minimum cluster: 2 vCPU, 2GB RAM (t3.small)
- Per Chrome node: 500m CPU, 512Mi memory
- Per test controller: 250m CPU, 256Mi memory

**Test Execution Time**:
- Full suite (5 tests): ~70-100 seconds
- Single Chrome node: Sequential execution
- Multiple Chrome nodes: Load-balanced execution


## Deployment Demo

Watch the complete deployment process from AWS EKS setup to test execution:

[![asciicast](https://asciinema.org/a/2eUANzCSqA4qOnmIA6klF7SeV.svg)](https://asciinema.org/a/2eUANzCSqA4qOnmIA6klF7SeV)

This terminal recording demonstrates:
- EKS cluster verification
- Helm chart deployment with Python script
- Test execution and results
- Pod status monitoring

## Conclusion
This project is created for Insider TestOps technical assessment.