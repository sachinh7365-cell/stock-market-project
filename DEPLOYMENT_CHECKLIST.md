# Render Deployment Checklist

## Pre-Deployment Steps

### Local Testing
- [ ] Run `python app.py` locally and test all features
- [ ] Verify login/registration works
- [ ] Test stock prediction with 2-3 different stocks
- [ ] Check that charts are generated correctly
- [ ] Verify MongoDB connection locally

### Code Cleanup
- [ ] Remove debug print statements (or keep them for now)
- [ ] Review and test error handling
- [ ] Ensure no hardcoded sensitive data in code
- [ ] Check that all required files are present

### Git Repository
- [ ] Initialize git repository: `git init`
- [ ] Add all files: `git add .`
- [ ] Create initial commit: `git commit -m "Initial commit"`
- [ ] Create GitHub repository and push code
- [ ] Verify `.gitignore` prevents sensitive files from being tracked

## Configuration Files Created ✅

- [x] `requirements.txt` - All Python dependencies
- [x] `Procfile` - Render deployment configuration
- [x] `runtime.txt` - Python version specification (3.11.6)
- [x] `.env.example` - Example environment variables template
- [x] `.gitignore` - Files to exclude from version control
- [x] `render.yaml` - Advanced Render configuration
- [x] `DEPLOYMENT.md` - Detailed deployment guide
- [x] `setup.sh` - Linux/Mac setup script
- [x] `setup.bat` - Windows setup script
- [x] `app.py` - Updated with environment variable support

## MongoDB Setup
- [ ] Create MongoDB Atlas account
- [ ] Create M0 (free) cluster
- [ ] Create database user with secure password
- [ ] Add IP whitelist (allow 0.0.0.0/0 for Render)
- [ ] Copy MongoDB connection string (with username and password)
- [ ] Create `stock_prediction` database
- [ ] Optionally create `users` collection or let it auto-create

## Render Deployment
- [ ] Create Render account at render.com
- [ ] Connect GitHub account to Render
- [ ] Create new Web Service from GitHub repository
- [ ] Configure environment variables in Render:
  - `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
  - `MONGO_URI` - Your MongoDB Atlas connection string
  - `DEBUG=False`
- [ ] Click "Create Web Service"
- [ ] Wait for build completion (5-10 minutes, especially first time due to TensorFlow)
- [ ] Verify deployment at your Render URL

## Post-Deployment Testing
- [ ] Access your Render URL in browser
- [ ] Verify login/registration still works
- [ ] Test stock predictions with different tickers
- [ ] Check that charts load properly
- [ ] Review logs for any errors
- [ ] Monitor for the first 24 hours

## Important Notes

### Size Concerns
- TensorFlow is large (~500MB) - first deployment will take time
- Consider using a paid Render plan for faster deployments
- Use `requirements.txt` wisely - only include needed packages

### Performance
- Render Free tier spins down after 15 minutes of inactivity
- First request after spin-down will be slow
- Consider upgrading to Paid plan for production use

### Troubleshooting
- If "Module not found" errors occur, check requirements.txt
- If MongoDB connection fails, verify MONGO_URI and whitelist
- If app crashes, check Render logs for errors
- TensorFlow might fail on Free tier due to memory - consider paid plan

## Environment Variables Needed

```
SECRET_KEY=<generate-a-strong-random-key>
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/stock_prediction?retryWrites=true&w=majority
DEBUG=False
```

## Useful Commands

### Local Development
```bash
# Windows
setup.bat

# Linux/Mac
bash setup.sh

# Then run:
python app.py
```

### Generate SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Check Python Version
```bash
python --version  # Should be 3.9+
```

### Test MongoDB Connection
```bash
python -c "from pymongo import MongoClient; client = MongoClient('<your-mongo-uri>'); print(client.server_info())"
```

## Quick Reference

| Aspect | Value |
|--------|-------|
| Python Version | 3.11.6 |
| Web Server | Gunicorn |
| Database | MongoDB Atlas |
| Hosting | Render |
| Framework | Flask |
| Domain | Will be provided by Render |

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [MongoDB Atlas Documentation](https://docs.mongodb.com/atlas/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://gunicorn.org/)
