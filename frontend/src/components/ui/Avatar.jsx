import { cn } from '../../lib/cn'

const sizes = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-16 w-16 text-lg',
  xl: 'h-24 w-24 text-2xl',
}

/** Photo de profil, ou initiales si absente. */
export default function Avatar({ src, firstName, lastName, size = 'md', className }) {
  const initials = `${firstName?.[0] ?? ''}${lastName?.[0] ?? ''}`.toUpperCase() || '?'
  return src ? (
    <img
      src={src}
      alt=""
      className={cn('shrink-0 rounded-full object-cover', sizes[size], className)}
    />
  ) : (
    <span
      aria-hidden="true"
      className={cn(
        'bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-200 inline-flex shrink-0 items-center justify-center rounded-full font-semibold',
        sizes[size],
        className,
      )}
    >
      {initials}
    </span>
  )
}
