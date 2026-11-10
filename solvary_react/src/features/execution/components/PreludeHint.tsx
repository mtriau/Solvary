import { useEffect, useRef, useState } from 'react';
import { PackageOpen } from 'lucide-react';
import { usePythonPrelude } from '../hooks/usePythonPrelude';

/**
 * "Auto-imports" toolbar button: a popover listing the standard-library
 * names the sandbox preloads for Python, so nobody has to remember whether
 * `Counter` or `heappush` needs an import. Hidden when the list is unavailable.
 */
export default function PreludeHint({ compact = false }: { compact?: boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { data } = usePythonPrelude();

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!data) return null;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        title="Standard-library names you can use without importing them"
        aria-expanded={open}
        className={`inline-flex items-center gap-1.5 rounded-lg font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-700 ${
          compact ? 'px-2 py-1 text-xs' : 'px-2.5 py-1.5 text-xs'
        }`}
      >
        <PackageOpen size={13} /> Auto-imports
      </button>
      {open && (
        <div
          role="dialog"
          className="absolute right-0 top-full z-20 mt-1 w-[28rem] max-w-[90vw] max-h-80 overflow-auto rounded-lg border border-gray-200 bg-white p-3 text-xs shadow-lg"
        >
          <p className="mb-2 text-gray-600">
            Preloaded for every Python run and submission, so no import is needed. Writing the
            import yourself is fine too.
          </p>
          <ul className="space-y-1.5 font-mono">
            {data.modules.map((m) => (
              <li key={m} className="leading-snug">
                <span className="text-indigo-700">{m}</span>
                {data.names[m]?.length ? (
                  <span className="text-gray-500">: {data.names[m].join(', ')}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
