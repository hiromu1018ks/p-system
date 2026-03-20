import { useState } from 'react';
import { uploadFile } from '../api/files';

export default function FileUploader({ relatedType, relatedId, fileType, onUploaded }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      await uploadFile(relatedType, relatedId, fileType || 'other', file);
      e.target.value = '';
      if (onUploaded) onUploaded();
    } catch (err) {
      setError(err.message || 'アップロードに失敗しました');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ marginTop: 12 }}>
      <label style={{
        display: 'inline-block',
        padding: '6px 16px',
        background: '#2b6cb0',
        color: '#fff',
        borderRadius: 4,
        cursor: uploading ? 'not-allowed' : 'pointer',
        opacity: uploading ? 0.6 : 1,
      }}>
        {uploading ? 'アップロード中...' : 'ファイルを追加'}
        <input
          type="file"
          style={{ display: 'none' }}
          onChange={handleUpload}
          disabled={uploading}
        />
      </label>
      {error && <p style={{ color: '#e53e3e', fontSize: 13, marginTop: 4 }}>{error}</p>}
    </div>
  );
}
