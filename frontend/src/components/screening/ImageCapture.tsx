import { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Upload, Camera, X, RotateCcw } from 'lucide-react';

interface ImageCaptureProps {
  imagePreview: string | null;
  onImageSelect: (file: File | null, preview: string | null) => void;
  onSubmit: () => void;
  onSkip: () => void;
  onBack: () => void;
  isLoading: boolean;
}

export function ImageCapture({
  imagePreview,
  onImageSelect,
  onSubmit,
  onSkip,
  onBack,
  isLoading,
}: ImageCaptureProps) {
  const [mode, setMode] = useState<'upload' | 'camera' | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        onImageSelect(file, reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, [onImageSelect]);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: 640, height: 480 }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
        setMode('camera');
      }
    } catch (err) {
      console.error('Camera access denied:', err);
      alert('Unable to access camera. Please allow camera permissions or upload an image instead.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const captureImage = useCallback(() => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], 'captured-image.jpg', { type: 'image/jpeg' });
            const dataUrl = canvas.toDataURL('image/jpeg');
            onImageSelect(file, dataUrl);
            stopCamera();
          }
        }, 'image/jpeg', 0.9);
      }
    }
  }, [onImageSelect, stopCamera]);

  const clearImage = useCallback(() => {
    onImageSelect(null, null);
    setMode(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onImageSelect]);

  return (
    <div className="space-y-8 animate-slide-up">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Facial Image Analysis</h2>
        <p className="text-muted-foreground text-sm">
          Upload or capture a frontal face image for CNN-based analysis with explainable AI visualizations.
        </p>
      </div>

      {!imagePreview ? (
        <div className="space-y-6">
          {/* Mode selection */}
          {!mode && (
            <div className="grid md:grid-cols-2 gap-4">
              <button
                onClick={() => {
                  setMode('upload');
                  fileInputRef.current?.click();
                }}
                className="upload-zone flex flex-col items-center gap-3 py-12"
              >
                <Upload className="w-10 h-10 text-muted-foreground" />
                <div>
                  <p className="font-medium">Upload Image</p>
                  <p className="text-sm text-muted-foreground">Select from device</p>
                </div>
              </button>
              <button
                onClick={startCamera}
                className="upload-zone flex flex-col items-center gap-3 py-12"
              >
                <Camera className="w-10 h-10 text-muted-foreground" />
                <div>
                  <p className="font-medium">Take Photo</p>
                  <p className="text-sm text-muted-foreground">Use camera</p>
                </div>
              </button>
            </div>
          )}

          {/* Camera view */}
          {mode === 'camera' && isStreaming && (
            <div className="space-y-4">
              <div className="relative rounded-lg overflow-hidden bg-black aspect-[4/3] max-w-lg mx-auto">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 border-2 border-dashed border-white/30 m-8 rounded-lg pointer-events-none" />
              </div>
              <div className="flex justify-center gap-3">
                <Button variant="outline" onClick={() => { stopCamera(); setMode(null); }}>
                  Cancel
                </Button>
                <Button onClick={captureImage}>
                  Capture
                </Button>
              </div>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
          <canvas ref={canvasRef} className="hidden" />

          {/* Guidelines */}
          <div className="bg-accent/50 rounded-lg p-4 space-y-2">
            <p className="font-medium text-sm">Image Guidelines</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Frontal face view with neutral expression</li>
              <li>• Good lighting, avoid shadows on face</li>
              <li>• Face should be clearly visible and unobstructed</li>
              <li>• Image should be in focus</li>
            </ul>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Image preview */}
          <div className="relative max-w-lg mx-auto">
            <img
              src={imagePreview}
              alt="Uploaded face"
              className="w-full rounded-lg border border-border"
            />
            <button
              onClick={clearImage}
              className="absolute top-2 right-2 p-2 bg-background/90 rounded-full border border-border hover:bg-background transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex justify-center">
            <Button variant="outline" onClick={clearImage} className="gap-2">
              <RotateCcw className="w-4 h-4" />
              Choose Different Image
            </Button>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between pt-4">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={onSkip}>
            Skip Image Analysis
          </Button>
          <Button onClick={onSubmit} disabled={!imagePreview || isLoading} size="lg">
            {isLoading ? 'Analyzing...' : 'Analyze Image'}
          </Button>
        </div>
      </div>
    </div>
  );
}
