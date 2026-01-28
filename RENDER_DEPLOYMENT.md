# Render Deployment Guide for Skilledge

## Prerequisites
1. MongoDB Atlas account with a cluster created
2. Render account

## Step 1: Configure MongoDB Atlas

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Navigate to your cluster → **Network Access**
3. Click **"Add IP Address"**
4. Select **"Allow Access from Anywhere"** (0.0.0.0/0) for Render deployment
5. Click **Confirm**

## Step 2: Get MongoDB Connection String

1. In MongoDB Atlas, click **"Connect"** on your cluster
2. Choose **"Connect your application"**
3. Copy the connection string (should look like):
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<password>` with your actual database user password

Your connection string:
```
mongodb+srv://dheerajabhishek111_db_user:qBfhsjZKsKfzdhj2@cluster0.c4pnwwj.mongodb.net/?appName=Cluster0
```

## Step 3: Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: skilledge (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Instance Type**: Free

## Step 4: Set Environment Variables in Render

1. In your Render web service settings, go to **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Add the following:

   **Key**: `MONGODB_URI`  
   **Value**: `mongodb+srv://dheerajabhishek111_db_user:qBfhsjZKsKfzdhj2@cluster0.c4pnwwj.mongodb.net/?appName=Cluster0`

4. Click **"Save Changes"**

## Step 5: Verify Deployment

1. Wait for Render to build and deploy (2-3 minutes)
2. Click on the provided URL
3. Check the logs in Render dashboard for:
   - `✓ Using MongoDB URI from environment variable`
   - `✅ MongoDB connected successfully!`

## Troubleshooting

### If MongoDB connection fails:

1. **Check Network Access**: Ensure 0.0.0.0/0 is whitelisted in MongoDB Atlas
2. **Check Credentials**: Verify username and password in connection string
3. **Check Environment Variable**: Ensure `MONGODB_URI` is set correctly in Render
4. **View Logs**: Check Render logs for detailed error messages

### Common Issues:

- **"Authentication failed"**: Password is incorrect or user doesn't exist
- **"Connection timeout"**: IP address not whitelisted in MongoDB Atlas
- **"Unable to parse"**: Connection string format is incorrect

## Testing Locally

To test locally with the same MongoDB:

1. Edit `.streamlit/secrets.toml` (already configured)
2. Run: `streamlit run AI-Resume-Analyzer/App/App.py`
3. Check console for connection status

## Security Notes

- ⚠️ Never commit `.streamlit/secrets.toml` to GitHub (already in .gitignore)
- ✅ Use environment variables on Render (secure)
- ✅ MongoDB credentials are encrypted in transit
- ⚠️ Consider rotating database password periodically
