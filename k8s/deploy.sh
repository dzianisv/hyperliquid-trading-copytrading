#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}HyperLiquid Trading Bot - Kubernetes Deployment${NC}"
echo ""

# Check if we're running on the cluster or need SSH
if [ -n "$SSH_HOST" ]; then
    echo -e "${YELLOW}Deploying to remote cluster: $SSH_HOST${NC}"
    KUBECTL="ssh $SSH_HOST kubectl"
else
    echo -e "${YELLOW}Deploying to local cluster${NC}"
    KUBECTL="kubectl"
fi

# Check for required environment variables
if [ -z "$PRIVATE_KEY_API" ] || [ -z "$ACCOUNT_TO_COPY" ] || [ -z "$TRADING_ADDRESS" ]; then
    echo -e "${RED}Error: Required environment variables not set${NC}"
    echo "Please set the following environment variables:"
    echo "  PRIVATE_KEY_API      - Your HyperLiquid API private key"
    echo "  ACCOUNT_TO_COPY      - The wallet address to copy (0x...)"
    echo "  TRADING_ADDRESS      - Your trading wallet address (0x...)"
    echo ""
    echo "Optional configuration:"
    echo "  BOT_TYPE             - 'position' or 'order' (default: position)"
    echo "  LEVERAGE             - Position size multiplier (default: 1.0)"
    echo "  TRADE_LIMIT          - Minimum trade size in USD (default: 10.0)"
    echo "  MINI_ALLOC_OF_PF     - Minimum portfolio allocation % (default: 0.0)"
    exit 1
fi

# Set defaults for optional variables
BOT_TYPE=${BOT_TYPE:-position}
LEVERAGE=${LEVERAGE:-1.0}
TRADE_LIMIT=${TRADE_LIMIT:-10.0}
MINI_ALLOC_OF_PF=${MINI_ALLOC_OF_PF:-0.0}

echo ""
echo "Configuration:"
echo "  Bot Type: $BOT_TYPE"
echo "  Account to Copy: $ACCOUNT_TO_COPY"
echo "  Trading Address: $TRADING_ADDRESS"
echo "  Leverage: ${LEVERAGE}x"
echo "  Trade Limit: \$$TRADE_LIMIT"
echo ""

# Apply ConfigMap
echo -e "${GREEN}Creating ConfigMap...${NC}"
cat <<EOF | $KUBECTL apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: hyperliquid-bot-config
  namespace: default
data:
  BOT_TYPE: "$BOT_TYPE"
  LEVERAGE: "$LEVERAGE"
  TRADE_LIMIT: "$TRADE_LIMIT"
  MINI_ALLOC_OF_PF: "$MINI_ALLOC_OF_PF"
EOF

# Create Secret
echo -e "${GREEN}Creating Secret...${NC}"
cat <<EOF | $KUBECTL apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: hyperliquid-bot-secrets
  namespace: default
type: Opaque
stringData:
  PRIVATE_KEY_API: "$PRIVATE_KEY_API"
  ACCOUNT_TO_COPY: "$ACCOUNT_TO_COPY"
  TRADING_ADDRESS: "$TRADING_ADDRESS"
EOF

# Create image pull secret for GHCR if GITHUB_TOKEN is provided
if [ -n "$GITHUB_TOKEN" ]; then
    echo -e "${GREEN}Creating GitHub Container Registry pull secret...${NC}"
    $KUBECTL create secret docker-registry ghcr-secret \
        --docker-server=ghcr.io \
        --docker-username=dzianisv \
        --docker-password="$GITHUB_TOKEN" \
        --docker-email=noreply@github.com \
        --dry-run=client -o yaml | $KUBECTL apply -f -
else
    echo -e "${YELLOW}Note: GITHUB_TOKEN not set, skipping GHCR pull secret${NC}"
    echo -e "${YELLOW}If the image is private, set GITHUB_TOKEN to create pull secret${NC}"
fi

# Deploy StatefulSet
echo -e "${GREEN}Deploying StatefulSet...${NC}"
$KUBECTL apply -f k8s/statefulset.yaml

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "To check the status:"
echo "  $KUBECTL get pods -l app=hyperliquid-bot"
echo ""
echo "To view logs:"
echo "  $KUBECTL logs -f hyperliquid-bot-0"
echo ""
echo "To delete the deployment:"
echo "  $KUBECTL delete statefulset hyperliquid-bot"
echo "  $KUBECTL delete configmap hyperliquid-bot-config"
echo "  $KUBECTL delete secret hyperliquid-bot-secrets"
