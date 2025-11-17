# DNS Resolution Error - Troubleshooting Guide

## Problem
The `command_script.py` uses Kubernetes service DNS names (like `promptimizer-service`, `llama-service`) which only resolve inside a Kubernetes cluster.

## Solutions

### Option 1: Run Script Inside Kubernetes Cluster (Recommended)
The script is designed to run as the "orchestrator" pod in your Kubernetes cluster.

1. Deploy all services to your cluster:
   ```bash
   kubectl apply -f coordinatorv2.yaml
   ```

2. Set environment variable in the orchestrator deployment to indicate cluster mode:
   ```yaml
   env:
   - name: RUNNING_IN_CLUSTER
     value: "true"
   ```

3. The script will automatically use Kubernetes service DNS names.

### Option 2: Run Script Locally with Port Forwarding
If you want to run the script locally for testing:

1. Deploy services to Kubernetes:
   ```bash
   kubectl apply -f coordinatorv2.yaml
   ```

2. Port-forward each service to localhost (in separate terminals):
   ```bash
   kubectl port-forward service/promptimizer-service 11434:11434
   kubectl port-forward service/llama-service 11435:11434
   kubectl port-forward service/qwen-service 11436:11434
   kubectl port-forward service/qwen-small-service 11437:11434
   kubectl port-forward service/judge-service 11438:11434
   ```

3. Set environment variables (or leave as default):
   ```bash
   # PowerShell
   $env:RUNNING_IN_CLUSTER="false"
   $env:PROMPTIMIZER_URL="http://localhost:11434/api/generate"
   $env:LLAMA_URL="http://localhost:11435/api/generate"
   $env:QWEN_URL="http://localhost:11436/api/generate"
   $env:QWEN_SMALL_URL="http://localhost:11437/api/generate"
   $env:JUDGE_URL="http://localhost:11438/api/generate"
   ```

4. Run the script:
   ```bash
   python command_script.py
   ```

### Option 3: Run All Services Locally with Ollama
If you have Ollama running locally:

1. Start Ollama and pull all models:
   ```bash
   ollama pull granite4:350m
   ollama pull llama3.2:1b-instruct-q4_0
   ollama pull qwen2.5-coder:1.5b-instruct-q4_0
   ollama pull qwen3:0.6b
   ollama pull gemma3:1b
   ```

2. Since Ollama can only serve one model at a time on the default port, you'll need to:
   - Run multiple Ollama instances on different ports, OR
   - Modify the script to use the same endpoint with different models, OR
   - Use Docker containers for each model (recommended)

## Verification

To verify DNS resolution works:

### Inside Kubernetes:
```bash
kubectl exec -it deployment/orchestrator -- nslookup promptimizer-service
```

### Locally:
```bash
# PowerShell
Test-NetConnection localhost -Port 11434
```

## Error Messages Explained

- **"Connection failed... DNS resolves"**: The hostname cannot be resolved. Use one of the solutions above.
- **"Request timed out"**: Service is not responding or not running. Check pod status: `kubectl get pods`
- **"Connection refused"**: Service exists but not accepting connections. Check service logs: `kubectl logs deployment/[service-name]`
