# Blog Automation Setup Guide

This guide will help you set up a Google Form so your girlfriend can submit blogs without touching any code!

## How It Works

1. **She fills out a simple Google Form** with:
   - Blog title
   - Tags (comma-separated)
   - PDF file upload
   - Image upload

2. **Google Apps Script** automatically:
   - Takes the form submission
   - Uploads files to your GitHub repo's `pending-blogs/` folder
   - Creates a metadata.json with the form data

3. **GitHub Actions** automatically:
   - Detects new files in `pending-blogs/`
   - Extracts text from the PDF
   - Generates the blog HTML
   - Updates blogs.html and blog-data.json
   - Commits and deploys to GitHub Pages

---

## Step 1: Create the Google Form

1. Go to [Google Forms](https://forms.google.com)
2. Create a new form called "New Blog Post"
3. Add these fields:

| Question | Type | Required |
|----------|------|----------|
| Blog Title | Short answer | Yes |
| Tags (comma-separated) | Short answer | Yes |
| Blog PDF | File upload | Yes |
| Featured Image | File upload | Yes |

4. In File upload settings:
   - Allow only specific file types
   - PDF for the blog file
   - Images (jpg, png) for the featured image
   - Max file size: 10MB each

5. Click the gear icon → "Responses" tab → Enable "Collect email addresses" (optional, for tracking)

---

## Step 2: Create a GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name it: `blog-automation`
4. Select scopes:
   - `repo` (full control of private repositories)
5. Click "Generate token"
6. **COPY THE TOKEN NOW** - you won't see it again!

---

## Step 3: Set Up Google Apps Script

1. Open your Google Form
2. Click the three dots menu → Script editor
3. Delete all the default code and paste this:

```javascript
// Configuration - UPDATE THESE VALUES
const GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN_HERE';  // From Step 2
const GITHUB_REPO = 'YOUR_USERNAME/YOUR_REPO';   // e.g., 'robde/mantooth-blog'
const GITHUB_BRANCH = 'main';

function onFormSubmit(e) {
  try {
    const responses = e.response.getItemResponses();

    let title = '';
    let tags = '';
    let pdfFile = null;
    let imageFile = null;

    // Extract form responses
    responses.forEach(response => {
      const question = response.getItem().getTitle().toLowerCase();
      const answer = response.getResponse();

      if (question.includes('title')) {
        title = answer;
      } else if (question.includes('tag')) {
        tags = answer;
      } else if (question.includes('pdf')) {
        pdfFile = DriveApp.getFileById(answer[0]);
      } else if (question.includes('image')) {
        imageFile = DriveApp.getFileById(answer[0]);
      }
    });

    if (!title || !pdfFile || !imageFile) {
      console.error('Missing required fields');
      return;
    }

    // Generate clean filename
    const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');

    // Upload PDF
    const pdfBlob = pdfFile.getBlob();
    uploadToGitHub(`pending-blogs/${slug}.pdf`, pdfBlob.getBytes(), `Add blog PDF: ${title}`);

    // Upload Image
    const imageBlob = imageFile.getBlob();
    const imageExt = imageFile.getName().split('.').pop().toLowerCase();
    uploadToGitHub(`pending-blogs/${slug}.${imageExt}`, imageBlob.getBytes(), `Add blog image: ${title}`);

    // Upload metadata
    const metadata = {
      title: title,
      tags: tags,
      date: new Date().toISOString().split('T')[0],
      submittedAt: new Date().toISOString()
    };
    const metadataBytes = Utilities.newBlob(JSON.stringify(metadata, null, 2)).getBytes();
    uploadToGitHub('pending-blogs/metadata.json', metadataBytes, `Add blog metadata: ${title}`);

    console.log(`Successfully submitted: ${title}`);

    // Clean up uploaded files from Drive (optional)
    // pdfFile.setTrashed(true);
    // imageFile.setTrashed(true);

  } catch (error) {
    console.error('Error processing form:', error);
  }
}

function uploadToGitHub(path, contentBytes, message) {
  const base64Content = Utilities.base64Encode(contentBytes);

  // Check if file exists (to get SHA for update)
  let sha = null;
  try {
    const existingResponse = UrlFetchApp.fetch(
      `https://api.github.com/repos/${GITHUB_REPO}/contents/${path}?ref=${GITHUB_BRANCH}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        },
        muteHttpExceptions: true
      }
    );
    if (existingResponse.getResponseCode() === 200) {
      sha = JSON.parse(existingResponse.getContentText()).sha;
    }
  } catch (e) {
    // File doesn't exist, that's fine
  }

  const payload = {
    message: message,
    content: base64Content,
    branch: GITHUB_BRANCH
  };

  if (sha) {
    payload.sha = sha;
  }

  const response = UrlFetchApp.fetch(
    `https://api.github.com/repos/${GITHUB_REPO}/contents/${path}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(payload)
    }
  );

  if (response.getResponseCode() !== 200 && response.getResponseCode() !== 201) {
    throw new Error(`GitHub upload failed: ${response.getContentText()}`);
  }

  return JSON.parse(response.getContentText());
}

// Test function - run this manually to verify setup
function testConnection() {
  try {
    const response = UrlFetchApp.fetch(
      `https://api.github.com/repos/${GITHUB_REPO}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    console.log('Connection successful! Repo:', JSON.parse(response.getContentText()).full_name);
  } catch (error) {
    console.error('Connection failed:', error);
  }
}
```

4. **UPDATE THE CONFIG VALUES** at the top:
   - Replace `YOUR_GITHUB_TOKEN_HERE` with your token from Step 2
   - Replace `YOUR_USERNAME/YOUR_REPO` with your actual repo (e.g., `robde/mantooth`)

5. Save the script (Ctrl+S)

6. Run the `testConnection` function to verify it works:
   - Click the dropdown next to "Run" and select `testConnection`
   - Click Run
   - Authorize the script when prompted
   - Check the execution log for "Connection successful!"

---

## Step 4: Set Up the Form Trigger

1. In the Apps Script editor, click the clock icon (Triggers) in the left sidebar
2. Click "+ Add Trigger"
3. Configure:
   - Function: `onFormSubmit`
   - Event source: From form
   - Event type: On form submit
4. Click Save
5. Authorize when prompted

---

## Step 5: Test It!

1. Open your Google Form
2. Fill it out with a test blog:
   - Title: "Test Blog Post"
   - Tags: "test, automation"
   - Upload a sample PDF
   - Upload a sample image
3. Submit the form
4. Check your GitHub repo - you should see new files in `pending-blogs/`
5. GitHub Actions will automatically run and process the blog!

---

## For Your Girlfriend

Share this simple link with her (replace with your actual form URL):

**"To post a new blog, just fill out this form: [Your Form Link]"**

That's it! She fills out the form, uploads her files, and the blog appears on the website automatically.

---

## Troubleshooting

### Form submission doesn't trigger
- Check the Triggers in Apps Script editor
- Look at Executions log for errors

### GitHub upload fails
- Verify your token has `repo` permissions
- Check the token hasn't expired
- Verify the repo name is correct

### Blog doesn't appear on site
- Check GitHub Actions tab for workflow runs
- Look at the workflow logs for errors
- Make sure the PDF has extractable text (not scanned images)

---

## Alternative: Manual GitHub Upload

If you prefer not to use Google Forms, she can also:

1. Go to your GitHub repo online
2. Navigate to `pending-blogs/` folder
3. Click "Add file" → "Upload files"
4. Upload the PDF, image, and a `metadata.json` file:

```json
{
  "title": "My Blog Title",
  "tags": "travel, adventure, life",
  "date": "2025-01-03"
}
```

The GitHub Action will process it automatically!
