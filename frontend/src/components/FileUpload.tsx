import { useState, useRef, useCallback } from 'react'

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>
  acceptedTypes?: string
  maxSizeMB?: number
  disabled?: boolean
  label?: string
}

export default function FileUpload({
  onUpload,
  acceptedTypes = '.pdf,.docx,.txt,.md,.csv,.json',
  maxSizeMB = 10,
  disabled = false,
  label = 'Upload file',
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(async (file: File) => {
    setError(null)
    setSuccess(null)

    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File size exceeds ${maxSizeMB}MB limit`)
      return
    }

    setUploading(true)
    setProgress(0)

    const interval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90))
    }, 100)

    try {
      await onUpload(file)
      setProgress(100)
      setSuccess(`Successfully uploaded ${file.name}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      clearInterval(interval)
      setUploading(false)
    }
  }, [onUpload, maxSizeMB])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled && !uploading) setIsDragging(true)
  }, [disabled, uploading])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (disabled || uploading) return

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFile(files[0])
    }
  }, [handleFile, disabled, uploading])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }, [handleFile])

  return (
    <div className="w-full">
      <div
        role="button"
        tabIndex={0}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer ${
          isDragging
            ? 'border-accent-400 bg-accent-500/10'
            : disabled
              ? 'border-titanium-700 bg-titanium-900/50 opacity-50 cursor-not-allowed'
              : 'border-titanium-600 hover:border-titanium-500 hover:bg-titanium-800/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click() }}
        aria-disabled={disabled || uploading}
      >
        <input
          ref={inputRef}
          type="file"
          accept={acceptedTypes}
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled || uploading}
          aria-label={label}
        />

        {uploading ? (
          <div className="space-y-3">
            <div className="w-10 h-10 mx-auto border-2 border-accent-400 border-t-transparent rounded-full animate-spin" />
            <div className="text-sm text-titanium-300">
              Uploading... {progress}%
            </div>
            <div className="w-full bg-titanium-700 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-accent-500 rounded-full transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <svg className="mx-auto h-12 w-12 text-titanium-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3" />
            </svg>
            <div>
              <span className="text-accent-400 font-medium">{label}</span>
              <span className="text-titanium-400 text-sm"> or drag and drop</span>
            </div>
            <p className="text-xs text-titanium-500">
              {acceptedTypes.replace(/\./g, '').replace(/,/g, ', ')} (max {maxSizeMB}MB)
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
          {error}
        </div>
      )}

      {success && (
        <div className="mt-3 p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-sm text-green-400">
          {success}
        </div>
      )}
    </div>
  )
}
