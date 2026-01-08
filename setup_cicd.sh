#!/bin/bash
# Quick CI/CD Setup Script for EvoTrack Backend

set -e

echo "🚀 EvoTrack CI/CD Setup"
echo "======================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    echo "Run: git init"
    exit 1
fi

echo "✓ Git repository detected"

# Install development dependencies
echo ""
echo "📦 Installing development dependencies..."
pip install -r requirements-dev.txt

echo "✓ Development dependencies installed"

# Setup pre-commit hooks
echo ""
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

echo "✓ Pre-commit hooks installed"

# Run initial checks
echo ""
echo "🔍 Running initial code quality checks..."

echo "  → Ruff linting..."
ruff check app/ tests/ --fix || echo "  ⚠️  Some linting issues found (run 'ruff check app/ tests/ --fix')"

echo "  → Black formatting..."
black app/ tests/ --check || echo "  ⚠️  Some formatting issues (run 'black app/ tests/')"

echo "  → isort import sorting..."
isort app/ tests/ --check-only || echo "  ⚠️  Import sorting needed (run 'isort app/ tests/')"

# Run tests
echo ""
echo "🧪 Running tests..."
pytest tests/ -v --cov=app || echo "  ⚠️  Some tests failed"

echo ""
echo "✅ CI/CD setup complete!"
echo ""
echo "Next steps:"
echo "1. Create GitHub repository and push:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/evotrack-backend.git"
echo "   git add ."
echo "   git commit -m 'Initial commit with CI/CD'"
echo "   git push -u origin main"
echo ""
echo "2. Configure GitHub Secrets:"
echo "   → RAILWAY_TOKEN"
echo "   → RAILWAY_APP_URL"
echo ""
echo "3. Setup Railway:"
echo "   → Create project at railway.app"
echo "   → Add PostgreSQL database"
echo "   → Deploy from GitHub"
echo ""
echo "📚 Full documentation: docs/CI_CD.md"
