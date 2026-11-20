import { AlertTriangle, RotateCcw } from "lucide-react";

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="banner banner-error" role="alert">
      <AlertTriangle size={18} aria-hidden="true" />
      <div className="banner-body">{message}</div>
      {onRetry && (
        <button className="btn btn-sm" onClick={onRetry} type="button">
          <RotateCcw size={15} aria-hidden="true" />
          Try again
        </button>
      )}
    </div>
  );
}
