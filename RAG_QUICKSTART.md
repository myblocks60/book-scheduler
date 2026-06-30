
# RAG Quickstart Guide

## 3 Simple Steps to Add RAG Integration

---

### Step 1: Get Available Categories
First, fetch what categories (folders) are available for your user.

```javascript
// Using fetch
const getCategories = async (userId) => {
  const response = await fetch("https://dev.myblocks.in:12095/api/rag/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: userId,
      userid: userId
    })
  });
  return await response.json();
};

// Example usage
getCategories("1559").then(data =&gt; console.log(data));
```

---

### Step 2: Upload Your File
Next, upload your generated file to a category.

```javascript
const uploadToRAG = async (userId, category, file) =&gt; {
  const formData = new FormData();
  formData.append("username", userId);
  formData.append("userid", userId);
  formData.append("category", category);
  formData.append("files", file);

  const response = await fetch("https://dev.myblocks.in:12095/api/rag/upload", {
    method: "POST",
    body: formData
  });
  return await response.json();
};
```

---

### Step 3: Update the Index
Finally, update the index so your file is searchable.

```javascript
const updateIndex = async (userId, category) =&gt; {
  const response = await fetch("https://dev.myblocks.in:12095/api/rag/update-index", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: userId,
      userid: userId,
      category: category
    })
  });
  return await response.json();
};
```

---

## How to Use in Your News Generation App

```javascript
// Full example: Generate news, save as PDF, upload to RAG
const generateNewsAndAddToRAG = async (topic) =&gt; {
  // 1. Generate your news content here
  const newsPDF = await generateNewsPDF(topic); // Your existing function
  
  // 2. Get RAG categories
  const categories = await getCategories("1559");
  const targetCategory = categories.categories[0].name;
  
  // 3. Upload to RAG
  await uploadToRAG("1559", targetCategory, newsPDF);
  
  // 4. Update index
  await updateIndex("1559", targetCategory);
  
  console.log("✅ News added to RAG successfully!");
};
```

---

## Notes
- User ID `1559` is just an example—use your actual user ID!
- Use a proxy server if calling from the browser to avoid CORS errors
- The file can be PDF, TXT, DOCX, or any other supported format

That's all you need!
