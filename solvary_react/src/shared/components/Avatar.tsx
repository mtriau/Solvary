interface AvatarProps {
  src: string;
  name: string;
  size?: 'sm' | 'md' | 'lg';
}

const SIZES = {
  sm: 'w-6 h-6 text-[10px]',
  md: 'w-8 h-8 text-xs',
  lg: 'w-10 h-10 text-sm',
} as const;

export function Avatar({ src, name, size = 'md' }: AvatarProps) {
  const initials = name
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div
      className={`${SIZES[size]} rounded-full bg-indigo-600 text-white flex items-center justify-center font-semibold overflow-hidden shrink-0`}
      title={name}
    >
      {src ? (
        <img src={src} alt={name} className="w-full h-full object-cover" />
      ) : (
        initials
      )}
    </div>
  );
}
