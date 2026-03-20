import { useState, useEffect } from 'react'
import { getFiles, deleteFile, downloadFile } from '../api/files'
import FileUploader from './FileUploader'

export default function FileList({ relatedType, relatedId, showUpload }) {
  const [files, setFiles] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (!relatedId) return
    getFiles(relatedType, relatedId)
      .then(setFiles)
      .catch((err) => setError(err.message))
  }, [relatedType, relatedId])

  const handleDelete = async (fileId) => {
    if (!window.confirm('このファイルを削除しますか？')) return
    try {
      await deleteFile(fileId)
      setFiles((prev) => prev.filter((f) => f.id !== fileId))
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDownload = async (fileId) => {
    try {
      await downloadFile(fileId)
    } catch (err) {
      setError(err.message)
    }
  }

  const fetchFiles = () => {
    getFiles(relatedType, relatedId)
      .then(setFiles)
      .catch((err) => setError(err.message))
  }

  if (error) return <p style={{ color: 'red' }}>{error}</p>

  return (
    <div>
      {showUpload && (
        <FileUploader
          relatedType={relatedType}
          relatedId={relatedId}
          onUploaded={fetchFiles}
        />
      )}

      {!files.length ? (
        <p>添付ファイルはありません</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: 8, textAlign: 'left' }}>ファイル名</th>
              <th style={{ padding: 8, textAlign: 'left' }}>種別</th>
              <th style={{ padding: 8, textAlign: 'right' }}>サイズ</th>
              <th style={{ padding: 8, textAlign: 'center' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr key={file.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 8 }}>{file.original_filename}</td>
                <td style={{ padding: 8 }}>{file.file_type}</td>
                <td style={{ padding: 8, textAlign: 'right' }}>
                  {(file.file_size_bytes / 1024).toFixed(1)} KB
                </td>
                <td style={{ padding: 8, textAlign: 'center' }}>
                  <button
                    onClick={() => handleDownload(file.id)}
                    style={{ marginRight: 8, padding: '4px 8px', fontSize: 12 }}
                  >
                    ダウンロード
                  </button>
                  <button
                    onClick={() => handleDelete(file.id)}
                    style={{ padding: '4px 8px', fontSize: 12, background: '#e53e3e' }}
                  >
                    削除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
