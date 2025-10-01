import { NextRequest, NextResponse } from 'next/server'

/**
 * Chat API Route - Proxy to Python Backend
 * Forwards chat requests to the GraphRAG backend
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { message, documents } = body

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 })
    }

    // Extract document IDs if available
    const document_ids = documents?.map((doc: any) => doc.id) || []

    // Forward to Python backend
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        document_ids
      }),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()

    return NextResponse.json(data)

  } catch (error) {
    console.error('Chat API error:', error)
    
    return NextResponse.json({
      success: false,
      response: 'Unable to connect to the AI backend. Please ensure the backend server is running.',
      citations: [],
      sources: [],
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}