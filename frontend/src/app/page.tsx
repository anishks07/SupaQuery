'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { 
  Upload, 
  FileText, 
  Image, 
  Mic, 
  Send, 
  Download, 
  Tag, 
  Moon, 
  Sun,
  MessageCircle,
  Bot,
  User,
  Paperclip,
  X,
  Loader2,
  Volume2,
  Menu,
  UploadCloud,
  RefreshCw
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import ProtectedRoute from '@/components/ProtectedRoute'
import UserMenu from '@/components/UserMenu'

interface UploadedFile {
  id: string
  name: string
  type: 'pdf' | 'docx' | 'image' | 'audio'
  size: number
  uploadProgress: number
  tags: string[]
  uploadedAt: Date
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: Array<{
    title: string
    url: string
    snippet: string
  }>
}

function ThemeWrapper({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return <div className="flex h-screen bg-background">{children}</div>
  }

  return <>{children}</>
}

export default function AIDashboard() {
  const [mounted, setMounted] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system')
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const [showMobilePanel, setShowMobilePanel] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isListening, setIsListening] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Get theme from localStorage or system preference
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null
    if (savedTheme) {
      setTheme(savedTheme)
    } else {
      setTheme('system')
    }
    
    // Fetch existing documents when component mounts
    fetchDocuments()
  }, [])
  
  const fetchDocuments = async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      if (!token) return;
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.documents) {
          // Convert backend documents to frontend format
          const existingFiles: UploadedFile[] = data.documents.map((doc: any) => ({
            id: doc.id.toString(),
            name: doc.filename,
            type: getFileType(doc.filename),
            size: doc.file_size || 0,
            uploadProgress: 100, // Already uploaded
            tags: [],
            uploadedAt: new Date(doc.created_at)
          }));
          setUploadedFiles(existingFiles);
        }
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  }

  useEffect(() => {
    if (!mounted) return
    
    // Apply theme to document
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else if (theme === 'light') {
      root.classList.remove('dark')
    } else {
      // System theme
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        root.classList.add('dark')
      } else {
        root.classList.remove('dark')
      }
    }
    
    // Save to localStorage
    localStorage.setItem('theme', theme)
  }, [theme, mounted])

  const handleThemeChange = (newTheme: 'light' | 'dark') => {
    setTheme(newTheme)
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files)
    }
  }

  const handleFiles = async (files: FileList) => {
    const newFiles: UploadedFile[] = Array.from(files).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      type: getFileType(file.name),
      size: file.size,
      uploadProgress: 0,
      tags: [],
      uploadedAt: new Date()
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])
    
    // Upload files to API
    const formData = new FormData()
    Array.from(files).forEach(file => {
      formData.append('files', file)
    })

    try {
      // Get auth token from localStorage
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      
      if (!token) {
        throw new Error('Please log in to upload files');
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        // Update files with processed status
        newFiles.forEach(file => {
          simulateUpload(file.id)
        })
      } else {
        throw new Error(data.detail || data.error || 'Upload failed')
      }
    } catch (error) {
      console.error('Upload error:', error)
      // Still simulate upload even if API fails for demo purposes
      newFiles.forEach(file => {
        simulateUpload(file.id)
      })
    }
  }

  const getFileType = (filename: string): 'pdf' | 'docx' | 'image' | 'audio' => {
    const ext = filename.toLowerCase().split('.').pop()
    if (ext === 'pdf') return 'pdf'
    if (ext === 'docx') return 'docx'
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return 'image'
    if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext || '')) return 'audio'
    return 'pdf'
  }

  const simulateUpload = (fileId: string) => {
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 30
      if (progress >= 100) {
        progress = 100
        clearInterval(interval)
      }
      
      setUploadedFiles(prev => 
        prev.map(file => 
          file.id === fileId ? { ...file, uploadProgress: progress } : file
        )
      )
    }, 300)
  }

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const addTag = (fileId: string, tag: string) => {
    if (!tag.trim()) return
    setUploadedFiles(prev => 
      prev.map(file => 
        file.id === fileId 
          ? { ...file, tags: [...new Set([...file.tags, tag.trim()])] }
          : file
      )
    )
  }

  const removeTag = (fileId: string, tagIndex: number) => {
    setUploadedFiles(prev => 
      prev.map(file => 
        file.id === fileId 
          ? { ...file, tags: file.tags.filter((_, i) => i !== tagIndex) }
          : file
      )
    )
  }

  const sendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = inputMessage
    setInputMessage('')
    setIsTyping(true)

    try {
      // Get auth token from localStorage
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      
      if (!token) {
        throw new Error('Please log in to use chat');
      }

      // Call the chat API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: currentInput,
          session_id: null
        }),
      })

      const data = await response.json()

      if (response.ok && data.response) {
        const aiMessage: Message = {
          id: Math.random().toString(36).substr(2, 9),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          citations: data.citations || []
        }
        setMessages(prev => [...prev, aiMessage])
      } else {
        throw new Error(data.detail || data.error || 'Failed to get response')
      }
    } catch (error) {
      console.error('Chat error:', error)
      // Fallback message
      const aiMessage: Message = {
        id: Math.random().toString(36).substr(2, 9),
        role: 'assistant',
        content: `I apologize, but I encountered an error while processing your request. Please try again later. Your question was: "${currentInput}"`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const startVoiceRecording = () => {
    setIsRecording(true)
    // Simulate voice recording
    setTimeout(() => {
      setIsRecording(false)
      setInputMessage('This is a simulated voice input about the uploaded documents')
    }, 3000)
  }

  const exportConversation = () => {
    const conversation = messages.map(msg => 
      `${msg.role === 'user' ? 'User' : 'AI'}: ${msg.content}`
    ).join('\n\n')
    
    const blob = new Blob([conversation], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ai-conversation-${new Date().toISOString().split('T')[0]}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf': return <FileText className="h-4 w-4" />
      case 'docx': return <FileText className="h-4 w-4" />
      case 'image': return <Image className="h-4 w-4" />
      case 'audio': return <Volume2 className="h-4 w-4" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  if (!mounted) {
    return (
      <div className="flex h-screen bg-background">
        <div className="flex items-center justify-center w-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <ThemeWrapper>
        <div className="flex h-screen bg-background">
        {/* Mobile Panel Overlay */}
        <AnimatePresence>
          {showMobilePanel && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setShowMobilePanel(false)}
            />
          )}
        </AnimatePresence>

        {/* Left Panel - Data Insertion (30% on desktop, overlay on mobile) */}
        <motion.div
          className={`fixed md:relative w-full md:w-[30%] lg:w-[30%] h-full bg-background border-r border-border flex flex-col z-50 md:z-auto transform transition-transform duration-300 ease-in-out ${
            showMobilePanel ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          }`}
          initial={false}
        >
          <div className="p-3 md:p-4 border-b border-border">
            <div className="flex items-center justify-between mb-3 md:mb-4">
              <div className="flex items-center space-x-2">
                <h2 className="text-base md:text-lg font-semibold">Data Ingestion</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={fetchDocuments}
                  className="h-6 w-6 p-0"
                  title="Refresh documents"
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
              <div className="flex items-center space-x-2">
                <Sun className="h-3 w-3 md:h-4 md:w-4" />
                <Switch
                  checked={theme === 'dark'}
                  onCheckedChange={(checked) => handleThemeChange(checked ? 'dark' : 'light')}
                />
                <Moon className="h-3 w-3 md:h-4 md:w-4" />
                <Button
                  variant="ghost"
                  size="sm"
                  className="md:hidden h-6 w-6 p-0"
                  onClick={() => setShowMobilePanel(false)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>
            
            {/* Drag and Drop Area */}
            <motion.div
              className={`border-2 border-dashed rounded-lg p-4 md:p-6 text-center transition-colors ${
                dragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted-foreground/25 hover:border-muted-foreground/50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.jpg,.jpeg,.png,.gif,.webp,.mp3,.wav,.ogg,.m4a"
                onChange={handleFileSelect}
                className="hidden"
              />
              <UploadCloud className="h-6 w-6 md:h-8 md:w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-xs md:text-sm text-muted-foreground mb-2">
                Drag & drop files here or
              </p>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="text-xs md:text-sm"
              >
                Browse Files
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                PDF, DOCX, Images, Audio
              </p>
            </motion.div>
          </div>

          {/* File List */}
          <ScrollArea className="flex-1 p-3 md:p-4">
            {uploadedFiles.length > 0 && (
              <div className="mb-3 pb-2 border-b border-border">
                <p className="text-xs text-muted-foreground">
                  {uploadedFiles.length} document{uploadedFiles.length !== 1 ? 's' : ''} available
                </p>
              </div>
            )}
            <div className="space-y-2 md:space-y-3">
              <AnimatePresence>
                {uploadedFiles.map((file) => (
                  <motion.div
                    key={file.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Card className="p-2 md:p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2 flex-1 min-w-0">
                          {getFileIcon(file.type)}
                          <span className="text-xs md:text-sm font-medium truncate">
                            {file.name}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(file.id)}
                          className="h-5 w-5 md:h-6 md:w-6 p-0"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                      
                      <div className="text-xs text-muted-foreground mb-2">
                        {formatFileSize(file.size)}
                      </div>

                      {file.uploadProgress < 100 && (
                        <div className="mb-2">
                          <Progress value={file.uploadProgress} className="h-1" />
                          <div className="text-xs text-muted-foreground mt-1">
                            {Math.round(file.uploadProgress)}%
                          </div>
                        </div>
                      )}

                      {/* Tags */}
                      <div className="flex flex-wrap gap-1 mb-2">
                        {file.tags.map((tag, index) => (
                          <Badge
                            key={index}
                            variant="secondary"
                            className="text-xs cursor-pointer"
                            onClick={() => removeTag(file.id, index)}
                          >
                            {tag} ×
                          </Badge>
                        ))}
                        <Input
                          placeholder="Add tag..."
                          className="h-5 md:h-6 text-xs px-2 py-1 w-16 md:w-20"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              addTag(file.id, (e.target as HTMLInputElement).value)
                              ;(e.target as HTMLInputElement).value = ''
                            }
                          }}
                        />
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </ScrollArea>
        </motion.div>

        {/* Right Panel - Chat Interface (70% on desktop, full on mobile) */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className="p-3 md:p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="md:hidden h-8 w-8 p-0"
                  onClick={() => setShowMobilePanel(true)}
                >
                  <Menu className="h-4 w-4" />
                </Button>
                <MessageCircle className="h-4 w-4 md:h-5 md:w-5" />
                <h1 className="text-lg md:text-xl font-semibold">AI Assistant</h1>
              </div>
              <div className="flex items-center space-x-2">
                {/* Mobile theme toggle */}
                <div className="flex md:hidden items-center space-x-1">
                  <Sun className="h-3 w-3" />
                  <Switch
                    checked={theme === 'dark'}
                    onCheckedChange={(checked) => handleThemeChange(checked ? 'dark' : 'light')}
                  />
                  <Moon className="h-3 w-3" />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={exportConversation}
                  disabled={messages.length === 0}
                  className="text-xs md:text-sm"
                >
                  <Download className="h-3 w-3 md:h-4 md:w-4 mr-1 md:mr-2" />
                  <span className="hidden sm:inline">Export</span>
                </Button>
                <UserMenu />
              </div>
            </div>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-3 md:p-4">
            <div className="space-y-3 md:space-y-4 max-w-4xl mx-auto">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`flex items-start space-x-2 max-w-[85%] sm:max-w-[80%] ${
                      message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                    }`}>
                      <div className="flex-shrink-0">
                        {message.role === 'user' ? (
                          <div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-primary flex items-center justify-center">
                            <User className="h-3 w-3 md:h-4 md:w-4 text-primary-foreground" />
                          </div>
                        ) : (
                          <div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-muted flex items-center justify-center">
                            <Bot className="h-3 w-3 md:h-4 md:w-4" />
                          </div>
                        )}
                      </div>
                      <div>
                        <Card className={`p-2 md:p-3 ${
                          message.role === 'user' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted'
                        }`}>
                          <p className="text-xs md:text-sm whitespace-pre-wrap">
                            {message.content}
                          </p>
                        </Card>
                        
                        {/* Citations */}
                        {message.citations && message.citations.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {message.citations.map((citation, index) => (
                              <div key={index} className="text-xs text-muted-foreground">
                                <a 
                                  href={citation.url} 
                                  className="hover:text-primary underline"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  [{index + 1}] {citation.title}
                                </a>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        <div className="text-xs text-muted-foreground mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {/* Typing Indicator */}
              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-muted flex items-center justify-center">
                      <Bot className="h-3 w-3 md:h-4 md:w-4" />
                    </div>
                    <Card className="p-2 md:p-3 bg-muted">
                      <div className="flex items-center space-x-1">
                        <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-muted-foreground rounded-full animate-bounce" />
                        <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </Card>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="p-3 md:p-4 border-t border-border">
            <div className="flex items-end space-x-2 max-w-4xl mx-auto">
              <div className="flex-1">
                <Textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask me anything about your documents..."
                  className="min-h-[50px] md:min-h-[60px] resize-none text-sm"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage()
                    }
                  }}
                />
              </div>
              <div className="flex flex-row md:flex-col space-x-2 md:space-x-0 md:space-y-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={startVoiceRecording}
                  disabled={isRecording}
                  className={`${isRecording ? 'animate-pulse' : ''} h-8 w-8 md:h-auto md:w-auto p-0 md:p-2`}
                >
                  {isRecording ? (
                    <Loader2 className="h-3 w-3 md:h-4 md:w-4 animate-spin" />
                  ) : (
                    <Mic className="h-3 w-3 md:h-4 md:w-4" />
                  )}
                </Button>
                <Button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isTyping}
                  size="sm"
                  className="h-8 w-8 md:h-auto md:w-auto p-0 md:p-2"
                >
                  <Send className="h-3 w-3 md:h-4 md:w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ThemeWrapper>
    </ProtectedRoute>
  )
}