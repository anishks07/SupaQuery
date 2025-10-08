# Document Filtering Fix - October 5, 2025

## 🐛 Problem

When users **selected specific files** (checked the checkboxes) and asked questions, they got:
```
Error: [object Object]
AI: I apologize, but I encountered an error while processing your request.
```

But when **NO files were selected**, everything worked fine!

---

## 🔍 Root Cause Analysis

### Issue #1: Type Mismatch in API Schema

**Location:** `backend/app/models/schemas.py` line 8

**Problem:**
```python
class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[str]] = None  # ❌ Expected strings
    session_id: Optional[str] = None
```

**Frontend was sending:**
```typescript
const selectedDocIds = selectedFiles
  .map(file => parseInt(file.id))  // ✅ Sending integers: [1, 2, 3]
  .filter(id => !isNaN(id))
```

**Result:** 422 Validation Error - Pydantic rejected the request because it expected `List[str]` but received `List[int]`

---

### Issue #2: Database ID vs File ID Mismatch

**Location:** `backend/main.py` chat endpoint

**Problem:**
- Frontend sends **database IDs** (integers): `[1, 2, 3]`
- Memgraph stores documents with **file_ids** (UUID strings): `["35572985-490b-43e2-93fa-7aebe1e05a8d", ...]`
- Backend was passing database IDs directly to Memgraph
- Memgraph couldn't find documents because `WHERE d.id IN [1, 2, 3]` doesn't match UUID strings

**Result:** No chunks retrieved from Memgraph, leading to empty or incorrect answers

---

## ✅ Solution

### Fix #1: Update Schema to Accept Integers

**File:** `backend/app/models/schemas.py`

```python
class ChatRequest(BaseModel):
    message: str
    document_ids: Optional[List[int]] = None  # ✅ Changed from str to int
    session_id: Optional[str] = None
```

---

### Fix #2: Convert Database IDs to File IDs

**File:** `backend/main.py` (lines 610-628)

```python
# Verify user has access to requested documents and get file_ids
file_ids = None
if request.document_ids:
    print(f"   🔍 Converting {len(request.document_ids)} database IDs to file_ids...")
    file_ids = []
    for doc_id in request.document_ids:
        try:
            doc = await db_service.get_document(doc_id, current_user.id)
            if not doc:
                print(f"   ❌ Access denied to document {doc_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to document {doc_id}"
                )
            # Extract file_id from filename (remove extension)
            # filename format: "35572985-490b-43e2-93fa-7aebe1e05a8d.pdf"
            file_id = doc.filename.rsplit('.', 1)[0]
            file_ids.append(file_id)
            print(f"   ✓ Document {doc_id} ({doc.original_filename}) -> file_id: {file_id}")
        except Exception as e:
            print(f"   ❌ Error getting document {doc_id}: {e}")
            raise
```

**Then pass `file_ids` to GraphRAG:**

```python
# Query the GraphRAG system with file_ids instead of database IDs
response = await graph_rag_service.query(
    query=request.message,
    document_ids=file_ids,  # ✅ Pass file_ids, not database IDs
    conversation_history=conversation_history
)
```

---

## 🎯 How It Works Now

### Data Flow:

```
1. Frontend Selection:
   User checks: "research.pdf" (db_id: 1), "interview.wav" (db_id: 2)
   ↓
2. Frontend sends:
   document_ids: [1, 2]  (integers)
   ↓
3. Backend receives & validates:
   ✅ ChatRequest accepts List[int]
   ↓
4. Backend converts IDs:
   db_id 1 → looks up document → filename "uuid-abc.pdf" → file_id "uuid-abc"
   db_id 2 → looks up document → filename "uuid-xyz.wav" → file_id "uuid-xyz"
   ↓
5. Backend passes to Memgraph:
   file_ids: ["uuid-abc", "uuid-xyz"]
   ↓
6. Memgraph query:
   WHERE d.id IN ["uuid-abc", "uuid-xyz"]  ✅ Match!
   ↓
7. Retrieves correct chunks:
   Only chunks from selected documents
   ↓
8. Generates accurate answer:
   With citations from selected documents only
```

---

## 🧪 Testing

### Test Case 1: Single PDF Selected
**Action:** Check "2404.08865v1.pdf", ask "What are the main findings?"

**Expected Result:**
- ✅ Answer based only on that PDF
- ✅ Citations show page numbers: `📄 pp. 2-4`
- ✅ Evaluation score displayed: `✨ Quality: 87%`

---

### Test Case 2: Single Audio File Selected
**Action:** Check "interview.wav", ask "SUMMARIZE"

**Expected Result:**
- ✅ Answer based only on that audio file
- ✅ Citations show timestamps: `🕐 02:05 - 02:25`
- ✅ No more "Error: [object Object]"

---

### Test Case 3: Multiple Files Selected
**Action:** Check 2 PDFs + 1 audio, ask "Compare the key points"

**Expected Result:**
- ✅ Answer synthesizes information from all 3 selected files
- ✅ Mixed citations (PDF pages + audio timestamps)
- ✅ Quality evaluation runs normally

---

### Test Case 4: No Files Selected
**Action:** Don't check any files, ask "SUMMARIZE"

**Expected Result:**
- ✅ Searches all documents (already working)
- ✅ Returns comprehensive answer

---

## 🔧 Debug Logging Added

To help troubleshoot future issues:

```python
print(f"   🔍 Converting {len(request.document_ids)} database IDs to file_ids...")
print(f"   ✓ Document {doc_id} ({doc.original_filename}) -> file_id: {file_id}")
print(f"   Response keys: {response.keys()}")
print(f"   Citations count: {len(response.get('citations', []))}")
```

Watch the backend terminal for these messages to verify the flow.

---

## 📋 Files Modified

1. **`backend/app/models/schemas.py`**
   - Changed `document_ids` type from `List[str]` to `List[int]`

2. **`backend/main.py`** (chat endpoint)
   - Added database ID → file_id conversion logic
   - Added comprehensive error handling and debug logging
   - Modified to pass `file_ids` to `graph_rag_service.query()`

---

## 🚀 Deployment

**To apply the fix:**

1. Stop the backend:
   ```bash
   pkill -f "python.*main.py"
   ```

2. Start the backend:
   ```bash
   cd /Users/mac/Desktop/SupaQuery/backend
   python3 main.py
   ```

3. Reload frontend (it will pick up the API changes automatically)

4. Test with checked files!

---

## ✅ Status

- **Issue:** Document filtering with selected files causing 422 errors
- **Root Cause:** Type mismatch + ID mapping issue
- **Fix Applied:** ✅ Schema updated + ID conversion added
- **Testing:** Ready for user testing
- **Deployment:** Restart backend required

---

**Fixed by:** GitHub Copilot
**Date:** October 5, 2025, 11:10 PM
**Impact:** Critical - Enables core document-aware query feature
