import { useEffect, useState } from 'react';
import { FileCode2 } from 'lucide-react';

interface Props {
  /** file name → source, in the order the judge runs them */
  files: Record<string, string>;
}

/**
 * pytest-mode problems ship their suite: the candidate reads it and debugs
 * from the failing test names, like a real screen. One tab per file.
 */
export function ProvidedTests({ files }: Props) {
  const names = Object.keys(files);
  const [active, setActive] = useState(names[names.length - 1] ?? '');
  // A newly unlocked part adds a file: show it
  useEffect(() => {
    setActive(names[names.length - 1] ?? '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [names.join('|')]);
  if (names.length === 0) return null;
  const source = files[active] ?? '';
  const count = (source.match(/^\s*def test/gm) ?? []).length;

  return (
    <div className="mt-4">
      <div className="flex items-center gap-2 mb-1.5">
        <FileCode2 size={13} className="text-gray-500" />
        <h4 className="text-xs font-semibold text-gray-900">Provided tests</h4>
        <span className="text-[11px] text-gray-400">
          Submit runs every file below; failures report by test name.
        </span>
      </div>
      {names.length > 1 && (
        <div className="flex gap-1 flex-wrap mb-1.5">
          {names.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setActive(n)}
              className={`px-2 py-0.5 rounded font-mono text-[11px] border ${
                n === active
                  ? 'bg-gray-900 text-white border-gray-900'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-100'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      )}
      <div className="text-[11px] text-gray-400 font-mono mb-1">
        {active} · {count} test{count === 1 ? '' : 's'}
      </div>
      <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-[12px] leading-5 overflow-x-auto max-h-[28rem] overflow-y-auto whitespace-pre">
        {source}
      </pre>
    </div>
  );
}
