import type { ButtonHTMLAttributes } from "react";

interface LoadingButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  variant?: "primary" | "ink" | "secondary" | "quiet";
  block?: boolean;
  size?: "md" | "sm";
}

export function LoadingButton({
  loading,
  variant = "primary",
  block,
  size = "md",
  children,
  disabled,
  className,
  ...rest
}: LoadingButtonProps) {
  const classes = [
    "btn",
    variant === "primary" ? "btn-primary" : variant === "ink" ? "btn-ink" : variant === "quiet" ? "btn-quiet" : "",
    size === "sm" ? "btn-sm" : "",
    block ? "btn-block" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {loading && <span className="spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}
