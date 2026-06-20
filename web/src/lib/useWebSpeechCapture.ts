import { useCallback, useEffect, useRef, useState } from "react";
import { speechRecognitionSupported } from "./speechCapture";

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string; message?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

type SpeechRecognitionEventLike = {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      [index: number]: { transcript: string };
    };
  };
};

function createRecognition(): SpeechRecognitionLike | null {
  if (typeof window === "undefined") return null;
  const w = window as Window & {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  if (!Ctor) return null;
  const rec = new Ctor();
  rec.continuous = true;
  rec.interimResults = true;
  rec.lang = "en-US";
  return rec;
}

export function useWebSpeechCapture() {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const supported = speechRecognitionSupported();

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const listeningRef = useRef(false);
  const finalTranscriptRef = useRef("");

  const stopLevelLoop = useCallback(() => {
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  const stopMedia = useCallback(() => {
    stopLevelLoop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (audioContextRef.current) {
      void audioContextRef.current.close();
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  }, [stopLevelLoop]);

  const stopRecognition = useCallback(() => {
    const rec = recognitionRef.current;
    recognitionRef.current = null;
    if (!rec) return;
    rec.onresult = null;
    rec.onerror = null;
    rec.onend = null;
    try {
      rec.abort();
    } catch {
      try {
        rec.stop();
      } catch {
        /* ignore */
      }
    }
  }, []);

  const stop = useCallback(() => {
    listeningRef.current = false;
    setListening(false);
    stopRecognition();
    stopMedia();
  }, [stopMedia, stopRecognition]);

  const startLevelLoop = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.fftSize);
    const tick = () => {
      if (!listeningRef.current) return;
      analyser.getByteTimeDomainData(data);
      let sum = 0;
      for (let i = 0; i < data.length; i += 1) {
        const v = (data[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / data.length);
      setAudioLevel(Math.min(1, rms * 4));
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const start = useCallback(async (): Promise<boolean> => {
    setError(null);
    finalTranscriptRef.current = "";
    setTranscript("");

    if (!supported) {
      setError("Speech recognition is not supported in this browser. Try Chrome or Safari.");
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const ctx = new AudioContext();
      audioContextRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
    } catch (e) {
      const msg =
        e instanceof DOMException && e.name === "NotAllowedError"
          ? "Microphone permission denied. Allow mic access for this site in browser settings."
          : e instanceof Error
            ? e.message
            : "Could not access microphone";
      setError(msg);
      stopMedia();
      return false;
    }

    const rec = createRecognition();
    if (!rec) {
      setError("Speech recognition is unavailable.");
      stopMedia();
      return false;
    }

    recognitionRef.current = rec;

    rec.onresult = (event) => {
      let interim = finalTranscriptRef.current;
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const piece = event.results[i][0]?.transcript ?? "";
        if (event.results[i].isFinal) {
          finalTranscriptRef.current += piece;
          interim = finalTranscriptRef.current;
        } else {
          interim = finalTranscriptRef.current + piece;
        }
      }
      setTranscript(interim.trim());
    };

    rec.onerror = (event) => {
      if (event.error === "aborted" || event.error === "no-speech") return;
      setError(event.message ?? `Speech error: ${event.error}`);
    };

    rec.onend = () => {
      if (!listeningRef.current) return;
      // Chrome stops recognition periodically — restart while passive listen is on.
      try {
        rec.start();
      } catch {
        /* ignore double-start */
      }
    };

    try {
      rec.start();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start speech recognition");
      stopMedia();
      return false;
    }

    listeningRef.current = true;
    setListening(true);
    startLevelLoop();
    return true;
  }, [supported, startLevelLoop, stopMedia]);

  useEffect(() => () => stop(), [stop]);

  return {
    supported,
    listening,
    transcript,
    audioLevel,
    error,
    start,
    stop,
    clearTranscript: () => {
      finalTranscriptRef.current = "";
      setTranscript("");
    },
  };
}
