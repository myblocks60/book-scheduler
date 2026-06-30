
# RAG Integration Guide

## Overview
This guide explains how to integrate your application with the RAG (Retrieval-Augmented Generation) server to upload and index documents.

---

## RAG Server Endpoints
All endpoints are available at `https://dev.myblocks.in:12095/api/rag/`

---

### 1. Get Categories Endpoint
Fetches available categories (folders) for a user.
- **Method**: POST
- **URL**: `https://dev.myblocks.in:12095/api/rag/categories`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "username": "1559",
    "userid": "1559"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "username": "RAG",
    "userid": "1559",
    "categories": [
      {
        "name": "Career book",
        "owner": "1559",
        "source": "owned",
        "permissions": { "business": false, "basic": false },
        "personaId": null,
        "complianceProfileId": null
      }
    ]
  }
  ```

---

### 2. Document Upload Endpoint
Uploads raw documents (PDF, TXT, DOCX) to a selected category.
- **Method**: POST
- **URL**: `https://dev.myblocks.in:12095/api/rag/upload`
- **Headers**: `Content-Type: multipart/form-data`
- **Form-Data Body**:
  - `username`: User ID (e.g., "1559")
  - `userid`: User ID (e.g., "1559")
  - `category`: Target category name (e.g., "Career book")
  - `files`: File objects (one or multiple)
- **Response**:
  ```json
  {
    "message": "Successfully uploaded 1 files.",
    "files": ["file1.pdf"]
  }
  ```

---

### 3. Update Index Endpoint
Builds/updates the AI index for a category to make documents queryable.
- **Method**: POST
- **URL**: `https://dev.myblocks.in:12095/api/rag/update-index`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "username": "1559",
    "userid": "1559",
    "category": "Career book"
  }
  ```

---

## Node.js Example Implementation

Here's a complete example using Express as a proxy (to avoid CORS issues):

```javascript
// server.js
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const FormData = require('form-data');
const fetch = require('node-fetch');

const app = express();
const upload = multer();

// CORS configuration
const corsOptions = {
  origin: true,
  credentials: true,
  optionsSuccessStatus: 200,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept']
};
app.use(cors(corsOptions));
app.use(express.json());

// RAG proxy endpoints
const RAG_BASE_URL = 'https://dev.myblocks.in:12095';

// Get categories
app.post('/api/rag-proxy/categories', async (req, res) => {
  try {
    const response = await fetch(`${RAG_BASE_URL}/api/rag/categories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error("RAG Proxy Error (Categories):", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Upload documents
app.post('/api/rag-proxy/upload', upload.array('files'), async (req, res) => {
  try {
    const form = new FormData();
    form.append('username', req.body.username);
    form.append('userid', req.body.userid);
    form.append('category', req.body.category);

    if (req.files && req.files.length > 0) {
      req.files.forEach(file => {
        form.append('files', file.buffer, {
          filename: file.originalname,
          contentType: file.mimetype,
        });
      });
    }

    const response = await fetch(`${RAG_BASE_URL}/api/rag/upload`, {
      method: 'POST',
      headers: form.getHeaders(),
      body: form
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error("RAG Proxy Error (Upload):", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Update index
app.post('/api/rag-proxy/update-index', async (req, res) => {
  try {
    const response = await fetch(`${RAG_BASE_URL}/api/rag/update-index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error("RAG Proxy Error (Update Index):", error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Start server
const PORT = process.env.PORT || 5636;
app.listen(PORT, () => console.log(`🚀 Server running on http://localhost:${PORT}`));
```

---

## React Frontend Example

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5636'; // Your proxy server

const RAGUploader = () => {
  const [ragUserid, setRagUserid] = useState('1559');
  const [ragCategories, setRagCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // Fetch categories when component loads
  useEffect(() => {
    if (ragUserid) {
      fetchCategories();
    }
  }, [ragUserid]);

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag-proxy/categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: ragUserid,
          userid: ragUserid
        })
      });
      const data = await response.json();
      if (data.success && data.categories) {
        setRagCategories(data.categories);
        if (data.categories.length > 0) {
          setSelectedCategory(data.categories[0].name);
        }
      }
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  };

  const handleAddToRag = async () => {
    if (!selectedFile) {
      alert('Please select a file first');
      return;
    }
    if (!selectedCategory) {
      alert('Please select a category');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('username', ragUserid);
      formData.append('userid', ragUserid);
      formData.append('category', selectedCategory);
      formData.append('files', selectedFile);

      // Upload file
      await axios.post(
        `${API_BASE_URL}/api/rag-proxy/upload`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      // Update index
      await axios.post(
        `${API_BASE_URL}/api/rag-proxy/update-index`,
        {
          username: ragUserid,
          userid: ragUserid,
          category: selectedCategory
        }
      );

      alert('✅ Document added to RAG and indexed successfully!');
      setSelectedFile(null);
    } catch (err) {
      console.error("Error uploading to RAG:", err);
      alert('Error uploading to RAG: ' + (err.response?.data?.error || err.message));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="rag-uploader">
      <h2>RAG Document Uploader</h2>
      
      <div style={{ marginBottom: '16px' }}>
        <label>User ID:</label>
        <input 
          type="text" 
          value={ragUserid} 
          onChange={(e) => setRagUserid(e.target.value)}
        />
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label>Category:</label>
        <select 
          value={selectedCategory} 
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="">Select a category</option>
          {ragCategories.map((cat, idx) => (
            <option key={idx} value={cat.name}>{cat.name}</option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label>Select File:</label>
        <input 
          type="file" 
          onChange={(e) => setSelectedFile(e.target.files[0])}
        />
        {selectedFile && <p>Selected: {selectedFile.name}</p>}
      </div>

      <button 
        onClick={handleAddToRag} 
        disabled={uploading || !selectedFile || !selectedCategory}
      >
        {uploading ? 'Uploading...' : 'Upload to RAG'}
      </button>
    </div>
  );
};

export default RAGUploader;
```

---

## Python Example Implementation (without proxy)

```python
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

RAG_BASE_URL = "https://dev.myblocks.in:12095"
USER_ID = "1559"
CATEGORY = "Career book"
FILE_PATH = "test.pdf"

# Step 1: Get categories
categories_response = requests.post(
    f"{RAG_BASE_URL}/api/rag/categories",
    json={"username": USER_ID, "userid": USER_ID}
)
print("Categories response:", categories_response.json())

# Step 2: Upload file
with open(FILE_PATH, 'rb') as f:
    multipart_data = MultipartEncoder(
        fields={
            'username': USER_ID,
            'userid': USER_ID,
            'category': CATEGORY,
            'files': (FILE_PATH, f, 'application/pdf')
        }
    )
    
    upload_response = requests.post(
        f"{RAG_BASE_URL}/api/rag/upload",
        data=multipart_data,
        headers={'Content-Type': multipart_data.content_type}
    )
    print("Upload response:", upload_response.json())

# Step 3: Update index
index_response = requests.post(
    f"{RAG_BASE_URL}/api/rag/update-index",
    json={"username": USER_ID, "userid": USER_ID, "category": CATEGORY}
)
print("Update index response:", index_response.json())
```

---

## Troubleshooting
- **CORS Issues**: Use a proxy server (like the Node.js example) to avoid CORS errors when calling the RAG API from the browser
- **File Too Large**: Check RAG server size limits
- **Category Not Found**: Ensure the category exists and is owned by the user
