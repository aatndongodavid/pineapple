import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface ResponsiveImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  webpSrc?: string;
  avifSrc?: string;
  aspectRatio?: 'square' | 'video' | 'banner' | 'auto';
  className?: string;
}

export const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  src,
  alt,
  webpSrc,
  avifSrc,
  aspectRatio = 'auto',
  className,
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const aspectClasses = {
    square: 'aspect-square',
    video: 'aspect-video',
    banner: 'aspect-[3/1]',
    auto: '',
  };

  return (
    <div
      className={cn(
        'relative overflow-hidden bg-stone-100 dark:bg-stone-800 transition-opacity',
        aspectClasses[aspectRatio],
        className
      )}
    >
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 bg-stone-200 dark:bg-stone-700 animate-pulse" />
      )}

      {hasError ? (
        <div className="absolute inset-0 flex items-center justify-center bg-stone-100 dark:bg-stone-800 text-stone-400 text-xs p-2 text-center">
          Image non disponible
        </div>
      ) : (
        <picture>
          {avifSrc && <source srcSet={avifSrc} type="image/avif" />}
          {webpSrc && <source srcSet={webpSrc} type="image/webp" />}
          <img
            src={src}
            alt={alt}
            loading="lazy"
            decoding="async"
            onLoad={() => setIsLoaded(true)}
            onError={() => setHasError(true)}
            className={cn(
              'w-full h-full object-cover transition-opacity duration-300',
              isLoaded ? 'opacity-100' : 'opacity-0'
            )}
            {...props}
          />
        </picture>
      )}
    </div>
  );
};
