import React, { useState } from 'react';
import { ingestFile } from '../lib/aiApi';

interface DocumentUploaderProps {
  sessionId: string;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ sessionId }) => {
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setUploadProgress(0);
    setUploadStatus(null);
    setErrorMessage(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication token not found. Please log in.');
      }

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${process.env.REACT_APP_API_BASE_URL}/api/documents/upload`, true);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.setRequestHeader('Accept', 'application/json');

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const response = JSON.parse(xhr.responseText);
            setUploadStatus(`✓ Indexed ${response.chunks_indexed} chunks`);
          } else {
            throw new Error('Unexpected response format from server.');
          }
        } else {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const errorResponse = JSON.parse(xhr.responseText);
            throw new Error(errorResponse.message || 'An error occurred during upload.');
          } else {
            throw new Error('An error occurred during upload.');
          }
        }
      };

      xhr.onerror = () => {
        throw new Error('Network error occurred during file upload.');
      };

      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      xhr.send(formData);
    } catch (error: any) {
      setErrorMessage(error.message || 'An unexpected error occurred.');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(file.type)) {
        handleFileUpload(file);
      } else {
        setErrorMessage('Unsupported file type. Please upload a .pdf, .docx, .xlsx, or .xls file.');
      }
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(file.type)) {
        handleFileUpload(file);
      } else {
        setErrorMessage('Unsupported file type. Please upload a .pdf, .docx, .xlsx, or .xls file.');
      }
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  return (
    <div className="p-4 border border-dashed border-gray-300 rounded-lg">
      <div
        className="flex flex-col items-center justify-center p-6 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <p className="text-gray-600">Drag and drop your file here, or</p>
        <label className="text-blue-500 underline cursor-pointer">
          <input
            type="file"
            className="hidden"
            accept=".pdf,.docx,.xlsx,.xls"
            onChange={handleFileSelect}
          />
          browse files
        </label>
      </div>
      {uploadProgress > 0 && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-500 h-2.5 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">{uploadProgress}% uploaded</p>
        </div>
      )}
      {uploadStatus && (
        <div className="mt-4 text-green-600 font-semibold">{uploadStatus}</div>
      )}
      {errorMessage && (
        <div className="mt-4 text-red-600 font-semibold">{errorMessage}</div>
      )}
    </div>
  );
};

export default DocumentUploader;