/**
 * Yjs + y-websocket provider hook (design §7/§8).
 *
 * - Auth: JWT rides the WebSocket subprotocol (protocols: [token]) — never
 *   the query string.
 * - Message type 127 is Solvary's file-listing-changed extension: the
 *   server broadcasts it after REST file mutations; we refetch metadata.
 * - The Y.Doc holds one Map "files" keyed by WorkspaceFile.id → Y.Text.
 */

import { useEffect, useRef, useState } from 'react';
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';

const MESSAGE_FILES_CHANGED = 127;

const PEER_COLORS = [
  '#e11d48', '#7c3aed', '#0284c7', '#059669',
  '#d97706', '#db2777', '#4f46e5', '#0d9488',
];

export function colorForUser(userId: string): string {
  let hash = 0;
  for (const ch of userId) hash = (hash * 31 + ch.charCodeAt(0)) | 0;
  return PEER_COLORS[Math.abs(hash) % PEER_COLORS.length];
}

export interface PeerState {
  clientId: number;
  name: string;
  color: string;
  userId: string;
}

export interface CollabState {
  doc: Y.Doc;
  provider: WebsocketProvider;
}

export function useCollab(
  workspaceId: string,
  user: { id: string; name: string },
  onFilesChanged: () => void,
) {
  const [collab, setCollab] = useState<CollabState | null>(null);
  const [synced, setSynced] = useState(false);
  const [connected, setConnected] = useState(false);
  const [peers, setPeers] = useState<PeerState[]>([]);
  const onFilesChangedRef = useRef(onFilesChanged);
  onFilesChangedRef.current = onFilesChanged;

  useEffect(() => {
    const doc = new Y.Doc();
    const token = localStorage.getItem('auth_token') ?? '';
    const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const provider = new WebsocketProvider(
      `${wsProto}//${location.host}/ws/workspaces`,
      workspaceId,
      doc,
      { protocols: [token] },
    );

    provider.messageHandlers[MESSAGE_FILES_CHANGED] = () => {
      onFilesChangedRef.current();
    };

    provider.awareness.setLocalStateField('user', {
      name: user.name,
      color: colorForUser(user.id),
      id: user.id,
    });

    const onSync = (isSynced: boolean) => setSynced(isSynced);
    const onStatus = ({ status }: { status: string }) =>
      setConnected(status === 'connected');
    const onAwareness = () => {
      const states: PeerState[] = [];
      provider.awareness.getStates().forEach((state, clientId) => {
        if (clientId === provider.awareness.clientID) return;
        const u = state.user as { name: string; color: string; id: string } | undefined;
        if (u) states.push({ clientId, name: u.name, color: u.color, userId: u.id });
      });
      setPeers(states);
    };

    provider.on('sync', onSync);
    provider.on('status', onStatus);
    provider.awareness.on('change', onAwareness);
    setCollab({ doc, provider });

    return () => {
      provider.awareness.off('change', onAwareness);
      provider.off('sync', onSync);
      provider.off('status', onStatus);
      provider.destroy();
      doc.destroy();
      setCollab(null);
      setSynced(false);
      setConnected(false);
      setPeers([]);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId, user.id]);

  return { collab, synced, connected, peers };
}
