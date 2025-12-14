#!/bin/bash

# LifeLink GitHub Deployment Script
echo "🚀 Preparing LifeLink for GitHub deployment..."
echo

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git not initialized. Run: git init"
    exit 1
fi

# Check for required files
if [ ! -f ".env.example" ]; then
    echo "❌ .env.example not found"
    exit 1
fi

if [ ! -f "README.md" ]; then
    echo "❌ README.md not found"
    exit 1
fi

echo "✅ Repository structure looks good!"
echo

# Show current status
echo "📋 Current git status:"
git status --short
echo

# Add all files
echo "📦 Adding files to git..."
git add .

# Show what will be committed
echo
echo "📋 Files to be committed:"
git status --short
echo

# Commit
echo "💾 Creating commit..."
read -p "Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="🏥 LifeLink: LangGraph multi-agent emergency coordination system"
fi

git commit -m "$commit_msg"

echo
echo "✅ Commit created successfully!"
echo

# Push to GitHub
echo "🔗 Pushing to GitHub repository..."
echo "Repository: https://github.com/YugmPatel/LifeLink.git"
echo

# Check if remote exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ Remote 'origin' already exists"
else
    echo "🔗 Adding remote origin..."
    git remote add origin https://github.com/YugmPatel/LifeLink.git
fi

# Set main branch and push
echo "🚀 Pushing to GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Successfully pushed to GitHub!"
    echo "🔗 View your repository: https://github.com/YugmPatel/LifeLink"
else
    echo
    echo "❌ Push failed. You may need to:"
    echo "1. Check your GitHub authentication"
    echo "2. Make sure the repository exists on GitHub"
    echo "3. Run: git push -u origin main --force (if needed)"
fi