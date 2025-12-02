#!/usr/bin/env python3
"""
Insider TestOps Deployment and Test Execution Script

This script:
1. Deploys Kubernetes resources using Helm chart
2. Accepts --node-count parameter for Chrome node replicas (min=1, max=5)
3. Waits for all pods to be ready
4. Monitors test execution and displays results
5. Cleans up resources after test completion
"""

import argparse
import sys
import time
import subprocess
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Deploy and run Selenium tests on Kubernetes using Helm'
    )
    parser.add_argument(
        '--node-count',
        type=int,
        default=2,
        choices=range(1, 6),
        help='Number of Chrome node replicas (min: 1, max: 5, default: 2)'
    )
    parser.add_argument(
        '--namespace',
        type=str,
        default='default',
        help='Kubernetes namespace (default: default)'
    )
    parser.add_argument(
        '--wait-timeout',
        type=int,
        default=300,
        help='Timeout in seconds to wait for pods (default: 300)'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up resources after test execution'
    )
    parser.add_argument(
        '--helm-chart-path',
        type=str,
        default='./helm/insider-tests',
        help='Path to Helm chart (default: ./helm/insider-tests)'
    )
    parser.add_argument(
        '--values-file',
        type=str,
        help='Custom Helm values file (e.g., values-aws.yaml)'
    )
    return parser.parse_args()


def run_command(cmd, description, check=True):
    """Run shell command and handle errors"""
    print(f"  → {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        if result.returncode == 0:
            print(f"    ✓ {description} completed")
            return result.stdout
        else:
            print(f"    ✗ {description} failed")
            if result.stderr:
                print(f"    Error: {result.stderr}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"    ✗ {description} failed: {e}")
        if e.stderr:
            print(f"    Error: {e.stderr}")
        return None


def deploy_with_helm(args):
    """Deploy Kubernetes resources using Helm"""
    print(f"\n{'='*60}")
    print("DEPLOYING WITH HELM")
    print(f"{'='*60}\n")

    release_name = "insider-tests"

    # Check if Helm release exists
    check_cmd = f"helm list -n {args.namespace} | grep {release_name}"
    existing = run_command(check_cmd, "Checking existing Helm release", check=False)

    # Prepare Helm command
    if existing:
        helm_cmd = f"helm upgrade {release_name} {args.helm_chart_path}"
        action = "Upgrading"
    else:
        helm_cmd = f"helm install {release_name} {args.helm_chart_path}"
        action = "Installing"

    helm_cmd += f" --set chromeNode.nodeCount={args.node_count}"
    helm_cmd += f" --namespace {args.namespace}"
    helm_cmd += " --create-namespace"
    if args.values_file:
        helm_cmd += f" -f {args.values_file}"
    helm_cmd += " --wait --timeout 5m"

    result = run_command(helm_cmd, f"{action} Helm chart")

    if result is None:
        print("\n✗ Helm deployment failed")
        return False

    print(f"\n✓ Helm deployment completed successfully")
    print(f"  Release: {release_name}")
    print(f"  Chrome Nodes: {args.node_count}")
    return True


def load_kube_config():
    """Load Kubernetes configuration"""
    try:
        config.load_kube_config()
        print("✓ Kubernetes config loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load kube config: {e}")
        return False


def wait_for_pods_ready(core_v1, namespace, timeout):
    """Wait for all pods to be ready"""
    print(f"\n{'='*60}")
    print("WAITING FOR PODS")
    print(f"{'='*60}\n")
    print(f"Timeout: {timeout}s\n")

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Get all pods
            pods = core_v1.list_namespaced_pod(namespace=namespace)

            chrome_pods = []
            test_pod = None

            for pod in pods.items:
                # Skip completed/failed pods
                if pod.status.phase in ['Succeeded', 'Failed']:
                    continue

                if 'chrome-node' in pod.metadata.name:
                    chrome_pods.append(pod)
                elif 'test-controller' in pod.metadata.name:
                    test_pod = pod

            # Check chrome nodes ready
            chrome_ready = sum(1 for pod in chrome_pods
                             if pod.status.phase == 'Running'
                             and any(c.type == 'Ready' and c.status == 'True'
                                   for c in (pod.status.conditions or [])))

            print(f"  Chrome Nodes: {chrome_ready}/{len(chrome_pods)} ready", end='')

            # Check test controller
            if test_pod:
                test_status = test_pod.status.phase
                print(f" | Test Controller: {test_status}", end='')

            print('\r', end='')

            # All chrome nodes ready
            if len(chrome_pods) > 0 and chrome_ready == len(chrome_pods):
                print(f"\n\n✓ All {len(chrome_pods)} Chrome nodes are ready")
                return True

            time.sleep(2)

        except ApiException as e:
            print(f"\n✗ Error checking pod status: {e}")
            return False

    print(f"\n✗ Timeout waiting for pods to be ready")
    return False


def wait_for_test_completion(core_v1, namespace, timeout):
    """Wait for test controller job to complete"""
    print(f"\n{'='*60}")
    print("WAITING FOR TEST EXECUTION")
    print(f"{'='*60}\n")

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            pods = core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector="app.kubernetes.io/component=test-controller"
            )

            if not pods.items:
                time.sleep(2)
                continue

            pod = pods.items[0]
            phase = pod.status.phase

            print(f"  Test Controller Status: {phase}    \r", end='')

            if phase == 'Succeeded':
                print(f"\n\n✓ Tests completed successfully")
                return pod.metadata.name
            elif phase == 'Failed':
                print(f"\n\n✗ Tests failed")
                return pod.metadata.name

            time.sleep(2)

        except ApiException as e:
            print(f"\n✗ Error waiting for test completion: {e}")
            return None

    print(f"\n✗ Timeout waiting for test completion")
    return None


def get_test_logs(core_v1, namespace, pod_name):
    """Get logs from test controller pod"""
    print(f"\n{'='*60}")
    print("TEST EXECUTION RESULTS")
    print(f"{'='*60}\n")

    try:
        logs = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container='test-runner'
        )
        print(logs)
        return True
    except ApiException as e:
        print(f"✗ Failed to get logs: {e}")
        return False


