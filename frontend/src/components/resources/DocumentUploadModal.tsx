import React, { useState, useRef } from "react";
import { UploadCloud, FileText, X, AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { documentsApi, type DocumentResponse } from "@/api/documents";

interface DocumentUploadModalProps {
  examTemplateId?: string;
  topicId?: string;
  token?: string;
  onClose: () => void;
  onSuccess: (document: DocumentResponse) => void;
}

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB
const ALLOWED_EXTENSIONS = [".pdf", ".md", ".txt"];

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  examTemplateId,
  topicId,
  token,
  onClose,
  onSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelection = (file: File) => {
    setError(null);
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file format (${ext}). Allowed formats: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError(`File size exceeds 25 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      return;
    }
    setSelectedFile(file);
    if (!title) {
      // Auto-populate human-friendly title from filename
      const baseName = file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
      setTitle(baseName.charAt(0).toUpperCase() + baseName.slice(1));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select a file to upload.");
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append("file", selectedFile);
      if (title.trim()) formData.append("title", title.trim());
      if (topicId) formData.append("topic_id", topicId);
      if (examTemplateId) formData.append("exam_template_id", examTemplateId);

      const uploadedDoc = await documentsApi.uploadDocument(formData, token);
      setSuccess(true);

      setTimeout(() => {
        onSuccess(uploadedDoc);
        onClose();
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload and chunk source document");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div
        className="w-full max-w-lg bg-card border border-border rounded-2xl shadow-2xl overflow-hidden"
        role="dialog"
        aria-label="Upload Curriculum Source Document"
      >
        {/* Header */}
        <div className="p-5 border-b border-border bg-muted/30 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <UploadCloud className="w-4.5 h-4.5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">Upload Source Material</h2>
              <p className="text-xs text-muted-foreground">PDF, Markdown or TXT with LaTeX preservation</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close"
            className="hover:bg-muted"
            disabled={uploading}
          >
            <X className="w-5 h-5 text-muted-foreground" />
          </Button>
        </div>

        {/* Body Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3.5 bg-destructive/10 border border-destructive/20 rounded-xl flex items-center gap-2.5 text-destructive text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3.5 bg-emerald-950/30 border border-emerald-800/40 rounded-xl flex items-center gap-2.5 text-emerald-400 text-xs">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>Document uploaded and segmented successfully!</span>
            </div>
          )}

          {/* Drag & Drop Upload Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
              isDragging
                ? "border-primary bg-primary/5 scale-[1.01]"
                : selectedFile
                ? "border-emerald-500/50 bg-emerald-950/10"
                : "border-border hover:border-primary/50 bg-muted/10"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".pdf,.md,.txt"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileSelection(e.target.files[0]);
                }
              }}
            />

            {selectedFile ? (
              <div className="space-y-1.5 flex flex-col items-center">
                <FileText className="w-9 h-9 text-emerald-400" />
                <p className="text-sm font-medium text-foreground truncate max-w-xs">{selectedFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Click to replace
                </p>
              </div>
            ) : (
              <div className="space-y-2 flex flex-col items-center">
                <UploadCloud className="w-10 h-10 text-muted-foreground/60" />
                <p className="text-sm font-medium text-foreground">
                  Drag and drop your file here, or <span className="text-primary underline">browse</span>
                </p>
                <p className="text-xs text-muted-foreground">Supports PDF, Markdown, and TXT (Max 25 MB)</p>
              </div>
            )}
          </div>

          {/* Document Title Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Document Title</label>
            <Input
              type="text"
              placeholder="e.g. University Physics: Mechanics & Vectors"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={uploading}
              className="bg-background text-sm"
            />
          </div>

          {/* Ingestion Info Box */}
          <div className="p-3 bg-muted/30 border border-border/60 rounded-xl text-xs text-muted-foreground flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <p>
              Uploaded documents are parsed server-side into semantic chunks, protecting mathematical LaTeX expressions
              and heading breadcrumbs for grounded RAG tutoring.
            </p>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-border/40">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={uploading}>
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={!selectedFile || uploading || success}
              className="gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Chunking & Segmenting...
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  Upload & Segment
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
