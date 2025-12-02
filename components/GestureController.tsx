import React, { useEffect, useRef, useState, useCallback } from 'react';
import { HandLandmarkerResult, GestureCallbacks } from '../types';

interface GestureControllerProps {
  isActive: boolean;
  callbacks: GestureCallbacks;
}

// Global declaration for MediaPipe
declare global {
  interface Window {
    vision: any;
  }
}

const GestureController: React.FC<GestureControllerProps> = ({ isActive, callbacks }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [handLandmarker, setHandLandmarker] = useState<any>(null);
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const requestRef = useRef<number>(0);
  const lastVideoTimeRef = useRef<number>(-1);

  // Gesture state tracking
  const gestureStateRef = useRef({
    lastGesture: '',
    gestureStartTime: 0,
    lastHandPosition: { x: 0, y: 0 },
    scrollVelocity: 0,
    zoomDistance: 0,
    gestureCooldown: 0,
    fistHoldStartTime: 0, // Track how long fist is held
    isFistStable: false    // Track if fist gesture is stable
  });

  // Initialize MediaPipe with offline support
  useEffect(() => {
    let landmarkerInstance: any = null;

    const initMediaPipe = async () => {
      try {
        // Try to load from local first, fallback to CDN
        const wasmPath = '/wasm';
        const modelPath = '/models/hand_landmarker.task';

        let FilesetResolver, HandLandmarker;

        // Try to load MediaPipe - local first, then CDN
        let loadedFromLocal = false;
        try {
          // Try local vision_bundle.js first
          const localModule = await import(/* @vite-ignore */ '/wasm/vision_bundle.js' as string);
          FilesetResolver = localModule.FilesetResolver;
          HandLandmarker = localModule.HandLandmarker;
          loadedFromLocal = true;
          console.log('✓ Loaded MediaPipe from local vision_bundle.js');
        } catch (localError) {
          console.log('Local vision_bundle.js not found, trying CDN...');
          // Fallback to CDN - import the package
          try {
            const moduleUrl = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0`;
            const module = await import(/* @vite-ignore */ moduleUrl);
            FilesetResolver = module.FilesetResolver;
            HandLandmarker = module.HandLandmarker;
            console.log('✓ Loaded MediaPipe from CDN');
          } catch (cdnError) {
            console.error('Failed to load MediaPipe from both local and CDN:', cdnError);
            throw cdnError;
          }
        }

        // Try to use local WASM files, fallback to CDN
        let vision;
        if (loadedFromLocal) {
          try {
            vision = await FilesetResolver.forVisionTasks(wasmPath);
            console.log('✓ Using local WASM files');
          } catch (e) {
            console.log('Local WASM files not found, using CDN WASM...');
            vision = await FilesetResolver.forVisionTasks(
              "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
            );
          }
        } else {
          // Already using CDN, use CDN WASM
          vision = await FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
          );
        }

        let landmarker;
        try {
          // Try local model first
          landmarker = await HandLandmarker.createFromOptions(vision, {
            baseOptions: {
              modelAssetPath: modelPath,
              delegate: "GPU",
            },
            runningMode: "VIDEO",
            numHands: 1,
          });
          console.log("HandLandmarker loaded from local files");
        } catch (localModelError) {
          console.log("Local model not found, using CDN fallback");
          // Fallback to CDN model
          landmarker = await HandLandmarker.createFromOptions(vision, {
            baseOptions: {
              modelAssetPath:
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
              delegate: "GPU",
            },
            runningMode: "VIDEO",
            numHands: 1,
          });
          console.log("HandLandmarker loaded from CDN");
        }

        setHandLandmarker(landmarker);
        setIsModelLoaded(true);
      } catch (err) {
        console.error("Failed to load MediaPipe:", err);
      }
    };

    if (isActive) {
      initMediaPipe();
    }

    return () => {
      if (landmarkerInstance) {
        landmarkerInstance.close?.();
      }
    };
  }, [isActive]);

  // Setup Camera
  useEffect(() => {
    if (!isActive || !isModelLoaded) return;

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: "user" }
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
  }, [isActive, isModelLoaded]);

  // Detect gestures from hand landmarks
  const detectGesture = useCallback((landmarks: { x: number; y: number; z: number }[]) => {
    const state = gestureStateRef.current;
    const now = Date.now();

    // Thumb tip (4), Index tip (8), Middle tip (12), Ring tip (16), Pinky tip (20)
    // Wrist (0)
    const thumbTip = landmarks[4];
    const indexTip = landmarks[8];
    const middleTip = landmarks[12];
    const ringTip = landmarks[16];
    const pinkyTip = landmarks[20];
    const wrist = landmarks[0];
    const middleMCP = landmarks[9]; // Middle finger MCP (knuckle)

    // Calculate hand center (palm position)
    const handCenter = {
      x: wrist.x,
      y: wrist.y
    };

    // Calculate distances
    const thumbIndexDist = Math.sqrt(
      Math.pow(thumbTip.x - indexTip.x, 2) +
      Math.pow(thumbTip.y - indexTip.y, 2)
    );

    const indexMiddleDist = Math.sqrt(
      Math.pow(indexTip.x - middleTip.x, 2) +
      Math.pow(indexTip.y - middleTip.y, 2)
    );

    // Check if fingers are extended
    const isThumbExtended = thumbTip.x < wrist.x; // Thumb to the left of wrist
    const isIndexExtended = indexTip.y < middleMCP.y; // Index tip above knuckle
    const isMiddleExtended = middleTip.y < middleMCP.y;
    const isRingExtended = ringTip.y < middleMCP.y;
    const isPinkyExtended = pinkyTip.y < middleMCP.y;

    const extendedFingers = [
      isThumbExtended,
      isIndexExtended,
      isMiddleExtended,
      isRingExtended,
      isPinkyExtended
    ].filter(Boolean).length;

    // Gesture cooldown to prevent rapid firing
    if (now - state.gestureCooldown < 300) {
      return;
    }

    // 1. POINTING UP/DOWN: Index finger extended, others closed (higher priority than zoom)
    // Check scroll gestures BEFORE zoom to prevent conflict
    if (isIndexExtended && !isMiddleExtended && !isRingExtended && !isPinkyExtended) {
      if (handCenter.y < state.lastHandPosition.y - 0.02) { // Very sensitive for scroll up
        // Hand moving up
        if (callbacks.onScroll) {
          callbacks.onScroll('up', 200); // Increased scroll amount
        }
        state.gestureCooldown = now;
        state.lastGesture = 'scroll_up';
        // Reset fist timer when doing other gestures
        state.fistHoldStartTime = 0;
        state.isFistStable = false;
        return;
      }
      if (handCenter.y > state.lastHandPosition.y + 0.02) { // Very sensitive for scroll down
        // Hand moving down
        if (callbacks.onScroll) {
          callbacks.onScroll('down', 200); // Increased scroll amount
        }
        state.gestureCooldown = now;
        state.lastGesture = 'scroll_down';
        // Reset fist timer when doing other gestures
        state.fistHoldStartTime = 0;
        state.isFistStable = false;
        return;
      }
    }

    // 2. PINCH/ZOOM: Thumb and index finger close together
    if (thumbIndexDist < 0.05) {
      // Pinch detected - zoom out
      if (callbacks.onZoomChange) {
        const scale = Math.max(0.5, state.zoomDistance * 0.8);
        callbacks.onZoomChange(scale);
        state.zoomDistance = scale;
      }
      state.lastGesture = 'pinch';
      // Reset fist timer when doing other gestures
      state.fistHoldStartTime = 0;
      state.isFistStable = false;
      return;
    }

    // 3. SPREAD/ZOOM IN: Fingers spread wide
    if (thumbIndexDist > 0.15 && extendedFingers >= 3) {
      if (callbacks.onZoomChange) {
        const scale = Math.min(3.0, state.zoomDistance * 1.2);
        callbacks.onZoomChange(scale);
        state.zoomDistance = scale;
      }
      state.lastGesture = 'spread';
      // Reset fist timer when doing other gestures
      state.fistHoldStartTime = 0;
      state.isFistStable = false;
      return;
    }

    // 4. FIST/BACK: All fingers closed - requires 1.5 seconds hold to prevent accidental triggers
    if (extendedFingers === 0 || (extendedFingers === 1 && isThumbExtended)) {
      // Start or continue fist hold
      if (state.fistHoldStartTime === 0) {
        state.fistHoldStartTime = now;
      }
      
      const holdDuration = now - state.fistHoldStartTime;
      
      // Require 1.5 seconds (1500ms) of stable fist hold
      if (holdDuration > 1500 && !state.isFistStable) {
        if (callbacks.onBack) {
          callbacks.onBack();
        }
        state.gestureCooldown = now;
        state.lastGesture = 'fist';
        state.isFistStable = true; // Mark as triggered to avoid repeat
        return;
      }
    } else {
      // Reset fist hold if hand opens
      state.fistHoldStartTime = 0;
      state.isFistStable = false;
    }

    // Update last position
    state.lastHandPosition = handCenter;
  }, [callbacks]);

  // Process Frames
  const predictWebcam = useCallback(() => {
    if (handLandmarker && videoRef.current && isCameraReady) {
      const nowInMs = Date.now();
      if (videoRef.current.currentTime !== lastVideoTimeRef.current) {
        lastVideoTimeRef.current = videoRef.current.currentTime;
        const results = handLandmarker.detectForVideo(videoRef.current, nowInMs) as HandLandmarkerResult;

        if (results.landmarks && results.landmarks.length > 0) {
          const landmarks = results.landmarks[0];
          detectGesture(landmarks);
        }
      }
    }
    requestRef.current = requestAnimationFrame(predictWebcam);
  }, [handLandmarker, isCameraReady, detectGesture]);

  useEffect(() => {
    if (isActive && isCameraReady && isModelLoaded) {
      requestRef.current = requestAnimationFrame(predictWebcam);
    } else {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    }
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [isActive, isCameraReady, isModelLoaded, predictWebcam]);

  if (!isActive) return null;

  return (
    <div className="fixed top-4 right-4 z-50 w-32 h-40 bg-black rounded-lg overflow-hidden border-2 border-green-400 shadow-lg opacity-90">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover transform scale-x-[-1]"
      />
      <div className="absolute bottom-0 w-full bg-black/70 text-[10px] text-white text-center py-1">
        {isModelLoaded ? '手势已就绪' : '加载中...'}
      </div>
    </div>
  );
};

export default GestureController;
