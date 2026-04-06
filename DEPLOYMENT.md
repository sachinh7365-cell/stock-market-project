# Deployment Guide - Render

This document provides instructions for deploying the Stock Market Prediction application to Render.

## Prerequisites

1. **Render Account**: Create a free account at [render.com](https://render.com)
2. **GitHub Repository**: Push your code to GitHub (required for Render deployment)
3. **MongoDB Atlas Account**: Set up a free M0 cluster at [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)

## Deployment Steps

### 1. Set Up MongoDB Atlas

1. Go to [MongoDB Atlas](https://mongodb.com/cloud/atlas)
2. Create a free M0 cluster
3. Create a database user with a secure password
4. Whitelist Render's IP address (or use 0.0.0.0/0 for testing)
5. Get your connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/stock_prediction?retryWrites=true&w=majority`)

### 2. Push Code to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 3. Deploy to Render

1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Fill in the deployment details:
   - **Name**: `stock-market-prediction` (or your preferred name)
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or paid if preferred)

### 4. Set Environment Variables

In the Render dashboard, add these environment variables:

```
SECRET_KEY=<generate-a-long-random-string-here>
MONGO_URI=<your-mongodb-atlas-connection-string>
DEBUG=False
```

To generate a SECRET_KEY, you can use:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Deploy

Click "Create Web Service" and Render will automatically:
- Clone your repository
- Install dependencies from requirements.txt
- Start the application with the gunicorn server
- Deploy it to a public URL

Your app will be available at: `https://<your-app-name>.onrender.com`

## Important Notes

- **First Deploy Warning**: TensorFlow installation can take 5-10 minutes on first deploy. Be patient!
- **Free Tier**: The free tier on Render spins down after 15 minutes of inactivity. Paid plans have better uptime.
- **Storage**: Render instances don't have persistent storage. Any generated charts will only exist during the request.
- **Model Loading**: The `stock_dl_model.h5` file is loaded on startup. Ensure it's in your repository.

## Updating the Application

After pushing changes to GitHub:
1. Go to your Render service dashboard
2. Click "Manual Deploy" → "Deploy latest commit"
3. Or enable "Auto-Deploy from GitHub" for automatic deployments

## Monitoring and Logs

View your application logs in the Render dashboard:
1. Go to your web service
2. Click "Logs" tab to see real-time output

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MONGO_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/db` |
| `DEBUG` | Flask debug mode | `False` (for production) |
| `PORT` | Server port (set by Render) | `5000` |

## Troubleshooting

### "Module not found" errors
- Ensure all dependencies are in `requirements.txt`
- Check that the versions are compatible

### MongoDB connection issues
- Verify the connection string is correct
- Ensure the IP address whitelist includes Render's servers
- Check username and password are URL-encoded if they contain special characters

### Application crashes
- Check the Render logs for error messages
- Ensure `gunicorn` is in requirements.txt
- Verify all environment variables are set

## Security Best Practices

1. **Never commit `.env`** - Always use environment variables in Render dashboard
2. **Use strong SECRET_KEY** - Generate a cryptographically secure key
3. **MongoDB Credentials** - Use a dedicated user with limited permissions
4. **HTTPS** - Render automatically provides HTTPS for your app
5. **IP Whitelisting** - MongoDB Atlas can restrict connections to specific IPs

## Cost Considerations

- **Render Free Tier**: Limited resources, spins down after 15 min inactivity
- **Render Paid**: Better performance and always-on
- **MongoDB Atlas Free Tier**: 512MB storage, sufficient for this project

## Support

For Render-specific issues: [Render Docs](https://render.com/docs)
For MongoDB questions: [MongoDB Atlas Docs](https://docs.mongodb.com/atlas/)
