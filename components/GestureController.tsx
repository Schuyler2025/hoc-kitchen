import React, { useEffect, useRef, useState, useCallback } from 'react';
import { HandLandmarkerResult } from '../types';

interface GestureControllerProps {
  onZoomChange: (scale: number) => void;
  isActive: boolean;
}

// Global declaration for MediaPipe loaded via CDN
declare global {
  interface Window {
    vision: any;
  }
}

const GestureController: React.FC<GestureControllerProps> = ({ onZoomChange, isActive }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [handLandmarker, setHandLandmarker] = useState<any>(null);
  const requestRef = useRef<number>(0);
  const lastVideoTimeRef = useRef<number>(-1);

  // Initialize MediaPipe HandLandmarker
  useEffect(() => {
    const initMediaPipe = async () => {
      try {
        const vision = await window.vision.FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
        );
        const landmarker = await window.vision.HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`,
            delegate: "GPU"
          },
          runningMode: "VIDEO",
          numHands: 1
        });
        setHandLandmarker(landmarker);
        console.log("HandLandmarker loaded");
      } catch (err) {
        console.error("Failed to load MediaPipe", err);
      }
    };
    initMediaPipe();
  }, []);

  // Setup Camera
  useEffect(() => {
    if (!isActive || !handLandmarker) return;

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: "user" }
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.addEventListener("loadeddata", () => {
            setIsCameraReady(true);
          });
        }
      } catch (err) {
        console.error("Camera access denied", err);
      }
    };

    startCamera();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [isActive, handLandmarker]);

  // Process Frames
  const predictWebcam = useCallback(() => {
    if (handLandmarker && videoRef.current && isCameraReady) {
      const nowInMs = Date.now();
      if (videoRef.current.currentTime !== lastVideoTimeRef.current) {
        lastVideoTimeRef.current = videoRef.current.currentTime;
        const results = handLandmarker.detectForVideo(videoRef.current, nowInMs) as HandLandmarkerResult;
        
        if (results.landmarks && results.landmarks.length > 0) {
          const landmarks = results.landmarks[0];
          // Thumb tip is 4, Index tip is 8
          const thumbTip = landmarks[4];
          const indexTip = landmarks[8];
          
          // Calculate Euclidean distance
          const distance = Math.sqrt(
            Math.pow(thumbTip.x - indexTip.x, 2) + 
            Math.pow(thumbTip.y - indexTip.y, 2)
          );

          // Map distance to zoom scale
          // Raw distance usually ranges from 0.02 (touching) to 0.2+ (open)
          // We want to map this to scale 1.0 to 3.0
          // Simple linear mapping:
          const minDist = 0.03;
          const maxDist = 0.20;
          
          let normalized = (distance - minDist) / (maxDist - minDist);
          normalized = Math.max(0, Math.min(1, normalized));
          
          // Invert logic: Pinch (small distance) = Zoom Out? Or Spread = Zoom In?
          // Usually spread = zoom in.
          // Let's do: Spread (large distance) = Zoom In (Seeing details)
          // Pinch (small distance) = Zoom Out (Overview)
          
          const targetScale = 1 + (normalized * 1.5); // Range 1.0 to 2.5
          
          onZoomChange(targetScale);
        }
      }
    }
    requestRef.current = requestAnimationFrame(predictWebcam);
  }, [handLandmarker, isCameraReady, onZoomChange]);

  useEffect(() => {
    if (isActive && isCameraReady) {
      requestRef.current = requestAnimationFrame(predictWebcam);
    } else {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    }
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [isActive, isCameraReady, predictWebcam]);

  if (!isActive) return null;

  return (
    <div className="fixed top-4 right-4 z-50 w-24 h-32 bg-black rounded-lg overflow-hidden border-2 border-green-400 shadow-lg opacity-80">
      <video 
        ref={videoRef} 
        autoPlay 
        playsInline 
        muted 
        className="w-full h-full object-cover transform scale-x-[-1]" // Mirror effect
      />
      <div className="absolute bottom-0 w-full bg-black/50 text-[10px] text-white text-center py-1">
        Air Gesture On
      </div>
    </div>
  );
};

export default GestureController;