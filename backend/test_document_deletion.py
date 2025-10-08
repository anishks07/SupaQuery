"""
Test Document Deletion Functionality
This script helps verify that document deletion works correctly
"""

import requests
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
UPLOADS_DIR = Path("uploads")

def test_document_deletion():
    """
    Test the complete document deletion workflow
    
    Steps:
    1. Login to get auth token
    2. Upload a test document
    3. Verify file exists in uploads/
    4. Delete the document
    5. Verify file is removed from uploads/
    6. Verify document is removed from knowledge graph
    """
    
    print("=" * 80)
    print("Document Deletion Test")
    print("=" * 80)
    
    # Step 1: Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "test_user",  # Replace with your username
            "password": "test_pass"   # Replace with your password
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Upload a test document
    print("\n2. Uploading test document...")
    test_content = b"This is a test document for deletion testing."
    files = {"files": ("test_delete.txt", test_content, "text/plain")}
    
    upload_response = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        files=files
    )
    
    if upload_response.status_code != 200:
        print(f"❌ Upload failed: {upload_response.text}")
        return
    
    upload_data = upload_response.json()
    document_id = upload_data["files"][0]["id"]
    print(f"✅ Document uploaded with ID: {document_id}")
    
    # Step 3: List documents to verify upload
    print("\n3. Verifying document exists...")
    list_response = requests.get(f"{BASE_URL}/api/documents", headers=headers)
    documents = list_response.json()
    
    doc_exists = any(doc["id"] == document_id for doc in documents)
    if not doc_exists:
        print(f"❌ Document not found in list")
        return
    
    print(f"✅ Document exists in database")
    
    # Find the uploaded file in uploads directory
    print("\n4. Checking physical file...")
    uploaded_files = list(UPLOADS_DIR.glob("*"))
    initial_file_count = len(uploaded_files)
    print(f"   Files in uploads/: {initial_file_count}")
    
    # Step 4: Delete the document
    print(f"\n5. Deleting document {document_id}...")
    delete_response = requests.delete(
        f"{BASE_URL}/api/documents/{document_id}",
        headers=headers
    )
    
    if delete_response.status_code != 200:
        print(f"❌ Delete failed: {delete_response.text}")
        return
    
    print(f"✅ Delete API call successful")
    
    # Step 5: Verify deletion
    print("\n6. Verifying complete deletion...")
    
    # Check database
    list_response = requests.get(f"{BASE_URL}/api/documents", headers=headers)
    documents = list_response.json()
    doc_exists = any(doc["id"] == document_id for doc in documents)
    
    if doc_exists:
        print(f"❌ Document still exists in database")
    else:
        print(f"✅ Document removed from database")
    
    # Check file system
    final_files = list(UPLOADS_DIR.glob("*"))
    final_file_count = len(final_files)
    
    if final_file_count < initial_file_count:
        print(f"✅ Physical file deleted (before: {initial_file_count}, after: {final_file_count})")
    else:
        print(f"⚠️  Physical file may not be deleted (before: {initial_file_count}, after: {final_file_count})")
    
    # Check knowledge graph
    print("\n7. Checking knowledge graph...")
    chat_response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json={
            "message": "What documents do you have?",
            "session_id": "test_session"
        }
    )
    
    if chat_response.status_code == 200:
        answer = chat_response.json()["answer"]
        print(f"   GraphRAG response: {answer[:100]}...")
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_document_deletion()
