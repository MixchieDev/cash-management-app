#!/bin/bash
#═══════════════════════════════════════════════════════════════════
# PARALLEL CREW SETUP SCRIPT
# Creates 3 Git worktrees for Development, Testing, and Debugging crews
#═══════════════════════════════════════════════════════════════════

echo "🚀 Setting up Parallel Crew System..."
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ ERROR: Not in a Git repository. Run from your project root."
    exit 1
fi

# Create .trees directory
mkdir -p .trees

# Remove existing worktrees if they exist (clean setup)
git worktree remove .trees/development 2>/dev/null
git worktree remove .trees/testing 2>/dev/null
git worktree remove .trees/debugging 2>/dev/null

# Create worktrees
echo "Creating Development worktree..."
git worktree add .trees/development -b crew-development 2>/dev/null || git worktree add .trees/development crew-development
echo "✅ Development worktree created"

echo "Creating Testing worktree..."
git worktree add .trees/testing -b crew-testing 2>/dev/null || git worktree add .trees/testing crew-testing
echo "✅ Testing worktree created"

echo "Creating Debugging worktree..."
git worktree add .trees/debugging -b crew-debugging 2>/dev/null || git worktree add .trees/debugging crew-debugging
echo "✅ Debugging worktree created"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ PARALLEL CREW SYSTEM READY!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Worktrees created:"
echo "  📁 .trees/development → Development Crew"
echo "  📁 .trees/testing     → Testing Crew"
echo "  📁 .trees/debugging   → Debugging Crew"
echo ""
echo "Next steps:"
echo "  1. Open 3 terminal windows"
echo "  2. Terminal 1: cd .trees/development && claude"
echo "  3. Terminal 2: cd .trees/testing && claude"
echo "  4. Terminal 3: cd .trees/debugging && claude"
echo "  5. Paste the crew prompts into each"
echo ""
