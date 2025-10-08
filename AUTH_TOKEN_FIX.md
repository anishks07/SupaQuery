# Authentication Token Error Fix

## Problem
You're seeing the error: **"Could not validate credentials"** when trying to chat with documents.

## Root Cause
Your JWT authentication token has either:
1. ✅ **Expired** (tokens expire after 30 minutes by default)
2. ✅ **Invalidated** (if backend SECRET_KEY changed)
3. ✅ **Missing** (not logged in properly)

---

## 🔧 Quick Fix - 3 Steps

### Step 1: Clear Browser Storage
Open your browser console (press `F12` or `Cmd+Option+J` on Mac) and run:
```javascript
localStorage.clear()
```

### Step 2: Refresh the Page
```
Cmd+R (Mac) or Ctrl+R (Windows)
```

### Step 3: Login Again
1. You'll be redirected to `/login`
2. Login with your credentials
3. You'll be redirected back to the main page
4. Try chatting again

---

## ✅ What Was Fixed

### Added Automatic Token Expiry Handling
The frontend now automatically:
- ✅ Detects when your token has expired (401 errors)
- ✅ Clears the invalid token
- ✅ Redirects you to login page
- ✅ Works across all API calls (chat, upload, delete, fetch documents)

### Changed Files
- `frontend/src/app/page.tsx` - Added 401 error handling to all API calls

---

## 🔐 How Authentication Works Now

### 1. Login Flow
```
User enters credentials → Backend validates → Returns JWT token → 
Frontend stores in localStorage → Token sent with every request
```

### 2. Token Validation
```
Every API request → Backend checks JWT token → 
If valid: Process request
If expired/invalid: Return 401 → Frontend redirects to login
```

### 3. Protected Routes
All these routes now require authentication:
- ✅ `POST /api/chat` - Chat with documents
- ✅ `POST /api/upload` - Upload documents
- ✅ `GET /api/documents` - List documents
- ✅ `DELETE /api/documents/{id}` - Delete document

---

## 🛠️ Testing Your Fix

### Test 1: Login
```bash
# Visit login page
open http://localhost:3000/login

# Login with test credentials
username: admin
password: admin
```

### Test 2: Upload Document
1. Go to main page
2. Click "Upload Files"
3. Select a PDF
4. Confirm upload works

### Test 3: Chat
1. Type a message: "Summarize the document"
2. Press Enter or click Send
3. Should get AI response

### Test 4: Token Expiry (Optional)
```javascript
// In browser console, corrupt the token
localStorage.setItem('auth_token', 'invalid_token')

// Try to chat - should redirect to login
```

---

## 📊 Token Lifecycle

```
Login (t=0min) → Token Valid (0-30min) → Token Expires (t=30min) → 
User makes request → 401 Error → Auto-redirect to login → User logs in again
```

---

## 🚨 If You Still Have Issues

### Issue 1: "No authentication token found"
**Solution:** You're not logged in. Go to `/login` and log in.

### Issue 2: Token keeps expiring immediately
**Solution:** Check if backend SECRET_KEY is consistent:
```bash
# In backend/.env
SECRET_KEY=your-secret-key-here  # Must not change

# Generate a new one if needed
openssl rand -hex 32
```

### Issue 3: Backend not running
**Solution:** Start the backend:
```bash
cd backend
python main.py
```

### Issue 4: Frontend not running
**Solution:** Start the frontend:
```bash
cd frontend
npm run dev
```

---

## 🎯 Best Practices Going Forward

1. **Don't change SECRET_KEY** in production (invalidates all tokens)
2. **Users will be auto-logged out** after 30 minutes of inactivity
3. **Increase token expiry** if needed (edit `backend/.env`):
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```
4. **Always check browser console** for auth errors

---

## 📝 Summary

The "Could not validate credentials" error has been fixed by:
1. ✅ Adding automatic 401 error detection
2. ✅ Auto-clearing expired tokens
3. ✅ Auto-redirecting to login page
4. ✅ Handling errors in all API calls

**Next time this happens:** Just login again! The app will handle the rest automatically.

---

## 🔍 Debugging Tips

### Check if you're logged in:
```javascript
// In browser console
localStorage.getItem('auth_token')
// Should return a long JWT string if logged in
```

### Check token expiry:
```javascript
// In browser console
const token = localStorage.getItem('auth_token')
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('Token expires:', new Date(payload.exp * 1000))
```

### Check backend logs:
```bash
# Backend terminal should show:
INFO:     POST /api/chat HTTP/1.1 401 Unauthorized
# This confirms token is invalid
```

---

**Status:** ✅ FIXED - Auto-redirect on token expiry implemented
**Date:** October 5, 2025
