import { useState, useCallback } from 'react';
import { X, Download, Copy, Check, Share2, Twitter } from 'lucide-react';
import type { ShareData } from '@/utils/circuitExporter';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  shareData: ShareData | null;
}

/**
 * One-click "Share to X" modal for circuit animations.
 * Pre-populates tweet text with circuit description and QuantCAI link.
 * Supports downloading the animation and copying the share link.
 */
export const ShareModal = ({ isOpen, onClose, shareData }: ShareModalProps) => {
  const [copied, setCopied] = useState(false);
  const [tweetText, setTweetText] = useState('');

  // Initialize tweet text when shareData changes
  useState(() => {
    if (shareData) {
      setTweetText(shareData.text);
    }
  });

  const handleCopyLink = useCallback(async () => {
    try {
      await navigator.clipboard.writeText('https://quantcai.in/circuit-builder');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = 'https://quantcai.in/circuit-builder';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, []);

  const handleShareToX = useCallback(() => {
    const text = encodeURIComponent(tweetText || shareData?.text || '');
    const hashtags = encodeURIComponent(
      (shareData?.hashtags || []).map(h => h.replace('#', '')).join(',')
    );
    const url = `https://twitter.com/intent/tweet?text=${text}&hashtags=${hashtags}`;
    window.open(url, '_blank', 'noopener,noreferrer,width=600,height=400');
  }, [tweetText, shareData]);

  const handleDownload = useCallback(() => {
    if (!shareData) return;
    const a = document.createElement('a');
    a.href = shareData.url;
    a.download = shareData.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, [shareData]);

  const handleNativeShare = useCallback(async () => {
    if (!shareData || !navigator.share) return;
    
    try {
      const file = new File([shareData.blob], shareData.filename, {
        type: 'video/webm',
      });
      
      await navigator.share({
        title: 'QuantCAI Circuit',
        text: shareData.text,
        files: [file],
      });
    } catch (error) {
      // User cancelled or share failed — fall back to X
      handleShareToX();
    }
  }, [shareData, handleShareToX]);

  if (!isOpen || !shareData) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md rounded-2xl border border-white/10 bg-[#0f172a]/95 p-6 shadow-2xl backdrop-blur-xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="mb-6">
          <h3 className="text-xl font-bold text-white">Share Your Circuit</h3>
          <p className="mt-1 text-sm text-gray-400">
            Share your quantum circuit animation with the world
          </p>
        </div>

        {/* Video Preview */}
        <div className="mb-6 overflow-hidden rounded-xl border border-white/10 bg-black/30">
          <video
            src={shareData.url}
            autoPlay
            loop
            muted
            playsInline
            className="h-48 w-full object-contain"
          />
        </div>

        {/* Tweet Text Editor */}
        <div className="mb-6">
          <label className="mb-2 block text-xs font-medium text-gray-400">
            Post Text
          </label>
          <textarea
            value={tweetText || shareData.text}
            onChange={(e) => setTweetText(e.target.value)}
            rows={3}
            maxLength={280}
            className="w-full resize-none rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-gray-500 outline-none transition-colors focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20"
          />
          <div className="mt-1 text-right text-xs text-gray-500">
            {(tweetText || shareData.text).length}/280
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-3">
          {/* Primary: Share to X */}
          <button
            onClick={handleShareToX}
            className="flex items-center justify-center gap-2 rounded-xl bg-black px-4 py-3 text-sm font-semibold text-white transition-all hover:bg-gray-900 active:scale-[0.98]"
          >
            <Twitter className="h-4 w-4" />
            Post to X
          </button>

          {/* Secondary Row */}
          <div className="flex gap-3">
            {/* Download */}
            <button
              onClick={handleDownload}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-white/10 active:scale-[0.98]"
            >
              <Download className="h-4 w-4" />
              Download
            </button>

            {/* Copy Link */}
            <button
              onClick={handleCopyLink}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-white/10 active:scale-[0.98]"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 text-green-400" />
                  <span className="text-green-400">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy Link
                </>
              )}
            </button>

            {/* Native Share (mobile) */}
            {typeof navigator !== 'undefined' && 'share' in navigator && (
              <button
                onClick={handleNativeShare}
                className="flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white transition-all hover:bg-white/10 active:scale-[0.98]"
                title="Share"
              >
                <Share2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        {/* Hashtags */}
        <div className="mt-4 flex flex-wrap gap-2">
          {shareData.hashtags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ShareModal;
