'use client'

import React, { useState, useEffect, useRef } from 'react'
import { 
  MessageSquare, 
  Database, 
  TrendingUp, 
  Terminal, 
  Send, 
  Upload, 
  FolderPlus, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  ChevronRight, 
  RefreshCw, 
  Code2, 
  HelpCircle,
  Play
} from 'lucide-react'

// Define interfaces
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  intent?: string
  citations?: Citation[]
  thoughtSteps?: string[]
}

interface Citation {
  index: number
  file_name: string
  page: number
  section: string
  chunk_id: string
  text_preview: string
}

interface EvalMetric {
  metric: string
  baseline: string
  agentic: string
  improvement: string
  status_label: string
}

export default function AgenticKnowledgeOS() {
  const [activeTab, setActiveTab] = useState<'chat' | 'ingest' | 'eval' | 'parallel'>('chat')
  
  // Parallel Task States
  const [taskInput, setTaskInput] = useState('Truy xuất tài liệu autoscaling k3s, rà soát lỗ hổng bảo mật codebase, đánh giá hiệu năng và đề xuất kế hoạch triển khai song song')
  const [maxWorkers, setMaxWorkers] = useState(4)
  const [optimizePlan, setOptimizePlan] = useState(true)
  const [decomposition, setDecomposition] = useState<any>(null)
  const [isExecutingTasks, setIsExecutingTasks] = useState(false)
  const [taskStatuses, setTaskStatuses] = useState<Record<string, any>>({})
  const [executionResult, setExecutionResult] = useState<any>(null)
  const [selectedTaskDetails, setSelectedTaskDetails] = useState<any>(null)
  const [executionTime, setExecutionTime] = useState(0)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Xin chào! Tôi là Agentic Knowledge OS, một nền tảng RAG đa tác vụ (Multi-Agent RAG). Tôi có thể giúp bạn trả lời tài liệu có nguồn trích dẫn rõ ràng, phân tích cấu trúc mã nguồn, review code hoặc tạo kế hoạch checklist triển khai kỹ thuật. Bạn muốn tìm hiểu gì hôm nay?',
      intent: 'welcome',
      thoughtSteps: ['Hệ thống khởi chạy thành công', 'Sub-agents sẵn sàng kết nối']
    }
  ])
  const [userInput, setUserInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  
  // Ingestion States
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [ingestStatus, setIngestStatus] = useState<{ type: 'success' | 'error' | 'loading' | null; msg: string }>({ type: null, msg: '' })
  const [repoPath, setRepoPath] = useState('')
  const [repoName, setRepoName] = useState('')

  // Eval States
  const [evalMarkdown, setEvalMarkdown] = useState('')
  const [evalMetrics, setEvalMetrics] = useState<EvalMetric[]>([])
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [goldCount, setGoldCount] = useState(30)

  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (activeTab === 'eval') {
      fetchLatestEval()
    }
  }, [activeTab])

  // Fetch Latest Evaluation Results
  const fetchLatestEval = async () => {
    try {
      const res = await fetch('/api/eval/latest')
      if (res.ok) {
        const data = await res.json()
        setEvalMarkdown(data.results_markdown)
        setEvalMetrics(data.metrics || [])
        setGoldCount(data.golden_dataset_count || 30)
      }
    } catch (e) {
      console.error('Failed to load eval metrics', e)
    }
  }

  // Handle Triggering new Evaluation
  const runEvaluationSuite = async () => {
    setIsEvaluating(true)
    try {
      const res = await fetch('/api/eval/run', { method: 'POST' })
      if (res.ok) {
        alert('Đã kích hoạt chạy đánh giá RAG ở chế độ nền! Vui lòng làm mới trang sau 10-15 giây để xem bảng so sánh cập nhật.')
      }
    } catch (e) {
      alert('Có lỗi xảy ra khi kích hoạt chạy đánh giá.')
    } finally {
      setIsEvaluating(false)
    }
  }

  // Handle Document Ingest
  const handleDocumentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return
    
    setIngestStatus({ type: 'loading', msg: 'Đang tải lên và phân tích tài liệu (PDF/DOCX/MD/TXT)...' })
    const formData = new FormData()
    formData.append('file', selectedFile)
    
    try {
      const res = await fetch('/api/ingest/document', {
        method: 'POST',
        body: formData
      })
      if (res.ok) {
        const data = await res.json()
        setIngestStatus({ 
          type: 'success', 
          msg: `Thành công! Đã ingest file "${data.file_name}" thành ${data.chunk_count} đoạn nhỏ trong Qdrant.` 
        })
        setSelectedFile(null)
      } else {
        const err = await res.json()
        setIngestStatus({ type: 'error', msg: err.detail || 'Tải tài liệu lên thất bại.' })
      }
    } catch (err) {
      setIngestStatus({ type: 'error', msg: 'Không thể kết nối đến máy chủ backend.' })
    }
  }

  // Handle Codebase Ingest
  const handleRepoSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!repoPath || !repoName) return
    
    setIngestStatus({ type: 'loading', msg: 'Đang quét cấu trúc thư mục codebase và trích xuất dữ liệu...' })
    
    try {
      const res = await fetch('/api/ingest/repo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPath, repo_name: repoName })
      })
      if (res.ok) {
        const data = await res.json()
        setIngestStatus({ 
          type: 'success', 
          msg: `Thành công! Đã quét repo "${data.file_name}" và lưu ${data.chunk_count} phân đoạn mã nguồn.` 
        })
        setRepoPath('')
        setRepoName('')
      } else {
        const err = await res.json()
        setIngestStatus({ type: 'error', msg: err.detail || 'Ingest codebase thất bại.' })
      }
    } catch (err) {
      setIngestStatus({ type: 'error', msg: 'Không thể kết nối đến backend.' })
    }
  }

  // Handle Sending Chat Query
  const handleSendQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userInput.trim()) return

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: userInput
    }

    setMessages(prev => [...prev, userMessage])
    setUserInput('')
    setIsSending(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content })
      })

      if (res.ok) {
        const data = await res.json()
        const assistantMessage: Message = {
          id: `msg-${Date.now()}-ai`,
          role: 'assistant',
          content: data.answer,
          intent: data.intent,
          citations: data.citations,
          thoughtSteps: data.thought_steps
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        setMessages(prev => [...prev, {
          id: `msg-error`,
          role: 'assistant',
          content: 'Thành thật xin lỗi, máy chủ gặp sự cố khi xử lý câu hỏi này.'
        }])
      }
    } catch (e) {
      setMessages(prev => [...prev, {
        id: `msg-error`,
        role: 'assistant',
        content: 'Không thể kết nối được tới máy chủ backend. Vui lòng kiểm tra cổng dịch vụ.'
      }])
    } finally {
      setIsSending(false)
    }
  }

  const handleRunParallelDecomposer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!taskInput.trim()) return

    setIsExecutingTasks(true)
    setDecomposition(null)
    setExecutionResult(null)
    setSelectedTaskDetails(null)
    setExecutionTime(0)

    const startT = Date.now()
    const timer = setInterval(() => {
      setExecutionTime(Number(((Date.now() - startT) / 1000).toFixed(1)))
    }, 100)

    try {
      const response = await fetch('/api/agents/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request: taskInput,
          max_workers: maxWorkers,
          enable_optimization: optimizePlan
        })
      })

      if (!response.ok) {
        throw new Error("Không thể kết nối đến máy chủ API song song.")
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      if (reader) {
        while (true) {
          const { value, done } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() || ""

          for (const line of lines) {
            if (!line.trim()) continue
            try {
              const data = JSON.parse(line)

              if (data.phase === "decomposition_complete") {
                setDecomposition(data.decomposition)
                // Initialize statuses
                const statuses: any = {}
                data.decomposition.subtasks.forEach((t: any) => {
                  statuses[t.id] = { status: "pending", error: null, result: null }
                })
                setTaskStatuses(statuses)
              } else if (data.phase === "progress") {
                setTaskStatuses((prev: any) => ({
                  ...prev,
                  [data.current_task]: {
                    ...prev[data.current_task],
                    status: data.status
                  }
                }))
              } else if (data.phase === "execution_complete") {
                setExecutionResult(data)
                
                // Set all final statuses
                const finalStatuses: any = {}
                Object.keys(data.results).forEach((tid) => {
                  const r = data.results[tid]
                  finalStatuses[tid] = {
                    status: r.status,
                    error: r.error,
                    result: r.result,
                    duration_sec: r.duration_sec
                  }
                })
                setTaskStatuses(finalStatuses)
                clearInterval(timer)
                setIsExecutingTasks(false)
                // Set initial active task preview to first task
                if (data.decomposition?.subtasks?.length > 0) {
                  const firstTaskId = data.decomposition.subtasks[0].id
                  setSelectedTaskDetails({
                    id: firstTaskId,
                    title: data.decomposition.subtasks[0].title,
                    ...finalStatuses[firstTaskId]
                  })
                }
              } else if (data.phase === "error") {
                alert("Lỗi thực thi: " + data.error)
                clearInterval(timer)
                setIsExecutingTasks(false)
              }
            } catch (err) {
              console.error("Lỗi parse dòng NDJSON:", err, line)
            }
          }
        }
      }
    } catch (err: any) {
      alert("Đã xảy ra sự cố trong quá trình chạy song song: " + err.message)
      clearInterval(timer)
      setIsExecutingTasks(false)
    }
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#0b0f19] text-gray-100 font-sans">
      
      {/* 1. Header Navigation Bar */}
      <header className="flex h-16 items-center justify-between border-b border-white/5 bg-[#131a2c]/60 px-6 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-lg shadow-indigo-500/20">
            <Terminal className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white font-mono">
              AGENTIC <span className="gradient-text">KNOWLEDGE OS</span>
            </h1>
            <p className="text-[10px] text-gray-400">MCP-Powered Multi-Agent RAG v1.0</p>
          </div>
        </div>

        <nav className="flex items-center space-x-2">
          <button 
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${activeTab === 'chat' ? 'bg-indigo-600/30 border border-indigo-500/30 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
          >
            <MessageSquare className="h-4 w-4" />
            <span>AI Agent Chat</span>
          </button>
          <button 
            onClick={() => setActiveTab('ingest')}
            className={`flex items-center space-x-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${activeTab === 'ingest' ? 'bg-indigo-600/30 border border-indigo-500/30 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
          >
            <Database className="h-4 w-4" />
            <span>Ingest Knowledge</span>
          </button>
          <button 
            onClick={() => setActiveTab('eval')}
            className={`flex items-center space-x-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${activeTab === 'eval' ? 'bg-indigo-600/30 border border-indigo-500/30 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
          >
            <TrendingUp className="h-4 w-4" />
            <span>Evaluation Dashboard</span>
          </button>
          <button 
            onClick={() => setActiveTab('parallel')}
            className={`flex items-center space-x-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${activeTab === 'parallel' ? 'bg-indigo-600/30 border border-indigo-500/30 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}
          >
            <Terminal className="h-4 w-4" />
            <span>Parallel Task Agent</span>
          </button>
        </nav>

        <div className="flex items-center space-x-2 rounded-full bg-emerald-500/10 px-3 py-1 text-[10px] font-semibold text-emerald-400 border border-emerald-500/20">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>SYSTEM ACTIVE</span>
        </div>
      </header>

      {/* 2. Main Tab Contents */}
      <main className="flex flex-1 overflow-hidden">
        
        {/* A. Chat Module Panel */}
        {activeTab === 'chat' && (
          <div className="flex flex-1 overflow-hidden">
            {/* Left: Chat Flow */}
            <div className="flex flex-1 flex-col justify-between bg-[#0b0f19]">
              
              {/* Message History */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map(msg => (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-2xl p-5 border ${msg.role === 'user' ? 'bg-indigo-600/20 border-indigo-500/20 text-white' : 'bg-[#131a2c]/80 border-white/5 shadow-md'}`}>
                      
                      {/* Intent Banner */}
                      {msg.intent && msg.intent !== 'welcome' && (
                        <div className="mb-2 flex items-center space-x-2">
                          <span className="rounded bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 text-[10px] font-bold text-cyan-400 uppercase font-mono">
                            Intent: {msg.intent}
                          </span>
                        </div>
                      )}

                      {/* Collapsible Reasoning Logs */}
                      {msg.thoughtSteps && msg.thoughtSteps.length > 0 && (
                        <details className="mb-3 rounded-lg bg-black/20 p-2 text-xs border border-white/5">
                          <summary className="cursor-pointer font-semibold text-indigo-400 hover:underline">
                            🔍 Xem suy nghĩ của Agent ({msg.thoughtSteps.length} bước)
                          </summary>
                          <ul className="mt-2 space-y-1 pl-4 list-disc text-gray-400 font-mono">
                            {msg.thoughtSteps.map((step, idx) => (
                              <li key={idx}>{step}</li>
                            ))}
                          </ul>
                        </details>
                      )}

                      {/* Chat text */}
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                      {/* Inline citations mapping links */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-4 border-t border-white/5 pt-3">
                          <p className="text-[10px] font-semibold uppercase text-gray-400 tracking-wider">📚 Tài liệu trích dẫn:</p>
                          <div className="mt-1 flex flex-wrap gap-2">
                            {msg.citations.map(cit => (
                              <button 
                                key={cit.index}
                                onClick={() => setSelectedCitation(cit)}
                                className="flex items-center space-x-1 rounded bg-white/5 border border-white/10 hover:border-indigo-400 px-2 py-1 text-xs text-indigo-400 hover:text-white transition"
                              >
                                <span>[{cit.index}]</span>
                                <span className="max-w-[100px] truncate">{cit.file_name}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input Uploader Box */}
              <div className="border-t border-white/5 bg-[#131a2c]/30 p-4">
                <form onSubmit={handleSendQuery} className="mx-auto max-w-4xl flex items-center space-x-3 rounded-xl bg-[#131a2c] border border-white/5 p-2 shadow-lg focus-within:border-indigo-500/50">
                  <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Đặt câu hỏi về tài liệu (autoscaling, k3s...) hoặc codebase..."
                    disabled={isSending}
                    className="flex-1 bg-transparent border-0 px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    disabled={isSending || !userInput.trim()}
                    className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:bg-gray-800 disabled:text-gray-600 transition"
                  >
                    {isSending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </button>
                </form>
              </div>
            </div>

            {/* Right: Citations side panel */}
            <div className="w-80 border-l border-white/5 bg-[#131a2c]/30 p-5 overflow-y-auto">
              <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">🔍 Chi tiết trích dẫn</h2>
              
              {selectedCitation ? (
                <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/20 p-4 space-y-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-indigo-400" />
                    <span className="font-bold text-sm truncate text-white">{selectedCitation.file_name}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-gray-400">
                    <div>Trang: <strong className="text-white">{selectedCitation.page}</strong></div>
                    <div>Phân mục: <strong className="text-white">{selectedCitation.section}</strong></div>
                  </div>
                  <div className="border-t border-white/5 pt-2">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Nội dung đoạn trích:</p>
                    <p className="mt-1 text-xs italic text-gray-300 leading-relaxed bg-black/35 p-3 rounded border border-white/5">
                      "{selectedCitation.text_preview}"
                    </p>
                  </div>
                  <div className="text-[9px] font-mono text-gray-500 text-right">Chunk: {selectedCitation.chunk_id}</div>
                </div>
              ) : (
                <div className="flex h-[80%] flex-col items-center justify-center text-center text-gray-500 p-4">
                  <HelpCircle className="h-8 w-8 text-gray-600 mb-2" />
                  <p className="text-xs">Click vào các trích dẫn ở dòng câu trả lời để xem chi tiết đoạn tài liệu tham khảo tương ứng.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* B. Ingestion Management Tab */}
        {activeTab === 'ingest' && (
          <div className="flex-1 overflow-y-auto bg-[#0b0f19] p-8">
            <div className="mx-auto max-w-4xl space-y-8">
              
              <div>
                <h2 className="text-2xl font-bold text-white font-mono">KNOWLEDGE BASE INGESTION</h2>
                <p className="text-xs text-gray-400 mt-1">Đăng ký dữ liệu mới vào Vector Database Qdrant và BM25 index phục vụ truy vấn lai.</p>
              </div>

              {/* Status Alert */}
              {ingestStatus.type && (
                <div className={`flex items-center space-x-3 rounded-lg border p-4 text-sm ${
                  ingestStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                  ingestStatus.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                  'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'
                }`}>
                  {ingestStatus.type === 'success' ? <CheckCircle className="h-5 w-5 flex-shrink-0" /> :
                   ingestStatus.type === 'error' ? <AlertCircle className="h-5 w-5 flex-shrink-0" /> :
                   <RefreshCw className="h-5 w-5 animate-spin flex-shrink-0" />}
                  <span>{ingestStatus.msg}</span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Form 1: Document Upload */}
                <div className="rounded-2xl border border-white/5 bg-[#131a2c]/50 p-6 space-y-4">
                  <div className="flex items-center space-x-2 text-indigo-400">
                    <Upload className="h-5 w-5" />
                    <h3 className="font-bold text-white font-mono">TẢI TÀI LIỆU LÊN</h3>
                  </div>
                  <p className="text-xs text-gray-400">Cho phép upload tệp đơn lẻ (PDF, DOCX, Markdown hoặc TXT) với kích thước tối đa 15MB.</p>
                  
                  <form onSubmit={handleDocumentSubmit} className="space-y-4 pt-2">
                    <div className="rounded-xl border border-dashed border-white/10 p-6 text-center hover:border-indigo-500 transition cursor-pointer bg-black/10">
                      <input 
                        type="file" 
                        id="docFile"
                        accept=".pdf,.docx,.md,.markdown,.txt"
                        onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        className="hidden"
                      />
                      <label htmlFor="docFile" className="cursor-pointer space-y-2 block">
                        <FileText className="mx-auto h-8 w-8 text-gray-500" />
                        <div className="text-sm font-semibold text-white">
                          {selectedFile ? selectedFile.name : 'Chọn một tệp từ máy tính'}
                        </div>
                        <p className="text-[10px] text-gray-500">PDF, DOCX, Markdown hoặc TXT tối đa 15MB</p>
                      </label>
                    </div>

                    <button
                      type="submit"
                      disabled={!selectedFile || ingestStatus.type === 'loading'}
                      className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-800 disabled:text-gray-500 transition"
                    >
                      Bắt đầu Ingest Tài liệu
                    </button>
                  </form>
                </div>

                {/* Form 2: Repository Ingestion */}
                <div className="rounded-2xl border border-white/5 bg-[#131a2c]/50 p-6 space-y-4">
                  <div className="flex items-center space-x-2 text-cyan-400">
                    <FolderPlus className="h-5 w-5" />
                    <h3 className="font-bold text-white font-mono">INGEST CODEBASE</h3>
                  </div>
                  <p className="text-xs text-gray-400">Index tự động các file code quan trọng (.py, .ts, .tsx, .js, .yaml, .yml, Dockerfile, Makefile) trong thư mục dự án.</p>
                  
                  <form onSubmit={handleRepoSubmit} className="space-y-4 pt-2">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Tên Repository</label>
                      <input 
                        type="text"
                        value={repoName}
                        onChange={(e) => setRepoName(e.target.value)}
                        placeholder="Ví dụ: agentic-knowledge-os"
                        className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Đường dẫn cục bộ (Absolute Path)</label>
                      <input 
                        type="text"
                        value={repoPath}
                        onChange={(e) => setRepoPath(e.target.value)}
                        placeholder="Ví dụ: /Users/username/project-dir"
                        className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={!repoPath || !repoName || ingestStatus.type === 'loading'}
                      className="w-full rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-cyan-500 disabled:bg-gray-800 disabled:text-gray-500 transition"
                    >
                      Bắt đầu Ingest Codebase
                    </button>
                  </form>
                </div>

              </div>

            </div>
          </div>
        )}

        {/* C. Evaluation Dashboard Tab */}
        {activeTab === 'eval' && (
          <div className="flex-1 overflow-y-auto bg-[#0b0f19] p-8">
            <div className="mx-auto max-w-4xl space-y-6">
              
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white font-mono">EVALUATION METRICS & DASHBOARD</h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Đo lường tính hiệu quả giữa RAG truyền thống và RAG Agentic thông qua tập câu hỏi mẫu gồm <strong>{goldCount} câu hỏi golden dataset</strong>.
                  </p>
                </div>
                
                <button
                  onClick={runEvaluationSuite}
                  disabled={isEvaluating}
                  className="flex items-center space-x-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-800 transition"
                >
                  <Play className="h-4 w-4" />
                  <span>{isEvaluating ? 'Đang đánh giá...' : 'Chạy thử nghiệm RAGAS'}</span>
                </button>
              </div>

              {/* Render results as structured styling panel */}
              {evalMetrics && evalMetrics.length > 0 ? (
                <div className="rounded-2xl border border-white/5 bg-[#131a2c]/50 p-6 space-y-6">
                  <div className="flex items-center space-x-2 text-indigo-400">
                    <TrendingUp className="h-5 w-5" />
                    <h3 className="font-bold text-white font-mono">BẢNG SO SÁNH HIỆU NĂNG</h3>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-left text-sm text-gray-300">
                      <thead>
                        <tr className="border-b border-white/10 text-gray-400 uppercase text-[10px] tracking-wider font-mono">
                          <th className="py-3 px-4">Evaluation Metric</th>
                          <th className="py-3 px-4 text-center">Baseline RAG</th>
                          <th className="py-3 px-4 text-center">Agentic RAG (LangGraph)</th>
                          <th className="py-3 px-4 text-center">Improvement</th>
                          <th className="py-3 px-4 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5 font-mono">
                        {evalMetrics.map((m, idx) => (
                          <tr key={idx} className="hover:bg-white/5">
                            <td className="py-4 px-4 font-sans font-semibold text-white">{m.metric}</td>
                            <td className="py-4 px-4 text-center">{m.baseline}</td>
                            <td className="py-4 px-4 text-center text-cyan-400 font-bold">{m.agentic}</td>
                            <td className="py-4 px-4 text-center text-emerald-400 font-bold">{m.improvement}</td>
                            <td className="py-4 px-4 text-center text-emerald-400 text-[10px] font-bold">{m.status_label}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="rounded-xl bg-black/25 border border-white/5 p-5 space-y-3 text-xs leading-relaxed text-gray-400">
                    <p className="font-bold text-white">💡 Đánh giá từ Hệ thống Observability:</p>
                    <p>
                      Kết quả đánh giá được trích xuất trực tiếp từ hệ thống RAG Evaluation. 
                      Sự chênh lệch giữa Baseline và Agentic thể hiện ưu thế của việc sử dụng LangGraph kết hợp với Critic Agent và Web Search Fallback (CRAG).
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex h-64 flex-col items-center justify-center text-center text-gray-500 rounded-2xl border border-dashed border-white/10 p-6 bg-black/10">
                  <TrendingUp className="h-10 w-10 text-gray-600 mb-3" />
                  <p className="text-sm">Chưa phát hiện kết quả đánh giá nào.</p>
                  <p className="text-xs text-gray-600 mt-1">Nhấp nút "Chạy thử nghiệm RAGAS" ở góc trên bên phải để kích hoạt đánh giá hiệu năng.</p>
                </div>
              )}

            </div>
          </div>
        )}

        {/* D. Parallel Task Agent Tab */}
        {activeTab === 'parallel' && (
          <div className="flex-1 overflow-y-auto bg-[#0b0f19] p-8">
            <div className="mx-auto max-w-6xl space-y-8">
              
              {/* Header */}
              <div className="flex flex-col space-y-2">
                <div className="flex items-center space-x-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                    <Terminal className="h-4 w-4" />
                  </span>
                  <h2 className="text-2xl font-bold text-white font-mono">TỰ ĐỘNG CHIA TÁCH VÀ ĐIỀU PHỐI SONG SONG</h2>
                </div>
                <p className="text-xs text-gray-400 max-w-3xl">
                  Nhập một yêu cầu kỹ thuật phức tạp bên dưới. Hệ thống sẽ sử dụng LLM để tự động phân rã yêu cầu thành các bước nhỏ độc lập, 
                  phân tích sự phụ thuộc giữa các công việc, phân bổ chúng cho các Agent chuyên biệt, và thực thi song song nhằm tối ưu hóa độ trễ (latency).
                </p>
              </div>

              {/* Form Configurator */}
              <div className="rounded-2xl border border-white/5 bg-[#131a2c]/50 p-6 space-y-6">
                <form onSubmit={handleRunParallelDecomposer} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Yêu cầu phức tạp cần thực hiện</label>
                    <textarea 
                      value={taskInput}
                      onChange={(e) => setTaskInput(e.target.value)}
                      placeholder="Nhập yêu cầu cần thực hiện..."
                      disabled={isExecutingTasks}
                      className="w-full h-24 rounded-xl border border-white/10 bg-black/20 p-4 text-sm text-white placeholder-gray-600 focus:border-indigo-500 focus:outline-none resize-none"
                    />
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
                    <div className="flex items-center space-x-6">
                      {/* Max Workers Select */}
                      <div className="space-y-1">
                        <span className="block text-[9px] font-bold uppercase tracking-wider text-gray-400">Số luồng chạy song song (Max Workers)</span>
                        <div className="flex items-center space-x-2 mt-1">
                          {[2, 4, 6, 8].map(w => (
                            <button
                              key={w}
                              type="button"
                              onClick={() => setMaxWorkers(w)}
                              disabled={isExecutingTasks}
                              className={`h-8 w-10 text-xs font-bold rounded-lg border transition ${
                                maxWorkers === w 
                                  ? 'bg-indigo-600/30 border-indigo-500/50 text-white font-mono' 
                                  : 'bg-black/20 border-white/5 text-gray-500 hover:border-white/10 hover:text-white'
                              }`}
                            >
                              {w}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Optimize Plan Toggle */}
                      <div className="space-y-1">
                        <span className="block text-[9px] font-bold uppercase tracking-wider text-gray-400">Tối ưu hóa sơ đồ đường găng</span>
                        <label className="relative inline-flex items-center cursor-pointer mt-1">
                          <input 
                            type="checkbox" 
                            checked={optimizePlan} 
                            onChange={(e) => setOptimizePlan(e.target.checked)}
                            disabled={isExecutingTasks}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-black/40 rounded-full peer peer-focus:ring-0 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-gray-400 after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600 peer-checked:after:bg-white"></div>
                          <span className="ml-2 text-xs text-gray-300">Đã kích hoạt</span>
                        </label>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isExecutingTasks || !taskInput.trim()}
                      className="flex items-center space-x-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-500 transition"
                    >
                      {isExecutingTasks ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                      <span>{isExecutingTasks ? `Đang xử lý... (${executionTime}s)` : 'Phân tách và chạy song song'}</span>
                    </button>
                  </div>
                </form>
              </div>

              {/* Status Board / Visualizer */}
              {decomposition && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  
                  {/* Left & Middle: Parallel lanes & subtasks */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="rounded-2xl border border-white/5 bg-[#131a2c]/50 p-6 space-y-6">
                      <div className="flex items-center justify-between border-b border-white/5 pb-4">
                        <div className="flex items-center space-x-2">
                          <Terminal className="h-5 w-5 text-indigo-400" />
                          <h3 className="font-bold text-white font-mono uppercase text-sm">Sơ đồ điều phối luồng song song</h3>
                        </div>
                        <span className="text-[10px] font-mono rounded bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 text-indigo-400">
                          Chiến lược: {decomposition.decomposition_strategy || "Topological Execution"}
                        </span>
                      </div>

                      {/* Render Parallel Groups */}
                      <div className="space-y-8 relative before:absolute before:left-4 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/5">
                        {decomposition.parallel_groups?.map((group: string[], gIdx: number) => (
                          <div key={gIdx} className="relative pl-8 space-y-3">
                            {/* Group Marker */}
                            <div className="absolute left-2.5 top-0 flex h-3.5 w-3.5 -translate-x-1/2 items-center justify-center rounded-full bg-[#0b0f19] border border-white/20">
                              <span className="h-1.5 w-1.5 rounded-full bg-indigo-500"></span>
                            </div>

                            <div className="flex items-center justify-between">
                              <h4 className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 font-mono">
                                Nhóm chạy song song #{gIdx + 1}
                              </h4>
                              <span className="text-[9px] text-gray-500 font-mono">
                                ({group.length} tác vụ con độc lập)
                              </span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {group.map(tid => {
                                const subtask = decomposition.subtasks?.find((t: any) => t.id === tid);
                                if (!subtask) return null;
                                
                                const state = taskStatuses[tid] || { status: "pending", error: null };
                                
                                // Dynamic UI states based on execution status
                                let statusBorder = "border-white/5 bg-[#131a2c]/40 hover:border-white/10";
                                let statusIcon = <div className="h-2 w-2 rounded-full bg-gray-500"></div>;
                                
                                if (state.status === "running") {
                                  statusBorder = "border-indigo-500/40 bg-indigo-950/10 shadow-lg shadow-indigo-500/5 animate-pulse";
                                  statusIcon = <RefreshCw className="h-3 w-3 text-indigo-400 animate-spin" />;
                                } else if (state.status === "completed") {
                                  statusBorder = "border-emerald-500/30 bg-emerald-950/5 hover:border-emerald-500/50 shadow-md";
                                  statusIcon = <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />;
                                } else if (state.status === "failed" || state.status === "timeout") {
                                  statusBorder = "border-red-500/30 bg-red-950/5 hover:border-red-500/50";
                                  statusIcon = <AlertCircle className="h-3.5 w-3.5 text-red-400" />;
                                }
                                
                                // Agent color mapper
                                let agentBadge = "bg-gray-500/10 border-gray-500/20 text-gray-400";
                                if (subtask.agent_type === "retriever") {
                                  agentBadge = "bg-cyan-500/10 border-cyan-500/20 text-cyan-400";
                                } else if (subtask.agent_type === "generator") {
                                  agentBadge = "bg-yellow-500/10 border-yellow-500/20 text-yellow-400";
                                } else if (subtask.agent_type === "critic") {
                                  agentBadge = "bg-pink-500/10 border-pink-500/20 text-pink-400";
                                } else if (subtask.agent_type === "analyzer") {
                                  agentBadge = "bg-purple-500/10 border-purple-500/20 text-purple-400";
                                }

                                return (
                                  <div 
                                    key={tid}
                                    onClick={() => setSelectedTaskDetails({ id: tid, title: subtask.title, ...state })}
                                    className={`rounded-xl border p-4 space-y-3 cursor-pointer transition ${statusBorder}`}
                                  >
                                    <div className="flex items-start justify-between space-x-2">
                                      <h5 className="text-xs font-semibold text-white leading-snug">{subtask.title}</h5>
                                      <span className="flex-shrink-0 mt-0.5">{statusIcon}</span>
                                    </div>
                                    <p className="text-[10px] text-gray-400 line-clamp-2">{subtask.description}</p>
                                    
                                    <div className="flex items-center justify-between pt-1 text-[9px] font-mono">
                                      <span className={`rounded border px-2 py-0.5 font-bold uppercase ${agentBadge}`}>
                                        {subtask.agent_type}
                                      </span>
                                      <span className="text-gray-500">
                                        Dự kiến: <strong>{subtask.estimated_duration_sec}s</strong>
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right: Metrics & Output preview */}
                  <div className="space-y-6">
                    
                    {/* Performance Card */}
                    <div className="rounded-2xl border border-white/5 bg-[#131a2c]/50 p-6 space-y-5">
                      <div className="flex items-center space-x-2 text-indigo-400">
                        <TrendingUp className="h-5 w-5" />
                        <h3 className="font-bold text-white font-mono uppercase text-sm">Hiệu suất luồng song song</h3>
                      </div>

                      {/* Speedup Display */}
                      <div className="text-center bg-black/20 rounded-2xl p-6 border border-white/5 space-y-2">
                        <div className="text-xs text-indigo-400 font-bold tracking-wider uppercase font-mono">Hệ số tăng tốc (Speedup)</div>
                        {executionResult ? (
                          <>
                            <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 font-mono animate-pulse">
                              {executionResult.metrics.actual_speedup_factor}x Faster
                            </div>
                            <div className="text-[10px] text-gray-400">Triển khai song song đạt hiệu quả vượt trội!</div>
                          </>
                        ) : decomposition.estimated_speedup_factor ? (
                          <>
                            <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 font-mono">
                              {decomposition.estimated_speedup_factor}x Speedup
                            </div>
                            <div className="text-[10px] text-gray-500">Hệ số lý thuyết tính theo sơ đồ đường găng.</div>
                          </>
                        ) : (
                          <>
                            <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 font-mono">
                              1.0x Speedup
                            </div>
                            <div className="text-[10px] text-gray-500 font-mono">Đang tính toán sơ đồ đường găng...</div>
                          </>
                        )}
                      </div>

                      {/* Latency Breakdown */}
                      <div className="space-y-3 font-mono text-xs">
                        <div className="flex justify-between items-center py-2 border-b border-white/5">
                          <span className="text-gray-400">Sequential Latency:</span>
                          <span className="font-bold text-white">
                            {decomposition.subtasks?.reduce((sum: number, t: any) => sum + t.estimated_duration_sec, 0).toFixed(1)}s
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-white/5">
                          <span className="text-gray-400">Parallelized Duration:</span>
                          <span className="font-bold text-cyan-400">
                            {executionResult 
                              ? `${executionResult.metrics.total_execution_time_sec}s` 
                              : `~${decomposition.estimated_total_time_sec.toFixed(1)}s`}
                          </span>
                        </div>
                        {executionResult && (
                          <div className="flex justify-between items-center py-2 border-b border-white/5">
                            <span className="text-gray-400">Efficiency Ratio:</span>
                            <span className="font-bold text-emerald-400">
                              {((1 - (executionResult.metrics.total_execution_time_sec / decomposition.subtasks?.reduce((sum: number, t: any) => sum + t.estimated_duration_sec, 0))) * 100).toFixed(1)}% time saved
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Database Indicator */}
                      <div className="rounded-xl bg-indigo-950/20 border border-indigo-500/20 p-4 text-[10px] leading-relaxed text-indigo-400 flex items-start space-x-2">
                        <span className="mt-0.5">💡</span>
                        <span>
                          <strong>Đã đồng bộ cơ sở dữ liệu:</strong> Toàn bộ {decomposition.subtasks?.length} công việc đã tự động lưu vào SQLite Task Manager. Bạn có thể mở CLI hoặc DB Viewer để xem.
                        </span>
                      </div>
                    </div>

                    {/* Output Viewer Card */}
                    <div className="rounded-2xl border border-white/5 bg-[#131a2c]/50 p-6 space-y-4">
                      <h3 className="font-bold text-white font-mono uppercase text-sm border-b border-white/5 pb-3">
                        🔍 Chi tiết kết quả tác vụ
                      </h3>
                      
                      {selectedTaskDetails ? (
                        <div className="space-y-3">
                          <div>
                            <h4 className="text-xs font-bold text-indigo-400">{selectedTaskDetails.title}</h4>
                            <span className="text-[9px] text-gray-500 font-mono">ID: {selectedTaskDetails.id}</span>
                          </div>
                          
                          <div className="border-t border-white/5 pt-2">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Kết quả đầu ra:</span>
                            {selectedTaskDetails.status === "completed" ? (
                              <div className="mt-1.5 text-xs text-gray-300 bg-black/45 p-4 rounded-xl border border-white/5 max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed font-mono">
                                {typeof selectedTaskDetails.result === 'object' 
                                  ? JSON.stringify(selectedTaskDetails.result, null, 2) 
                                  : selectedTaskDetails.result}
                              </div>
                            ) : selectedTaskDetails.status === "running" ? (
                              <div className="mt-1.5 flex h-24 items-center justify-center rounded-xl bg-black/25 text-xs text-indigo-400 font-mono animate-pulse">
                                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                                Đang xử lý...
                              </div>
                            ) : selectedTaskDetails.status === "failed" ? (
                              <div className="mt-1.5 text-xs text-red-400 bg-red-950/20 p-4 rounded-xl border border-red-500/20 whitespace-pre-wrap font-mono">
                                Lỗi thực thi: {selectedTaskDetails.error}
                              </div>
                            ) : (
                              <div className="mt-1.5 flex h-24 items-center justify-center rounded-xl bg-black/25 text-xs text-gray-600 font-mono">
                                Đang chờ luồng chạy...
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="flex h-36 flex-col items-center justify-center text-center text-gray-500 bg-black/10 rounded-xl border border-dashed border-white/10 p-4">
                          <HelpCircle className="h-6 w-6 text-gray-600 mb-1" />
                          <p className="text-xs">Click vào bất kỳ thẻ công việc con nào ở bên để xem chi tiết kết quả trả về của Agent.</p>
                        </div>
                      )}
                    </div>

                  </div>

                </div>
              )}

            </div>
          </div>
        )}

      </main>
    </div>
  )
}
