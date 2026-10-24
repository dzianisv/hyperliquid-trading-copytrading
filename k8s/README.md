# Kubernetes Deployment Guide

## Prerequisites

1. Access to a Kubernetes cluster (k3s, minikube, etc.)
2. `kubectl` configured to access your cluster
3. HyperLiquid API credentials

## Configuration

### Required Environment Variables

```bash
export PRIVATE_KEY_API="your_hyperliquid_api_private_key"
export ACCOUNT_TO_COPY="0xYOUR_ACCOUNT_TO_COPY_ADDRESS"
export TRADING_ADDRESS="0xYOUR_TRADING_WALLET_ADDRESS"
```

### Optional Configuration

```bash
export BOT_TYPE="position"           # or "order"
export LEVERAGE="1.0"                 # Position size multiplier
export TRADE_LIMIT="10.0"             # Minimum trade size in USD
export MINI_ALLOC_OF_PF="0.0"        # Minimum portfolio allocation %
```

### For Private Docker Images

If the Docker image is private, set:

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

## Deployment Methods

### Method 1: Using deploy.sh Script (Recommended)

```bash
# Local cluster
cd k8s
./deploy.sh

# Remote cluster via SSH
export SSH_HOST="root@100.88.150.94"
./deploy.sh
```

### Method 2: Manual Deployment

1. **Create ConfigMap:**

```bash
kubectl apply -f configmap.yaml
```

2. **Create Secret from template:**

```bash
# Copy the template
cp secret.yaml.template secret.yaml

# Edit with your values
vim secret.yaml

# Apply
kubectl apply -f secret.yaml

# Delete the file (security)
rm secret.yaml
```

3. **Create GHCR pull secret (if image is private):**

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  --docker-email=your-email@example.com
```

4. **Deploy StatefulSet:**

```bash
kubectl apply -f statefulset.yaml
```

## Managing the Deployment

### Check Status

```bash
kubectl get pods -l app=hyperliquid-bot
kubectl get statefulset hyperliquid-bot
```

### View Logs

```bash
# Follow logs
kubectl logs -f hyperliquid-bot-0

# View recent logs
kubectl logs --tail=100 hyperliquid-bot-0
```

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap hyperliquid-bot-config

# Edit Secret
kubectl edit secret hyperliquid-bot-secrets

# Restart pod to apply changes
kubectl rollout restart statefulset hyperliquid-bot
```

### Delete Deployment

```bash
kubectl delete statefulset hyperliquid-bot
kubectl delete configmap hyperliquid-bot-config
kubectl delete secret hyperliquid-bot-secrets
kubectl delete secret ghcr-secret  # if created
```

## Troubleshooting

### Pod not starting

```bash
# Check pod events
kubectl describe pod hyperliquid-bot-0

# Check logs
kubectl logs hyperliquid-bot-0
```

### Image pull errors

If you see `ImagePullBackOff`:

1. Verify the image exists: `ghcr.io/dzianisv/hyperliquid-trading-copytrading:latest`
2. For private images, ensure `ghcr-secret` is created correctly
3. Check StatefulSet has `imagePullSecrets` configured

### Bot not trading

1. Check logs for errors: `kubectl logs -f hyperliquid-bot-0`
2. Verify environment variables are set correctly
3. Ensure API credentials are valid
4. Check network connectivity from the cluster

## Security Best Practices

1. **Never commit secrets to git**
   - Always use `secret.yaml.template` as reference
   - Create actual `secret.yaml` locally and delete after applying

2. **Use RBAC**
   - Limit service account permissions
   - Use namespaces for isolation

3. **Rotate credentials regularly**
   - Update secrets periodically
   - Use separate API keys for different environments

4. **Monitor resource usage**
   - Set resource limits in StatefulSet
   - Monitor CPU/memory consumption

## Remote Deployment to k3s

For the specific k3s cluster at `root@100.88.150.94`:

```bash
# Set environment variables first
export PRIVATE_KEY_API="..."
export ACCOUNT_TO_COPY="0x..."
export TRADING_ADDRESS="0x..."
export GITHUB_TOKEN="..."  # if needed

# Option 1: Deploy via script
SSH_HOST="root@100.88.150.94" ./deploy.sh

# Option 2: Manual remote deployment
# Copy files to server
scp -r k8s/ root@100.88.150.94:/root/hyperliquid-bot/

# SSH and deploy
ssh root@100.88.150.94
cd /root/hyperliquid-bot
export PRIVATE_KEY_API="..."
export ACCOUNT_TO_COPY="0x..."
export TRADING_ADDRESS="0x..."
./deploy.sh
```
