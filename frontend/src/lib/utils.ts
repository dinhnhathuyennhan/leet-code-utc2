import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Merge Tailwind class names intelligently.
 *
 * Standard shadcn-style utility: `clsx` for conditional classes,
 * `tailwind-merge` để gộp các class Tailwind trùng nhau.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