def cleanup_resources(args):
    """Clean up Helm release"""
    print(f"\n{'='*60}")
    print("CLEANUP")
    print(f"{'='*60}\n")

    cmd = f"helm uninstall insider-tests --namespace {args.namespace}"
    result = run_command(cmd, "Removing Helm release")

    if result:
        print("\n✓ Cleanup completed")
        return True
    else:
        print("\n✗ Cleanup failed")
        return False


def display_cluster_info(core_v1, apps_v1, namespace):
    """Display cluster deployment information"""
    print(f"\n{'='*60}")
    print("CLUSTER STATUS")
    print(f"{'='*60}\n")

    try:
        # Get deployments
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)

        print("Deployments:")
        for dep in deployments.items:
            replicas = dep.status.replicas or 0
            ready = dep.status.ready_replicas or 0
            print(f"  {dep.metadata.name}: {ready}/{replicas} ready")

        # Get jobs
        batch_v1 = client.BatchV1Api()
        jobs = batch_v1.list_namespaced_job(namespace=namespace)

        print("\nJobs:")
        for job in jobs.items:
            succeeded = job.status.succeeded or 0
            failed = job.status.failed or 0
            active = job.status.active or 0
            print(f"  {job.metadata.name}: Active={active}, Succeeded={succeeded}, Failed={failed}")

        # Get services
        services = core_v1.list_namespaced_service(namespace=namespace)

        print("\nServices:")
        for svc in services.items:
            if svc.metadata.name == 'kubernetes':
                continue
            cluster_ip = svc.spec.cluster_ip
            ports = [f"{p.port}/{p.protocol}" for p in svc.spec.ports]
            print(f"  {svc.metadata.name}: {cluster_ip} - {', '.join(ports)}")

        print(f"\n{'='*60}\n")

    except ApiException as e:
        print(f"✗ Failed to get cluster info: {e}")


def main():
    """Main execution flow"""
    args = parse_args()

    print(f"\n{'='*60}")
    print("INSIDER TESTOPS DEPLOYMENT & EXECUTION")
    print(f"{'='*60}\n")
    print(f"Chrome Node Count: {args.node_count}")
    print(f"Namespace: {args.namespace}")
    print(f"Helm Chart: {args.helm_chart_path}")
    print(f"Cleanup After: {'Yes' if args.cleanup else 'No'}\n")

    # Deploy with Helm
    if not deploy_with_helm(args):
        sys.exit(1)

    # Load Kubernetes config
    if not load_kube_config():
        sys.exit(1)

    # Initialize API clients
    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    # Wait for Chrome nodes to be ready
    if not wait_for_pods_ready(core_v1, args.namespace, args.wait_timeout):
        sys.exit(1)

    # Display cluster info
    display_cluster_info(core_v1, apps_v1, args.namespace)

    # Wait for test completion
    pod_name = wait_for_test_completion(core_v1, args.namespace, args.wait_timeout)
    if not pod_name:
        sys.exit(1)

    # Get and display test logs
    if not get_test_logs(core_v1, args.namespace, pod_name):
        sys.exit(1)

    # Cleanup if requested
    if args.cleanup:
        cleanup_resources(args)

    print("\n✓ Deployment and test execution completed successfully\n")


if __name__ == '__main__':
    main()
