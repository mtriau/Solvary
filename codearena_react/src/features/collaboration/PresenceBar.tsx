import { useEffect } from 'react';
import type { PeerState } from './useCollab';
import { syncRemoteCursorStyles } from './remote-cursors';

interface Props {
  peers: PeerState[];
  connected: boolean;
}

/** Avatar stack of live collaborators + connection dot. Also owns the
 * injected per-peer cursor styles. */
export default function PresenceBar({ peers, connected }: Props) {
  useEffect(() => {
    syncRemoteCursorStyles(peers);
  }, [peers]);

  return (
    <div className="flex items-center gap-3">
      <div className="flex -space-x-2">
        {peers.map((p) => (
          <div
            key={p.clientId}
            title={p.name}
            className="w-7 h-7 rounded-full border-2 border-white flex items-center justify-center text-[11px] font-semibold text-white"
            style={{ backgroundColor: p.color }}
          >
            {p.name.slice(0, 2).toUpperCase()}
          </div>
        ))}
      </div>
      <span
        className={`inline-flex items-center gap-1.5 text-xs ${
          connected ? 'text-emerald-600' : 'text-amber-600'
        }`}
      >
        <span
          className={`w-2 h-2 rounded-full ${
            connected ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'
          }`}
        />
        {connected ? 'Live' : 'Connecting…'}
      </span>
    </div>
  );
}
