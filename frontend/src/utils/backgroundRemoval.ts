
const MAX_IMAGE_DIMENSION = 1024;

function resizeImageIfNeeded(canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, image: HTMLImageElement) {
  let width = image.naturalWidth;
  let height = image.naturalHeight;

  if (width > MAX_IMAGE_DIMENSION || height > MAX_IMAGE_DIMENSION) {
    if (width > height) {
      height = Math.round((height * MAX_IMAGE_DIMENSION) / width);
      width = MAX_IMAGE_DIMENSION;
    } else {
      width = Math.round((width * MAX_IMAGE_DIMENSION) / height);
      height = MAX_IMAGE_DIMENSION;
    }

    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(image, 0, 0, width, height);
    return true;
  }

  canvas.width = width;
  canvas.height = height;
  ctx.drawImage(image, 0, 0);
  return false;
}

// Enhanced function to remove black background and text
const removeBlackBackgroundAndText = (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D): HTMLCanvasElement => {
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;

  // Create output canvas
  const outputCanvas = document.createElement('canvas');
  outputCanvas.width = canvas.width;
  outputCanvas.height = canvas.height;
  const outputCtx = outputCanvas.getContext('2d');

  if (!outputCtx) return canvas;

  // Process each pixel to remove black background and text
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const alpha = data[i + 3];

    // Check if pixel is black or very dark (threshold for background)
    const brightness = (r + g + b) / 3;
    const isBlackish = brightness < 30;

    // Check if pixel is likely text (dark but not pure black, or high contrast edges)
    const isTextLike = brightness < 80 && brightness > 20;

    // Check for white/light text on dark background
    const isWhiteText = brightness > 200 && (r > 180 && g > 180 && b > 180);

    if (isBlackish || isTextLike || isWhiteText) {
      // Make these pixels transparent
      data[i + 3] = 0;
    } else {
      // Keep non-black pixels as they are
      data[i + 3] = alpha;
    }
  }

  outputCtx.putImageData(imageData, 0, 0);
  return outputCanvas;
};

export const removeBackground = async (imageElement: HTMLImageElement): Promise<Blob> => {
  try {

    // Try enhanced black background and text removal
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) throw new Error('Could not get canvas context');

    // Resize image if needed and draw it to canvas
    const wasResized = resizeImageIfNeeded(canvas, ctx, imageElement);

    // Apply enhanced background and text removal
    const processedCanvas = removeBlackBackgroundAndText(canvas, ctx);

    // Convert canvas to blob
    return new Promise((resolve, reject) => {
      processedCanvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to create blob'));
          }
        },
        'image/png',
        1.0
      );
    });
  } catch (error) {
    console.error('Error removing background and text:', error);

    // Fallback: try to at least convert to PNG with transparency
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      if (ctx) {
        canvas.width = imageElement.naturalWidth;
        canvas.height = imageElement.naturalHeight;
        ctx.drawImage(imageElement, 0, 0);

        return new Promise((resolve, reject) => {
          canvas.toBlob(
            (blob) => {
              if (blob) {
                console.log('Created fallback blob');
                resolve(blob);
              } else {
                reject(new Error('Failed to create fallback blob'));
              }
            },
            'image/png',
            1.0
          );
        });
      }
    } catch (fallbackError) {
      console.error('Fallback also failed:', fallbackError);
    }

    throw error;
  }
};

export const loadImage = (file: Blob): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
};

export const loadImageFromUrl = (url: string): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.crossOrigin = 'anonymous';
    img.src = url;
  });
};
