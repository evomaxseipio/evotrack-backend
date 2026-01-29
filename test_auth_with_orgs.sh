#!/bin/bash
# Script para probar los endpoints de autenticación con organizaciones

BASE_URL="http://localhost:8000/api/v1"

echo "🧪 Probando endpoints de autenticación con organizaciones"
echo "=================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Registrar un nuevo usuario
echo -e "${BLUE}1. Registrando nuevo usuario...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPass123",
    "first_name": "Test",
    "last_name": "User"
  }')

echo "$REGISTER_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REGISTER_RESPONSE"
echo ""

# Extraer access_token si existe
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('access_token', ''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${YELLOW}⚠️  No se pudo obtener el token. Intentando login...${NC}"
  
  # Intentar login
  echo -e "${BLUE}2. Intentando login...${NC}"
  LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "testuser@example.com",
      "password": "TestPass123"
    }')
  
  echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('access_token', ''))" 2>/dev/null)
fi

echo ""
echo -e "${GREEN}✅ Verificando campos en la respuesta:${NC}"
echo ""

# Verificar que la respuesta tenga los nuevos campos
if [ ! -z "$ACCESS_TOKEN" ]; then
  echo -e "${BLUE}3. Verificando endpoint /me con token...${NC}"
  ME_RESPONSE=$(curl -s -X GET "${BASE_URL}/auth/me" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")
  
  echo "$ME_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ME_RESPONSE"
  
  echo ""
  echo -e "${GREEN}📋 Campos verificados:${NC}"
  echo "$ME_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    user = data.get('data', {}).get('user', data.get('user', {}))
    print(f\"  ✓ full_name: {user.get('full_name', '❌ NO ENCONTRADO')}\")
    print(f\"  ✓ has_organization: {user.get('has_organization', '❌ NO ENCONTRADO')}\")
    print(f\"  ✓ organizations: {len(user.get('organizations', []))} organización(es)\")
    if user.get('organizations'):
        for org in user['organizations']:
            print(f\"    - {org.get('name')} (slug: {org.get('slug')}, role: {org.get('role')})\")
except Exception as e:
    print(f\"Error: {e}\")
" 2>/dev/null || echo "  ⚠️  No se pudo parsear la respuesta"
else
  echo -e "${YELLOW}⚠️  No se pudo obtener el token de acceso${NC}"
fi

echo ""
echo "=================================================="
echo "✅ Prueba completada"
