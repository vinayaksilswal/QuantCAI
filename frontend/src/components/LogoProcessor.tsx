
import { useEffect, useState } from 'react';
import { removeBackground, loadImageFromUrl } from '@/utils/backgroundRemoval';

interface LogoProcessorProps {
  originalSrc: string;
  alt: string;
  className?: string;
  style?: React.CSSProperties;
}

export const LogoProcessor = ({ originalSrc, alt, className, style }: LogoProcessorProps) => {
  const [processedSrc, setProcessedSrc] = useState<string>(originalSrc);
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasProcessed, setHasProcessed] = useState(false);

  useEffect(() => {
    const processLogo = async () => {
      try {
        setIsProcessing(true);

        const imageElement = await loadImageFromUrl(originalSrc);

        const processedBlob = await removeBackground(imageElement);
        const processedUrl = URL.createObjectURL(processedBlob);

        setProcessedSrc(processedUrl);
        setHasProcessed(true);
      } catch (error) {
        console.error('Error processing logo:', error);
        // Keep original image if processing fails
        setProcessedSrc(originalSrc);
        setHasProcessed(false);
      } finally {
        setIsProcessing(false);
      }
    };

    processLogo();

    // Cleanup function to revoke object URL
    return () => {
      if (processedSrc !== originalSrc && processedSrc.startsWith('blob:')) {
        URL.revokeObjectURL(processedSrc);
      }
    };
  }, [originalSrc]);

  return (
    <img
      src={processedSrc}
      alt={alt}
      className={className}
      style={{
        ...style,
        opacity: isProcessing ? 0.7 : 1,
        transition: 'opacity 0.3s ease-in-out',
        // Enhanced filters for better logo appearance after processing
        filter: hasProcessed
          ? 'drop-shadow(0 0 20px rgba(59, 130, 246, 0.6)) brightness(1.4) contrast(1.5) saturate(1.4)'
          : style?.filter || 'drop-shadow(0 0 15px rgba(59, 130, 246, 0.5)) brightness(1.2) contrast(1.3) saturate(1.2)',
        mixBlendMode: hasProcessed ? 'normal' : 'screen'
      }}
    />
  );
};
