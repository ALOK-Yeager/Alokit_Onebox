# Render.com Deployment Guide

This guide explains how to deploy the Onebox Aggregator to Render.com using the provided `render.yaml` configuration.

## Prerequisites

1. **Render.com Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code must be in a GitHub repository (already done: `ALOK-Yeager/Alokit_Onebox`)
3. **External Services**: Set up the required external services before deployment

## Required External Services Setup

### 1. Elasticsearch (Elastic Cloud)

1. Sign up at [Elastic Cloud](https://cloud.elastic.co/)
2. Create a new deployment
3. Note down:
   - Deployment URL (format: `https://[deployment-name].[region].gcp.elastic-cloud.com:9243`)
   - Username: `elastic`
   - Password: (provided during setup)

### 2. Email Provider Setup

For Gmail:
1. Enable 2-Factor Authentication
2. Generate an App Password at [Google Account Settings](https://myaccount.google.com/apppasswords)
3. Use `imap.gmail.com` as the server

For Outlook:
1. Use `outlook.office365.com` as the server
2. Use your regular email password or create an app password

## Deployment Steps

### Step 1: Update render.yaml

Before deploying, update the following placeholders in `render.yaml`:

```yaml
# Update Elasticsearch configuration
ELASTICSEARCH_URL: https://[YOUR_DEPLOYMENT_NAME].[REGION].gcp.elastic-cloud.com:9243
ELASTICSEARCH_HOST: [YOUR_DEPLOYMENT_NAME].[REGION].gcp.elastic-cloud.com

# Update email configuration
IMAP_SERVER: imap.gmail.com  # or your provider
IMAP_USER: your.email@gmail.com

# Update frontend routes (after deployment)
destination: https://api-gateway-[YOUR_RENDER_SERVICE_NAME].onrender.com
```

### Step 2: Deploy to Render

1. **Connect Repository**:
   - Go to Render Dashboard
   - Click "New" → "Blueprint"
   - Connect your GitHub repository: `ALOK-Yeager/Alokit_Onebox`
   - Select the `render.yaml` file

2. **Configure Environment Variables**:
   - Render will automatically create environment variable groups
   - Set sensitive values manually in the dashboard:
     - `ELASTICSEARCH_PASSWORD`
     - `IMAP_PASSWORD`
     - `GROQ_API_KEY` (optional)
     - `OPENAI_API_KEY` (optional)

3. **Deploy Services**:
   - Render will deploy all services defined in `render.yaml`
   - Services will be deployed in dependency order
   - Monitor deployment logs for any issues

### Step 3: Post-Deployment Configuration

1. **Update Frontend Routes**:
   - Once the API Gateway is deployed, note its URL
   - Update the frontend routes in `render.yaml`
   - Redeploy the frontend service

2. **Test the Application**:
   - Access your frontend URL
   - Test email search functionality
   - Verify all services are communicating properly

## Service URLs

After deployment, your services will be available at:

- **Frontend**: `https://frontend-[hash].onrender.com`
- **API Gateway**: `https://api-gateway-[hash].onrender.com`
- **Node Backend**: `https://node-backend-[hash].onrender.com`
- **API Server**: `https://api-server-[hash].onrender.com`
- **VectorDB Service**: `https://vectordb-service-[hash].onrender.com`

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ELASTICSEARCH_URL` | Yes | Elastic Cloud URL | `https://my-deployment.us-east1.gcp.elastic-cloud.com:9243` |
| `ELASTICSEARCH_PASSWORD` | Yes | Elastic password | Set in Render dashboard |
| `IMAP_SERVER` | Yes | Email server | `imap.gmail.com` |
| `IMAP_USER` | Yes | Your email | `you@gmail.com` |
| `IMAP_PASSWORD` | Yes | Email password | Set in Render dashboard |
| `GROQ_API_KEY` | Optional | AI service key | Set in Render dashboard |

## Troubleshooting

### Common Issues

1. **Service Startup Failures**:
   - Check environment variables are set correctly
   - Verify external services (Elasticsearch) are accessible
   - Review service logs in Render dashboard

2. **Email Connection Issues**:
   - Verify IMAP credentials
   - Check if 2FA/App Passwords are required
   - Ensure IMAP is enabled on your email account

3. **Frontend API Calls Failing**:
   - Verify API Gateway URL in frontend routes
   - Check CORS configuration
   - Ensure all backend services are running

### Monitoring

- Use Render's built-in monitoring dashboard
- Set up log aggregation for debugging
- Configure health checks for automatic restart

## Cost Estimation

Render.com pricing (approximate):
- **Free Tier**: Limited resources, services sleep after inactivity
- **Starter Plan**: $7/month per service
- **Pro Plan**: $25/month per service with better resources

For this application (5 services), estimate $35-125/month depending on usage and plan selection.

## Security Best Practices

1. **Never commit sensitive data** to your repository
2. **Use Render's environment variables** for all secrets
3. **Enable HTTPS** for all services (automatic with Render)
4. **Regularly rotate API keys** and passwords
5. **Monitor access logs** for suspicious activity

## Support

- [Render Documentation](https://render.com/docs)
- [Elastic Cloud Support](https://cloud.elastic.co/support)
- Project Issues: [GitHub Issues](https://github.com/ALOK-Yeager/Alokit_Onebox/issues)