# Delete Feature - Testing Guide

## What's Been Fixed

### UI Changes ✅
- **Icon**: Changed from `X` to red `Trash2` icon
- **Color**: Always red (text-red-500)
- **Hover**: Darker red with light background
- **Size**: Slightly larger on desktop
- **Tooltip**: "Delete document"

### Functionality ✅
- **Confirmation Dialog**: Asks before deleting
- **API Integration**: Calls DELETE /api/documents/{id}
- **Database Cleanup**: Removes from PostgreSQL
- **Graph Cleanup**: Removes from Memgraph knowledge graph
- **UI Update**: Removes from file list immediately

## How to Test

### 1. Check the UI
1. Open the app: http://localhost:3000
2. Log in as admin
3. Look at the document list on the left
4. You should see a **RED TRASH ICON** next to each document
5. Hover over it - it should get darker and show "Delete document"

### 2. Test Deletion
1. Click the red trash icon on any document
2. A confirmation dialog should appear:
   > "Are you sure you want to delete this document? This action cannot be undone."
3. Click **OK** to confirm
4. The document should:
   - Disappear from the list immediately
   - Be removed from PostgreSQL database
   - Be removed from Memgraph knowledge graph
5. Refresh the page
6. The document should still be gone
7. Ask chatbot: "what are the names of the documents"
8. It should show one less document

### 3. If It's Not Working

#### If you don't see the red trash icon:
- Hard refresh: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)
- Check browser console (F12) for errors
- Make sure frontend is running: `npm run dev`

#### If deletion doesn't work:
- Open browser console (F12)
- Click the trash icon
- Check for error messages
- Common issues:
  - "No auth token found" → You're not logged in
  - "403 Forbidden" → You don't have delete permission
  - "404 Not Found" → Document doesn't exist
  - "Failed to fetch" → Backend not running

#### Check backend logs:
Look for:
- `🗑️ Deleting document from knowledge graph: {id}`
- `✅ Document {id} deleted from knowledge graph`

## Current Status

- **Documents**: 4
- **Backend**: Running on port 8000
- **Frontend**: Running on port 3000
- **Trash Icon**: ✅ Red trash bin
- **Delete API**: ✅ Working
- **Confirmation**: ✅ Working

## Code Files Modified

1. `frontend/src/app/page.tsx`
   - Updated `removeFile()` function (async, API call)
   - Changed icon from X to Trash2
   - Added red color styling
   - Added confirmation dialog

2. `backend/app/services/graph_rag_v2.py`
   - Added `delete_document()` method

3. `backend/main.py`
   - Delete endpoint already exists (line 498)

---

**Note**: If you're still seeing 4 documents after deletion, make sure:
1. You clicked OK on the confirmation dialog
2. No error appeared in the console
3. The document actually got removed from the UI
4. You're logged in with proper permissions
