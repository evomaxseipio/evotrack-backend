#!/bin/bash
# Quick Fix para Puerto 5432 en Uso

echo "🔍 Diagnosticando conflicto de puerto 5432..."
echo ""

# Verificar qué está usando el puerto
echo "Proceso usando puerto 5432:"
sudo lsof -i :5432 2>/dev/null || echo "No se pudo verificar (requiere sudo)"
echo ""

echo "Opciones disponibles:"
echo ""
echo "1️⃣  OPCIÓN 1: Usar puerto 5433 para Docker PostgreSQL (YA APLICADO)"
echo "   Comando: docker-compose up --build"
echo ""
echo "2️⃣  OPCIÓN 2: Detener PostgreSQL local"
echo "   Comando: sudo systemctl stop postgresql"
echo "   Luego: docker-compose up --build"
echo ""
echo "3️⃣  OPCIÓN 3: Usar PostgreSQL local + Solo FastAPI en Docker"
echo "   Primero crear DB local:"
echo "   psql -U postgres -c \"CREATE USER evotrack_user WITH PASSWORD 'evotrack_password';\""
echo "   psql -U postgres -c \"CREATE DATABASE evotrack_db OWNER evotrack_user;\""
echo "   Luego: docker-compose -f docker-compose-dev.yml up --build"
echo ""
echo "💡 Recomendación: Opción 1 (más simple)"
