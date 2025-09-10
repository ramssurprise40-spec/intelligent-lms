# Intelligent LMS Deployment Script for Render
# This script prepares and pushes code changes for deployment

Write-Host "🚀 Intelligent LMS Deployment Script" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "render.yaml")) {
    Write-Host "❌ Error: render.yaml not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

# Stage 1: Git operations
Write-Host "📝 Stage 1: Preparing Git commit..." -ForegroundColor Yellow

try {
    git add .
    $commitMessage = Read-Host "Enter commit message (or press Enter for default)"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Update: API integration and production deployment configuration"
    }
    
    git commit -m "$commitMessage"
    Write-Host "✅ Git commit successful" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Git commit failed or no changes to commit" -ForegroundColor Yellow
}

# Stage 2: Push to GitHub
Write-Host "📤 Stage 2: Pushing to GitHub..." -ForegroundColor Yellow

try {
    git push origin main
    Write-Host "✅ Successfully pushed to GitHub" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to push to GitHub. Please check your authentication." -ForegroundColor Red
    Write-Host "You may need to push manually with: git push origin main" -ForegroundColor Yellow
}

# Stage 3: Display deployment instructions
Write-Host "🔧 Stage 3: Next steps for Render deployment" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow

Write-Host ""
Write-Host "1. Go to Render Dashboard: https://dashboard.render.com" -ForegroundColor Cyan
Write-Host "2. Click 'New' -> 'Blueprint'" -ForegroundColor Cyan  
Write-Host "3. Connect your GitHub repo: ramssurprise40-spec/intelligent-lms" -ForegroundColor Cyan
Write-Host "4. Select render.yaml file" -ForegroundColor Cyan
Write-Host "5. Wait for services to deploy" -ForegroundColor Cyan

Write-Host ""
Write-Host "🔑 IMPORTANT: Add these environment variables manually in Render:" -ForegroundColor Red
Write-Host "--------------------------------------------------------------" -ForegroundColor Red
Write-Host "For Backend Service (intelligent-lms-backend):" -ForegroundColor White
Write-Host "   OPENAI_API_KEY=your-openai-api-key" -ForegroundColor Gray
Write-Host ""
Write-Host "For AI Microservices (all 3 services):" -ForegroundColor White  
Write-Host "   OPENAI_API_KEY=your-openai-api-key" -ForegroundColor Gray

Write-Host ""
Write-Host "📚 Full deployment guide available in: DEPLOYMENT_GUIDE.md" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Deployment preparation complete!" -ForegroundColor Green
Write-Host "Your code is ready for deployment on Render." -ForegroundColor Green
