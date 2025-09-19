"use client";

import React, { useCallback, useState } from "react";
import { Upload, File, X, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { Progress } from "./progress";
import { Alert, AlertDescription } from "./alert";

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  onUploadProgress?: (progress: number) => void;
  onUploadComplete?: () => void;
  onUploadError?: (error: string) => void;
  accept?: string;
  multiple?: boolean;
  maxFiles?: number;
  maxSize?: number; // in MB
  className?: string;
  disabled?: boolean;
  description?: string;
  allowFolders?: boolean; // New prop for folder upload
}

interface FileWithProgress {
  file: File;
  progress: number;
  status: "pending" | "uploading" | "completed" | "error";
  error?: string;
}

export function FileUpload({
  onFilesSelected,
  onUploadProgress,
  onUploadComplete,
  onUploadError,
  accept = ".csv,.txt",
  multiple = false,
  maxFiles = 50,
  maxSize = 100, // 100MB default
  className,
  disabled = false,
  description,
  allowFolders = false,
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const validateFile = (file: File): string | null => {
    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSize) {
      return `File size exceeds ${maxSize}MB limit`;
    }

    // Check file type
    if (accept) {
      const acceptedTypes = accept.split(",").map(type => type.trim());
      const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
      if (!acceptedTypes.includes(fileExtension)) {
        return `File type not supported. Accepted: ${accept}`;
      }
    }

    return null;
  };

  const handleFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    
    // Check max files limit
    if (!multiple && fileArray.length > 1) {
      onUploadError?.("Only one file is allowed");
      return;
    }
    
    if (maxFiles > 0 && files.length + fileArray.length > maxFiles) {
      onUploadError?.(`Maximum ${maxFiles} files allowed`);
      return;
    }

    // Validate each file
    const validatedFiles: FileWithProgress[] = [];
    const errors: string[] = [];

    fileArray.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        errors.push(`${file.name}: ${error}`);
      } else {
        validatedFiles.push({
          file,
          progress: 0,
          status: "pending",
        });
      }
    });

    if (errors.length > 0) {
      onUploadError?.(errors.join("; "));
      return;
    }

    // Add valid files
    const updatedFiles = multiple ? [...files, ...validatedFiles] : validatedFiles;
    setFiles(updatedFiles);
    onFilesSelected(validatedFiles.map(f => f.file));
  }, [files, multiple, maxFiles, maxSize, accept, onFilesSelected, onUploadError]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled) return;
    
    const droppedFiles = e.dataTransfer.files;
    handleFiles(droppedFiles);
  }, [disabled, handleFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    onFilesSelected(updatedFiles.map(f => f.file));
  };

  const clearAllFiles = () => {
    setFiles([]);
    onFilesSelected([]);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split(".").pop()?.toLowerCase();
    return <File className="w-4 h-4" />;
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drag and Drop Area */}
      <div
        className={cn(
          "relative border-2 border-dashed rounded-lg p-6 transition-colors",
          isDragOver 
            ? "border-[#C41230] bg-red-50" 
            : "border-gray-300 hover:border-gray-400",
          disabled && "opacity-50 cursor-not-allowed"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleFileInput}
          disabled={disabled}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          {...(allowFolders ? { webkitdirectory: "", directory: "" } : {})}
        />
        
        <div className="flex flex-col items-center justify-center text-center">
          <Upload className={cn(
            "w-8 h-8 mb-2",
            isDragOver ? "text-[#C41230]" : "text-gray-400"
          )} />
          <p className="text-sm font-medium text-gray-700">
            {isDragOver 
              ? `Drop ${allowFolders ? "folder" : "files"} here` 
              : `Drag and drop ${allowFolders ? "a folder" : "files"} here`
            }
          </p>
          <p className="text-xs text-gray-500 mt-1">
            or click to browse {allowFolders ? "folder" : "files"}
          </p>
          {description && (
            <p className="text-xs text-gray-400 mt-2">{description}</p>
          )}
          <div className="text-xs text-gray-400 mt-2">
            Max size: {maxSize}MB • Formats: {accept}
            {multiple && maxFiles > 0 && ` • Max files: ${maxFiles}`}
            {allowFolders && " • Folder upload supported"}
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">
              Selected Files ({files.length})
            </h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFiles}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Clear All
            </Button>
          </div>
          
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {files.map((fileWithProgress, index) => (
              <div
                key={`${fileWithProgress.file.name}-${index}`}
                className="flex items-center space-x-3 p-2 bg-gray-50 rounded border"
              >
                <div className="flex-shrink-0">
                  {fileWithProgress.status === "completed" ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : fileWithProgress.status === "error" ? (
                    <AlertCircle className="w-4 h-4 text-red-500" />
                  ) : (
                    getFileIcon(fileWithProgress.file.name)
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700 truncate">
                    {fileWithProgress.file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(fileWithProgress.file.size)}
                  </p>
                  
                  {fileWithProgress.status === "uploading" && (
                    <Progress 
                      value={fileWithProgress.progress} 
                      className="h-1 mt-1" 
                    />
                  )}
                  
                  {fileWithProgress.error && (
                    <p className="text-xs text-red-500 mt-1">
                      {fileWithProgress.error}
                    </p>
                  )}
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  disabled={isUploading}
                  className="flex-shrink-0 h-6 w-6 p-0"
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 