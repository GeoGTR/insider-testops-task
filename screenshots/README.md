# Deployment Screenshots - AWS EKS

Screenshots from deployment and test execution on AWS EKS cluster.

## image-01.png
Python deployment script execution start. Shows configuration parameters:
- Chrome Node Count: 1
- Namespace: insider
- Helm chart installation in progress

## image-02.png
Deployment script completion. Shows:
- All pods ready status
- Test execution results (5 tests passed, 0 failed)
- Total duration: 98.26 seconds

## image-03.png
Kubernetes cluster status from EC2 instance:
- `kubectl get all -n insider`: Shows all resources (deployments, services, jobs, pods)
- `kubectl get job`: Test Controller Job details with completion status

## image-04.png
Chrome Node pod logs showing:
- Selenium Server startup
- WebDriver endpoint availability
- Session management and browser lifecycle

## image-05.png
GitHub Actions workflow execution summary:
- Manual workflow trigger (Run Tests on Kubernetes)
- Test execution results in GitHub Actions UI
- Configuration parameters and test results displayed
- Automated deployment and testing on AWS EKS

## ec2-demo.cast
Terminal recording of complete deployment workflow. To view:

```bash
# Install asciinema
brew install asciinema  # macOS
sudo apt install asciinema  # Ubuntu

# Play recording
asciinema play ec2-demo.cast
```
