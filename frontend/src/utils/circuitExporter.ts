/**
 * =============================================================================
 * QuantCAI — Client-Side Circuit Animation Exporter
 * =============================================================================
 * Records quantum circuit canvas animations using the HTML5 MediaRecorder API.
 * Produces .webm blobs that can be downloaded or shared to social media.
 *
 * Architecture:
 *   - Uses HTMLCanvasElement.captureStream() for zero-copy frame capture
 *   - MediaRecorder encodes to VP8/WebM format natively in the browser
 *   - No server-side compute required — fully client-side
 *
 * Usage:
 *   const exporter = new CircuitExporter(canvasElement);
 *   exporter.startRecording();
 *   // ... user runs circuit simulation ...
 *   const blob = await exporter.stopRecording();
 *   exporter.download('my-circuit.webm');
 *   // or use exporter.getShareData() for the Share Modal
 *
 * Copyright (c) 2026 QuantCAI — All rights reserved.
 * =============================================================================
 */

export interface CircuitExportResult {
  blob: Blob;
  url: string;
  duration: number;
  format: 'webm' | 'gif';
}

export interface ShareData {
  blob: Blob;
  url: string;
  filename: string;
  text: string;
  hashtags: string[];
}

/**
 * Client-side circuit animation recorder using the MediaRecorder API.
 *
 * Records canvas animations to .webm format for sharing and download.
 * Falls back gracefully if MediaRecorder is not supported.
 */
export class CircuitExporter {
  private canvas: HTMLCanvasElement;
  private mediaRecorder: MediaRecorder | null = null;
  private recordedChunks: Blob[] = [];
  private startTime: number = 0;
  private resultBlob: Blob | null = null;
  private resultUrl: string | null = null;
  private isRecording: boolean = false;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
  }

  /**
   * Check if MediaRecorder is available in this browser.
   */
  static isSupported(): boolean {
    return (
      typeof MediaRecorder !== 'undefined' &&
      typeof HTMLCanvasElement.prototype.captureStream === 'function'
    );
  }

  /**
   * Start recording the canvas animation.
   *
   * @param fps - Target frames per second (default: 30)
   * @returns true if recording started successfully
   */
  startRecording(fps: number = 30): boolean {
    if (!CircuitExporter.isSupported()) {
      console.warn('[CircuitExporter] MediaRecorder not supported in this browser');
      return false;
    }

    if (this.isRecording) {
      console.warn('[CircuitExporter] Already recording');
      return false;
    }

    // Clean up any previous recording
    this.cleanup();

    try {
      const stream = this.canvas.captureStream(fps);

      // Prefer VP9 codec, fall back to VP8
      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
        ? 'video/webm;codecs=vp9'
        : 'video/webm;codecs=vp8';

      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        videoBitsPerSecond: 2_500_000, // 2.5 Mbps for good quality
      });

      this.recordedChunks = [];
      this.startTime = performance.now();

      this.mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      };

      // Request data every 100ms for smooth chunking
      this.mediaRecorder.start(100);
      this.isRecording = true;

      console.log(`[CircuitExporter] Recording started (${mimeType}, ${fps}fps)`);
      return true;
    } catch (error) {
      console.error('[CircuitExporter] Failed to start recording:', error);
      return false;
    }
  }

  /**
   * Stop recording and return the result.
   *
   * @returns Promise resolving to the export result with blob and metadata
   */
  stopRecording(): Promise<CircuitExportResult> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || !this.isRecording) {
        reject(new Error('Not recording'));
        return;
      }

      this.mediaRecorder.onstop = () => {
        const duration = (performance.now() - this.startTime) / 1000;
        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);

        this.resultBlob = blob;
        this.resultUrl = url;
        this.isRecording = false;

        console.log(
          `[CircuitExporter] Recording stopped. Duration: ${duration.toFixed(1)}s, ` +
          `Size: ${(blob.size / 1024).toFixed(1)}KB`
        );

        resolve({
          blob,
          url,
          duration,
          format: 'webm',
        });
      };

      this.mediaRecorder.stop();
    });
  }

  /**
   * Download the recorded animation as a .webm file.
   *
   * @param filename - Name of the downloaded file (without extension)
   */
  download(filename: string = 'quantcai-circuit'): void {
    if (!this.resultBlob || !this.resultUrl) {
      console.warn('[CircuitExporter] No recording available to download');
      return;
    }

    const a = document.createElement('a');
    a.href = this.resultUrl;
    a.download = `${filename}.webm`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  /**
   * Get data formatted for the Share Modal component.
   *
   * @param circuitName - Human-readable name of the circuit
   * @returns ShareData object ready for the ShareModal component
   */
  getShareData(circuitName: string = 'Quantum Circuit'): ShareData | null {
    if (!this.resultBlob || !this.resultUrl) {
      return null;
    }

    return {
      blob: this.resultBlob,
      url: this.resultUrl,
      filename: `quantcai-${circuitName.toLowerCase().replace(/\s+/g, '-')}.webm`,
      text: `🔬 Just built and simulated "${circuitName}" on @QuantCAI!\n\nExplore quantum circuits interactively → https://quantcai.in/circuit-builder`,
      hashtags: ['#QuantumComputing', '#Qiskit', '#QuantCAI', '#PQC'],
    };
  }

  /**
   * Take a single screenshot of the canvas.
   *
   * @param format - Image format ('png' or 'jpeg')
   * @param quality - JPEG quality (0-1, default 0.92)
   * @returns Blob of the screenshot, or null if failed
   */
  async takeScreenshot(
    format: 'png' | 'jpeg' = 'png',
    quality: number = 0.92
  ): Promise<Blob | null> {
    return new Promise((resolve) => {
      this.canvas.toBlob(
        (blob) => resolve(blob),
        `image/${format}`,
        quality
      );
    });
  }

  /**
   * Check if a recording is currently in progress.
   */
  get recording(): boolean {
    return this.isRecording;
  }

  /**
   * Get the last recorded blob, if available.
   */
  get lastRecording(): Blob | null {
    return this.resultBlob;
  }

  /**
   * Clean up resources (revoke object URLs).
   */
  cleanup(): void {
    if (this.resultUrl) {
      URL.revokeObjectURL(this.resultUrl);
      this.resultUrl = null;
    }
    this.resultBlob = null;
    this.recordedChunks = [];
    this.isRecording = false;
    this.mediaRecorder = null;
  }
}

/**
 * Convenience function to record a canvas for a fixed duration.
 *
 * @param canvas - The canvas element to record
 * @param durationMs - How long to record in milliseconds
 * @param fps - Target frames per second
 * @returns Promise resolving to the export result
 */
export async function recordCanvasAnimation(
  canvas: HTMLCanvasElement,
  durationMs: number = 3000,
  fps: number = 30
): Promise<CircuitExportResult | null> {
  const exporter = new CircuitExporter(canvas);

  if (!exporter.startRecording(fps)) {
    return null;
  }

  await new Promise((resolve) => setTimeout(resolve, durationMs));

  return exporter.stopRecording();
}
