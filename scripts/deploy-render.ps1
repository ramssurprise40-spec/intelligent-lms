# Render Deployment Script for Intelligent LMS
# This script helps deploy the Intelligent LMS to Render.com

param(
    [string]$Action = "deploy",
    [string]$Environment = "production",
    [switch]$Verbose
)

# Set error handling
$ErrorActionPreference = "Stop"

Write-Host "🚀 Intelligent LMS Render Deployment Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Test-Prerequisites {
    Write-Log "Checking prerequisites..." "INFO"
    
    # Check if render CLI is installed
    try {
        $renderVersion = render --version 2>$null
        Write-Log "Render CLI found: $renderVersion" "SUCCESS"
    }
    catch {
        Write-Log "Render CLI not found. Please install it from https://render.com/docs/cli" "ERROR"
        exit 1
    }
    
    # Check if user is logged in
    try {
        $user = render whoami 2>$null
        Write-Log "Logged in as: $user" "SUCCESS"
    }
    catch {
        Write-Log "Not logged into Render. Please run 'render login'" "ERROR"
        exit 1
    }
    
    # Check if we're in the right directory
    if (!(Test-Path "render.yml")) {
        Write-Log "render.yml not found. Please run this script from the project root." "ERROR"
        exit 1
    }
    
    Write-Log "All prerequisites met!" "SUCCESS"
}

