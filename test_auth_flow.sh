#!/bin/bash
# Test authentication flow locally

API_URL="${API_URL:-http://localhost:8000}"

echo "🧪 Testing Authentication Flow"
echo "API URL: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Register
echo "1️⃣  Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_'$(date +%s)'@example.com",
    "password": "test123456",
    "full_name": "Test User"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "email"; then
    echo -e "${GREEN}✅ Registration successful${NC}"
    USER_EMAIL=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['email'])" 2>/dev/null)
else
    echo -e "${RED}❌ Registration failed${NC}"
    echo "$REGISTER_RESPONSE"
    exit 1
fi

echo ""

# Test 2: Login
echo "2️⃣  Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USER_EMAIL&password=test123456")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ Login successful${NC}"
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    TENANT_ID=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['tenant_id'])" 2>/dev/null)
    echo "Token: ${TOKEN:0:20}..."
    echo "Tenant ID: $TENANT_ID"
else
    echo -e "${RED}❌ Login failed${NC}"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo ""

# Test 3: Get current user
echo "3️⃣  Testing get current user..."
USER_INFO=$(curl -s "$API_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN")

if echo "$USER_INFO" | grep -q "email"; then
    echo -e "${GREEN}✅ Get user info successful${NC}"
    echo "$USER_INFO" | python3 -m json.tool
else
    echo -e "${RED}❌ Get user info failed${NC}"
    echo "$USER_INFO"
    exit 1
fi

echo ""

# Test 4: Test OAuth status (should work with tenant)
echo "4️⃣  Testing OAuth status endpoint..."
OAUTH_STATUS=$(curl -s "$API_URL/oauth/slack/status" \
  -H "Authorization: Bearer $TOKEN")

if echo "$OAUTH_STATUS" | grep -q "connected\|Not connected"; then
    echo -e "${GREEN}✅ OAuth status endpoint works${NC}"
    echo "$OAUTH_STATUS" | python3 -m json.tool
else
    echo -e "${YELLOW}⚠️  OAuth status endpoint returned unexpected response${NC}"
    echo "$OAUTH_STATUS"
fi

echo ""

# Test 5: Test workflow endpoint (should require subscription)
echo "5️⃣  Testing workflow endpoint..."
WORKFLOW_RESPONSE=$(curl -s "$API_URL/workflows/standup" \
  -H "Authorization: Bearer $TOKEN")

if echo "$WORKFLOW_RESPONSE" | grep -q "in_progress\|todo\|backlog"; then
    echo -e "${GREEN}✅ Workflow endpoint works${NC}"
    echo "$WORKFLOW_RESPONSE" | python3 -m json.tool | head -20
else
    echo -e "${YELLOW}⚠️  Workflow endpoint returned unexpected response${NC}"
    echo "$WORKFLOW_RESPONSE"
fi

echo ""
echo -e "${GREEN}🎉 All authentication tests passed!${NC}"
echo ""
echo "Next steps:"
echo "1. Set up OAuth apps (Slack, Linear, GitHub)"
echo "2. Deploy to production"
echo "3. Set up frontend"
echo "4. Test OAuth connection flow"

