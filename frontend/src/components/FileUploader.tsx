import { useRef, useState, useEffect } from 'react'
import { apiClient } from '../services/api'

interface Props {
  /** Compact mode: renders just a paperclip icon button (for use in InputArea) */
  compact?: boolean
}

export default function FileUploader({ compact = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  // Auto-dismiss notification after 3s
  useEffect(() => {
    if (!msg) return
    const t = setTimeout(() => setMsg(null), 3000)
    return () => clearTimeout(t)
  }, [msg])

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setUploading(true)
    setMsg(null)
    try {
      const result = await apiClient.uploadFiles(files)
      setMsg({ type: 'ok', text: `Đã tải ${result.files.length} tệp` })
    } catch (err: any) {
      const text = err.response?.data?.error?.message || err.message || 'Upload thất bại'
      setMsg({ type: 'err', text })
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const hiddenInput = (
    <input
      ref={inputRef}
      type="file"
      accept=".pdf,.docx,.txt,.md"
      multiple
      className="hidden"
      onChange={(e) => handleFiles(e.target.files)}
    />
  )

  /* ── Compact mode (paperclip icon inside InputArea) ── */
  if (compact) {
    return (
      <div className="relative flex items-center">
        {hiddenInput}
        <button
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          title="Đính kèm tệp (PDF, DOCX, TXT, MD)"
          className="p-1.5 rounded-lg text-[#8e8ea0] hover:text-[#ececf1] hover:bg-white/10 disabled:opacity-40 transition-colors"
        >
          {uploading ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="animate-spin">
              <circle cx="12" cy="12" r="10" strokeOpacity=".25"/>
              <path d="M12 2a10 10 0 0 1 10 10" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          )}
        </button>
        {msg && (
          <div className={`absolute bottom-full left-0 mb-2 px-2 py-1 rounded-md text-xs whitespace-nowrap shadow-lg ${msg.type === 'ok' ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`}>
            {msg.text}
          </div>
        )}
      </div>
    )
  }

  /* ── Full mode (for sidebar document section) ── */
  return (
    <div className="flex flex-col gap-1">
      {hiddenInput}
      <button
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#8e8ea0] hover:text-[#ececf1] hover:bg-white/5 disabled:opacity-50 transition-colors"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
        </svg>
        <span>{uploading ? 'Đang tải lên...' : 'Tải tệp lên'}</span>
      </button>
      {msg && (
        <p className={`px-3 text-xs ${msg.type === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
          {msg.text}
        </p>
      )}
    </div>
  )
}
