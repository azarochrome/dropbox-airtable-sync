# Dropbox to Airtable Sync

This project automatically syncs files from Dropbox folders to Airtable records, organizing them by folder categories.

## Features

- 🔄 Automatic daily sync via GitHub Actions
- 📁 Organizes files by Dropbox folder categories
- 🔗 Creates temporary Dropbox links for media previews
- ⚡ Handles rate limiting and retries
- 📊 Comprehensive logging and error handling

## Setup

### 1. Environment Variables

You need to set up the following environment variables in your GitHub repository secrets:

- `DROPBOX_TOKEN`: Your Dropbox API access token
- `AIRTABLE_TOKEN`: Your Airtable API key
- `AIRTABLE_BASE_ID`: Your Airtable base ID
- `AIRTABLE_TABLE_NAME`: Your Airtable table name

### 2. Airtable Table Structure

Your Airtable table should have the following fields:
- `File Name` (Single line text)
- `Dropbox Path` (Single line text)
- `File Type` (Single line text)
- `Category` (Single line text)
- `Date Created` (Date)
- `Media Preview` (Attachment)
- `Media Download` (Attachment)
- `Media URL (optional)` (URL)

### 3. Dropbox Setup

Ensure your Dropbox API token has access to the folders you want to sync.

## Debugging

### Local Testing

Before deploying to GitHub Actions, test your setup locally:

1. Set up environment variables locally:
   ```bash
   export DROPBOX_TOKEN="your_dropbox_token"
   export AIRTABLE_TOKEN="your_airtable_token"
   export AIRTABLE_BASE_ID="your_base_id"
   export AIRTABLE_TABLE_NAME="your_table_name"
   ```

2. Run the test script:
   ```bash
   python test_setup.py
   ```

3. If tests pass, run the sync script:
   ```bash
   python sync.py
   ```

### Common Issues

#### 1. Missing Environment Variables
- **Error**: "Missing required environment variables"
- **Solution**: Ensure all secrets are properly configured in GitHub repository settings

#### 2. Invalid API Tokens
- **Error**: "401 Unauthorized" responses
- **Solution**: Regenerate your Dropbox or Airtable API tokens

#### 3. Invalid Airtable Base/Table
- **Error**: "404 Not Found" from Airtable API
- **Solution**: Verify your base ID and table name are correct

#### 4. Rate Limiting
- **Error**: "429 Too Many Requests"
- **Solution**: The script includes automatic retry logic with exponential backoff

#### 5. Network Issues
- **Error**: Connection timeouts
- **Solution**: Check your internet connection and API endpoint availability

### GitHub Actions Debugging

1. **Check Workflow Logs**: Go to your repository → Actions → Select the failed workflow run
2. **Look for Error Messages**: The improved logging will show detailed error information
3. **Verify Secrets**: Ensure all secrets are set in repository settings
4. **Check API Limits**: Verify your API tokens haven't exceeded rate limits

### Manual Workflow Trigger

You can manually trigger the sync workflow:
1. Go to your repository → Actions
2. Select "Dropbox to Airtable Sync"
3. Click "Run workflow"

## Files

- `sync.py`: Main sync script with improved error handling
- `test_setup.py`: Test script for debugging setup issues
- `.github/workflows/sync.yml`: GitHub Actions workflow configuration
- `requirements.txt`: Python dependencies

## Improvements Made

The original code has been enhanced with:

1. **Better Error Handling**: Comprehensive try-catch blocks and validation
2. **Improved Logging**: Timestamped logs for better debugging
3. **Retry Logic**: Exponential backoff for rate limiting
4. **Environment Validation**: Checks for required variables before starting
5. **API Testing**: Validates connections before running sync
6. **Timeout Handling**: Prevents hanging requests
7. **Better GitHub Actions**: Enhanced workflow with validation steps

## Troubleshooting

If you're still having issues:

1. Run `python test_setup.py` locally to identify the problem
2. Check the GitHub Actions logs for specific error messages
3. Verify your API tokens have the correct permissions
4. Ensure your Airtable table structure matches the expected format
5. Check that your Dropbox folders contain the files you expect to sync 