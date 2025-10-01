import { NextRequest, NextResponse } from 'next/server'

/**
 * Upload API Route - Proxy to Python Backend
 * Forwards file uploads to the GraphRAG backend for processing
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const files = formData.getAll('files') as File[]
    
    if (!files || files.length === 0) {
      return NextResponse.json({ error: 'No files provided' }, { status: 400 })
    }

    // Forward to Python backend
    const backendFormData = new FormData()
    files.forEach(file => {
      backendFormData.append('files', file)
    })

    const response = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: backendFormData,
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json(
      { 
        success: false,
        error: 'Unable to connect to the backend. Please ensure the backend server is running.',
        message: 'Upload failed'
      },
      { status: 500 }
    )
  }
}