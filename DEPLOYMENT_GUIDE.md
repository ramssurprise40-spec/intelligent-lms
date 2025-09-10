# Intelligent LMS - Production Deployment Guide

This guide covers deploying the Intelligent LMS to Render.com using the blueprint configuration.

## Prerequisites

1. GitHub repository with the latest code
2. Render.com account (free tier available)
3. OpenAI API key for AI features
4. (Optional) Email service credentials for notifications

## Deployment Steps

### 1. Deploy Infrastructure using Blueprint

1. **Connect Repository to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository: `https://github.com/ramssurprise40-spec/intelligent-lms`
   - Select the `render.yaml` file

2. **Blueprint Services Overview:**
   The blueprint will create:
   - PostgreSQL database (`intelligent-lms-postgres`)
   - Redis cache (`intelligent-lms-redis`)
   - Django backend web service (`intelligent-lms-backend`)
   - Celery worker service (`intelligent-lms-worker`)
   - AI Search microservice (`intelligent-lms-ai-search`)
   - AI Content microservice (`intelligent-lms-ai-content`)
   - AI Assessment microservice (`intelligent-lms-ai-assessment`)

### 2. Configure Environment Variables

After the blueprint creates the services, you need to manually add sensitive environment variables:

#### For Backend Service (`intelligent-lms-backend`):

1. Go to the backend service in your Render dashboard
2. Navigate to "Environment" tab
3. Add the following environment variables:

```
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
```

#### For AI Microservices:

Add to each AI microservice (`ai-search`, `ai-content`, `ai-assessment`):

```
OPENAI_API_KEY=your-openai-api-key-here
```

#### For Email Services (Optional):

Add to backend service if you want email notifications:

```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

### 3. Deploy Frontend (Separate Static Site)

1. **Create a new Static Site:**
   - In Render dashboard, click "New" → "Static Site"
   - Connect the same GitHub repository
   - Set build command: `cd frontend && npm ci && npm run build`
   - Set publish directory: `frontend/dist`

2. **Configure Frontend Environment Variables:**
   ```
   VITE_API_URL=https://intelligent-lms-backend.onrender.com/api/v1
   VITE_AI_SEARCH_URL=https://intelligent-lms-ai-search.onrender.com
   VITE_AI_CONTENT_URL=https://intelligent-lms-ai-content.onrender.com
   VITE_AI_ASSESSMENT_URL=https://intelligent-lms-ai-assessment.onrender.com
   ```

3. **Update CORS Settings:**
   - Go to backend service environment variables
   - Update `CORS_ALLOWED_ORIGINS` with your frontend URL:
   ```
   CORS_ALLOWED_ORIGINS=https://your-frontend-url.onrender.com
   ```

### 4. Initial Setup and Verification

1. **Wait for All Services to Deploy:**
   - Monitor the deployment logs for each service
   - Ensure all services show "Live" status

2. **Create Superuser Account:**
   - Go to backend service → "Shell"
   - Run: `python manage.py createsuperuser`
   - Follow the prompts to create an admin account

3. **Test the Application:**
   - Visit your frontend URL
   - Try registering a new student account
   - Test login functionality
   - Verify AI features are working

### 5. Monitoring and Maintenance

#### Health Checks:
- Backend: `https://your-backend.onrender.com/api/docs/`
- AI Search: `https://your-ai-search.onrender.com/docs`
- AI Content: `https://your-ai-content.onrender.com/docs`
- AI Assessment: `https://your-ai-assessment.onrender.com/docs`

#### Logs:
- Monitor service logs in Render dashboard
- Check for any deployment or runtime errors
- Set up alerts for critical issues

#### Scaling:
- Free tier has limitations (750 compute hours/month)
- Consider upgrading to paid plans for production use
- Monitor performance and resource usage

## Troubleshooting

### Common Issues:

1. **Services Won't Start:**
   - Check build logs for dependency issues
   - Verify all environment variables are set
   - Ensure requirements.txt is up to date

2. **Database Connection Errors:**
   - Verify DATABASE_URL is automatically set by Render
   - Check if migrations ran successfully
   - Ensure PostgreSQL service is running

3. **Redis Connection Issues:**
   - Verify REDIS_URL is set correctly
   - Check if Redis service is running
   - Confirm Celery worker can connect

4. **CORS Errors:**
   - Update CORS_ALLOWED_ORIGINS with correct frontend URL
   - Ensure both HTTP and HTTPS are handled appropriately
   - Check that CORS middleware is properly configured

5. **AI Features Not Working:**
   - Verify OPENAI_API_KEY is set for all relevant services
   - Check OpenAI API quota and billing
   - Monitor AI service logs for errors

### Performance Optimization:

1. **Database:**
   - Monitor query performance
   - Add database indexes as needed
   - Consider connection pooling for high traffic

2. **Caching:**
   - Verify Redis is working correctly
   - Monitor cache hit rates
   - Implement additional caching strategies

3. **Static Files:**
   - Ensure collectstatic runs during deployment
   - Consider using a CDN for static assets
   - Optimize image and asset sizes

## Security Considerations

1. **Environment Variables:**
   - Never commit sensitive data to Git
   - Use Render's environment variable encryption
   - Rotate secrets regularly

2. **HTTPS:**
   - Render provides SSL certificates automatically
   - Ensure all external links use HTTPS
   - Configure secure cookie settings

3. **Authentication:**
   - Enable MFA for admin accounts
   - Set strong password policies
   - Monitor login attempts and security events

## Backup and Recovery

1. **Database Backups:**
   - Render provides automated PostgreSQL backups
   - Consider additional backup strategies for critical data
   - Test restoration procedures regularly

2. **Code Backups:**
   - Use Git for version control
   - Tag releases for easy rollbacks
   - Maintain separate staging environment

## Support Resources

- [Render Documentation](https://render.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- Project GitHub Issues for technical support

---

**Note:** This deployment setup uses free tier services which have limitations. For production use with high traffic, consider upgrading to paid plans and implementing additional monitoring and scaling strategies.
