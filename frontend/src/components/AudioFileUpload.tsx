import React, { useState, useCallback, useRef } from 'react';
import { Upload, FileAudio, X, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Progress } from './ui/progress';
import { useAudioEncoder, AudioUtils } from '../utils/audio-encoder';
import { logger } from '../utils/logger';

interface AudioFileUploadProps {
  userId: string;
  onAudioEncoded?: (encodedMessage: any) => void;
  onError?: (error: string) => void;
  maxFileSizeMB?: number;
  className?: string;
}

interface UploadState {
  file: File | null;
  isUploading: boolean;
  progress: number;
  error: string | null;
  success: boolean;
}

export function AudioFileUpload({ 
  userId, 
  onAudioEncoded, 
  onError,
  maxFileSizeMB = 10,
  className = ""
}: AudioFileUploadProps) {
  const audioEncoder = useAudioEncoder(userId);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    isUploading: false,
    progress: 0,
    error: null,
    success: false
  });

  const handleFileSelect = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Reset state
    setUploadState({
      file: null,
      isUploading: false,
      progress: 0,
      error: null,
      success: false
    });

    // Validate file
    if (!AudioUtils.isSupportedAudioFile(file)) {
      const error = "Unsupported audio format. Please use WAV, WebM, MP3, M4A, or OGG files.";
      setUploadState(prev => ({ ...prev, error }));
      onError?.(error);
      return;
    }

    if (!AudioUtils.validateFileSize(file, maxFileSizeMB)) {
      const error = `File too large. Maximum size is ${maxFileSizeMB}MB.`;
      setUploadState(prev => ({ ...prev, error }));
      onError?.(error);
      return;
    }

    setUploadState(prev => ({ ...prev, file, isUploading: true }));

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90)
        }));
      }, 100);

      // Encode the audio file
      const encodedMessage = await audioEncoder.encodeFile(file, {
        userId,
        isFinal: true
      });

      clearInterval(progressInterval);
      
      setUploadState(prev => ({
        ...prev,
        isUploading: false,
        progress: 100,
        success: true,
        error: null
      }));

      logger.info('audio', `File encoded successfully: ${file.name}`);
      onAudioEncoded?.(encodedMessage);

    } catch (error) {
      const errorMessage = `Failed to encode audio file: ${error}`;
      setUploadState(prev => ({
        ...prev,
        isUploading: false,
        progress: 0,
        error: errorMessage,
        success: false
      }));
      
      logger.error('audio', errorMessage);
      onError?.(errorMessage);
    }
  }, [audioEncoder, userId, maxFileSizeMB, onAudioEncoded, onError]);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && fileInputRef.current) {
      // Create a fake event to reuse handleFileSelect
      const fakeEvent = {
        target: { files: [file] }
      } as React.ChangeEvent<HTMLInputElement>;
      handleFileSelect(fakeEvent);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  }, []);

  const clearFile = useCallback(() => {
    setUploadState({
      file: null,
      isUploading: false,
      progress: 0,
      error: null,
      success: false
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const triggerFileSelect = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className={`w-full max-w-md ${className}`}>
      <Card className="p-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="text-center">
            <h3 className="text-lg font-semibold">Upload Audio File</h3>
            <p className="text-sm text-muted-foreground">
              Upload an audio file to send via WebSocket
            </p>
          </div>

          {/* Drop Zone */}
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${uploadState.isUploading 
                ? 'border-blue-300 bg-blue-50' 
                : uploadState.error 
                  ? 'border-red-300 bg-red-50' 
                  : uploadState.success 
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
              }
            `}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={triggerFileSelect}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            {uploadState.isUploading ? (
              <div className="space-y-2">
                <FileAudio className="w-12 h-12 mx-auto text-blue-500" />
                <p className="text-sm font-medium text-blue-700">Encoding...</p>
                <Progress value={uploadState.progress} className="w-full" />
                <p className="text-xs text-blue-600">{uploadState.progress}%</p>
              </div>
            ) : uploadState.error ? (
              <div className="space-y-2">
                <AlertCircle className="w-12 h-12 mx-auto text-red-500" />
                <p className="text-sm font-medium text-red-700">Upload Failed</p>
                <p className="text-xs text-red-600">{uploadState.error}</p>
              </div>
            ) : uploadState.success ? (
              <div className="space-y-2">
                <CheckCircle className="w-12 h-12 mx-auto text-green-500" />
                <p className="text-sm font-medium text-green-700">Upload Complete!</p>
                <p className="text-xs text-green-600">
                  {uploadState.file?.name} ({AudioUtils.formatFileSize(uploadState.file?.size || 0)})
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="w-12 h-12 mx-auto text-gray-400" />
                <p className="text-sm font-medium text-gray-700">
                  Drop audio file here or click to browse
                </p>
                <p className="text-xs text-gray-500">
                  Supports WAV, WebM, MP3, M4A, OGG (max {maxFileSizeMB}MB)
                </p>
              </div>
            )}
          </div>

          {/* File Info */}
          {uploadState.file && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileAudio className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {uploadState.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {AudioUtils.formatFileSize(uploadState.file.size)}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFile}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-2">
            <Button
              onClick={triggerFileSelect}
              disabled={uploadState.isUploading}
              className="flex-1"
            >
              <Upload className="w-4 h-4 mr-2" />
              {uploadState.file ? 'Choose Different File' : 'Select Audio File'}
            </Button>
            
            {uploadState.file && (
              <Button
                variant="outline"
                onClick={clearFile}
                disabled={uploadState.isUploading}
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Encoding Info */}
          {uploadState.success && uploadState.file && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <p className="text-sm text-green-700">
                  Ready to send via WebSocket
                </p>
              </div>
              <p className="text-xs text-green-600 mt-1">
                Session ID: {audioEncoder.getCurrentSessionId()}
              </p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
