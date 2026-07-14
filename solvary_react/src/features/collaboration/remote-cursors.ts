/**
 * y-monaco renders remote selections/cursors with per-client CSS classes
 * (`.yRemoteSelection-<clientId>`, `.yRemoteSelectionHead-<clientId>`) but
 * ships no styles — we inject a rule set per peer, tinted with their color.
 */

import type { PeerState } from './useCollab';

const STYLE_ID = 'y-remote-cursor-styles';

export function syncRemoteCursorStyles(peers: PeerState[]): void {
  let el = document.getElementById(STYLE_ID) as HTMLStyleElement | null;
  if (!el) {
    el = document.createElement('style');
    el.id = STYLE_ID;
    document.head.appendChild(el);
  }
  el.textContent = peers
    .map(
      (p) => `
.yRemoteSelection-${p.clientId} { background-color: ${p.color}40; }
.yRemoteSelectionHead-${p.clientId} {
  position: absolute;
  border-left: 2px solid ${p.color};
  height: 100%;
}
.yRemoteSelectionHead-${p.clientId}::after {
  content: "${p.name.replace(/["\\]/g, '')}";
  position: absolute;
  top: -1.2em;
  left: -2px;
  padding: 0 4px;
  font-size: 10px;
  line-height: 1.2em;
  white-space: nowrap;
  color: white;
  background-color: ${p.color};
  border-radius: 2px 2px 2px 0;
}`,
    )
    .join('\n');
}
