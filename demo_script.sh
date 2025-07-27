#!/bin/bash

# AI Changelog Generator Demo Script
# This script demonstrates the complete workflow

set -e

echo "🚀 AI Changelog Generator Demo"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY not set. AI features will be limited."
    echo "To enable AI features, run: export OPENAI_API_KEY='your-api-key'"
fi

print_step "Step 1: Setting up demo environment..."

# Create demo project directory
DEMO_DIR="changelog-demo"
if [ -d "$DEMO_DIR" ]; then
    rm -rf "$DEMO_DIR"
fi

mkdir "$DEMO_DIR"
cd "$DEMO_DIR"

# Initialize a demo git repository
git init
echo "# Demo Project" > README.md
git add README.md
git commit -m "Initial commit"

# Create some demo commits
echo "## Features" >> README.md
git add README.md
git commit -m "feat: Add new user authentication system"

echo "- User login" >> README.md
git add README.md
git commit -m "feat: Add user registration flow"

echo "- Password reset" >> README.md
git add README.md
git commit -m "fix: Fix password reset email bug"

echo "- Two-factor auth" >> README.md
git add README.md
git commit -m "feat: Add two-factor authentication support"

echo "## Bug Fixes" >> README.md
git add README.md
git commit -m "fix: Resolve memory leak in background processor"

echo "- Performance improvements" >> README.md
git add README.md
git commit -m "perf: Optimize database query performance"

echo "- Better error handling" >> README.md
git add README.md
git commit -m "chore: Update dependencies and refactor code"

print_success "Demo Git repository created with sample commits"

cd ..

print_step "Step 2: Starting the changelog generator services..."

# Start Docker services
docker-compose up -d

print_success "Services started!"

# Wait for services to be healthy
print_step "Step 3: Waiting for services to be ready..."
sleep 10

# Check if services are running
if ! curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    print_error "Backend service is not responding"
    docker-compose logs backend
    exit 1
fi

if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_error "Frontend service is not responding"
    docker-compose logs frontend
    exit 1
fi

print_success "All services are healthy!"

print_step "Step 4: Installing CLI tool..."

# Install CLI tool
cd cli
pip install -e . > /dev/null 2>&1
cd ..

print_success "CLI tool installed!"

print_step "Step 5: Generating changelog..."

# Change to demo directory
cd "$DEMO_DIR"

# Initialize changelog generator
changelog-gen init

# Generate changelog
print_step "Generating changelog from recent commits..."
changelog-gen generate --repo-path ./changelog-demo --days 7 --output ./changelog.md

print_step "Step 6: Publishing changelog..."

# Version to publish
VERSION="v1.0.0"

# Delete existing changelog with same version if it exists
print_step "Checking for existing changelog with version $VERSION..."

# Use Python to delete the entry (Python is guaranteed to be in the container)
DELETE_SCRIPT="import sqlite3; conn = sqlite3.connect('/app/changelog.db'); conn.execute('DELETE FROM changelogs WHERE version=?', ('$VERSION',)); conn.commit(); conn.close(); print('Deleted existing changelog entries for version $VERSION')"

docker exec changelog-backend python3 -c "$DELETE_SCRIPT" || true
print_success "Cleared any existing changelog with version $VERSION"

# Publish changelog
changelog-gen publish --repo-path ./changelog-demo --version "$VERSION" --title "Initial Release" --file ./changelog.md

cd ..

print_success "Changelog published!"

print_step "Demo completed! 🎉"
echo ""
echo "📋 What was demonstrated:"
echo "  ✅ Docker services setup"
echo "  ✅ CLI tool installation"
echo "  ✅ Git commit analysis"
echo "  ✅ AI-powered changelog generation"
echo "  ✅ Publishing to public website"
echo ""
echo "🌐 Access the services:"
echo "  Frontend (Public Site): http://localhost"
echo "  Backend API: http://localhost:8000"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Try the CLI commands:"
echo "  changelog-gen generate --help"
echo "  changelog-gen list"
echo "  changelog-gen show v1.0.0"
echo ""
echo "🛑 To stop the demo:"
echo "  docker-compose down"
echo "  rm -rf $DEMO_DIR"

# Optional: Open browser
if command -v xdg-open &> /dev/null; then
    print_step "Opening browser..."
    xdg-open http://localhost
elif command -v open &> /dev/null; then
    print_step "Opening browser..."
    open http://localhost
fi