function Deploy-Services {
    Write-Log "Starting deployment to Render..." "INFO"
    
    try {
        # Deploy using render.yml
        Write-Log "Deploying services from render.yml..." "INFO"
        render deploy --config render.yml
        
        Write-Log "Deployment initiated successfully!" "SUCCESS"
        Write-Log "You can monitor the deployment at https://dashboard.render.com/" "INFO"
        
        # Show service URLs
        Write-Log "Your services will be available at:" "INFO"
        Write-Host "  🌐 Main Backend: https://intelligent-lms-backend.onrender.com" -ForegroundColor Green
        Write-Host "  🤖 AI Content: https://ai-content-service.onrender.com" -ForegroundColor Green
        Write-Host "  📝 AI Assessment: https://ai-assessment-service.onrender.com" -ForegroundColor Green
        Write-Host "  🔍 AI Search: https://ai-search-service.onrender.com" -ForegroundColor Green
        Write-Host "  💬 AI Communication: https://ai-communication-service.onrender.com" -ForegroundColor Green
        Write-Host "  🌸 Flower Monitor: https://flower-monitor.onrender.com" -ForegroundColor Green
        Write-Host "  ⚛️  Frontend: https://intelligent-lms-frontend.onrender.com" -ForegroundColor Green
        
    }
    catch {
        Write-Log "Deployment failed: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}

function Setup-Environment-Variables {
    Write-Log "Setting up environment variables..." "INFO"
    
    $envVars = @{
        "SECRET_KEY" = "your-secret-key-here"
        "OPENAI_API_KEY" = "your-openai-api-key"
        "EMAIL_HOST" = "smtp.gmail.com"
        "EMAIL_HOST_USER" = "your-email@gmail.com"
        "EMAIL_HOST_PASSWORD" = "your-app-password"
        "ANTHROPIC_API_KEY" = "your-anthropic-api-key"
        "FLOWER_BASIC_AUTH" = "admin:secure_password_2024"
    }
    
    Write-Log "Please set the following environment variables in Render dashboard:" "WARN"
    foreach ($var in $envVars.GetEnumerator()) {
        Write-Host "  $($var.Key): $($var.Value)" -ForegroundColor Yellow
    }
    
    Write-Log "You can set these at https://dashboard.render.com/ under each service's Environment tab" "INFO"
}

function Show-Post-Deployment-Steps {
    Write-Log "Post-deployment steps:" "INFO"
    
    Write-Host "1. 📧 Configure Email Settings:" -ForegroundColor Cyan
    Write-Host "   - Set up SMTP credentials in environment variables"
    Write-Host "   - Test email functionality"
    
    Write-Host "2. 🤖 Configure AI Services:" -ForegroundColor Cyan
    Write-Host "   - Add OpenAI API key to environment variables"
    Write-Host "   - Test AI content generation"
    Write-Host "   - Verify RAG search functionality"
    
    Write-Host "3. 📊 Set up Monitoring:" -ForegroundColor Cyan
    Write-Host "   - Access Flower dashboard for task monitoring"
    Write-Host "   - Check Redis Insight for cache monitoring"
    Write-Host "   - Review application logs"
    
    Write-Host "4. 🔒 Security Configuration:" -ForegroundColor Cyan
    Write-Host "   - Update ALLOWED_HOSTS in Django settings"
    Write-Host "   - Configure CORS settings"
    Write-Host "   - Set up SSL certificates (handled by Render)"
    
    Write-Host "5. 📈 Performance Optimization:" -ForegroundColor Cyan
    Write-Host "   - Monitor resource usage"
    Write-Host "   - Scale services as needed"
    Write-Host "   - Configure auto-scaling policies"
}

function Show-Troubleshooting-Guide {
    Write-Log "Troubleshooting Guide:" "INFO"
    
    Write-Host "Common Issues and Solutions:" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "🔴 Build Failures:" -ForegroundColor Red
    Write-Host "   - Check Dockerfile syntax"
    Write-Host "   - Verify requirements.txt includes all dependencies"
    Write-Host "   - Check build logs in Render dashboard"
    Write-Host ""
    
    Write-Host "🔴 Database Connection Issues:" -ForegroundColor Red
    Write-Host "   - Ensure DATABASE_URL is correctly set"
    Write-Host "   - Run migrations after deployment"
    Write-Host "   - Check PostgreSQL service status"
    Write-Host ""
    
    Write-Host "🔴 Redis Connection Issues:" -ForegroundColor Red
    Write-Host "   - Verify REDIS_URL environment variable"
    Write-Host "   - Check Redis service status"
    Write-Host "   - Review Celery worker logs"
    Write-Host ""
    
    Write-Host "🔴 AI Service Issues:" -ForegroundColor Red
    Write-Host "   - Verify API keys are set correctly"
    Write-Host "   - Check microservice health endpoints"
    Write-Host "   - Review service-specific logs"
    Write-Host ""
    
    Write-Host "📞 Get Help:" -ForegroundColor Cyan
    Write-Host "   - Render Documentation: https://render.com/docs"
    Write-Host "   - Render Support: https://render.com/support"
    Write-Host "   - Community: https://community.render.com/"
}

# Main execution
switch ($Action.ToLower()) {
    "deploy" {
        Test-Prerequisites
        Deploy-Services
        Setup-Environment-Variables
        Show-Post-Deployment-Steps
    }
    "check" {
        Test-Prerequisites
        Write-Log "All checks passed! Ready for deployment." "SUCCESS"
    }
    "env" {
        Setup-Environment-Variables
    }
    "troubleshoot" {
        Show-Troubleshooting-Guide
    }
    "help" {
        Write-Host "Usage: .\deploy-render.ps1 [ACTION]" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Yellow
        Write-Host "  deploy       - Deploy all services to Render (default)"
        Write-Host "  check        - Check prerequisites only"
        Write-Host "  env          - Show environment variables to configure"
        Write-Host "  troubleshoot - Show troubleshooting guide"
        Write-Host "  help         - Show this help message"
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Green
        Write-Host "  .\deploy-render.ps1"
        Write-Host "  .\deploy-render.ps1 -Action check"
        Write-Host "  .\deploy-render.ps1 -Action env"
    }
    default {
        Write-Log "Unknown action: $Action. Use 'help' for available actions." "ERROR"
        exit 1
    }
}

Write-Log "Script completed successfully!" "SUCCESS"
