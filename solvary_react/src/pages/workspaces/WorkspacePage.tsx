import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Eye, Share2 } from 'lucide-react';
import { useAuth } from '@/app/providers/AuthProvider';
import CollabEditor from '@/features/collaboration/CollabEditor';
import PresenceBar from '@/features/collaboration/PresenceBar';
import { useCollab } from '@/features/collaboration/useCollab';
import ChallengePanel from '@/features/workspaces/ChallengePanel';
import FileTree from '@/features/workspaces/FileTree';
import SharePanel from '@/features/workspaces/SharePanel';
import {
  createFile,
  deleteFile,
  fetchFiles,
  fetchWorkspace,
  renameFile,
} from '@/shared/lib/api';

export default function WorkspacePage() {
  const { workspaceId = '' } = useParams();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [showShare, setShowShare] = useState(false);

  const { data: workspace } = useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => fetchWorkspace(workspaceId),
  });

  const { data: files = [] } = useQuery({
    queryKey: ['ws-files', workspaceId],
    queryFn: () => fetchFiles(workspaceId),
  });

  // Server broadcasts message 127 after REST file mutations → refetch metadata
  const onFilesChanged = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['ws-files', workspaceId] });
  }, [queryClient, workspaceId]);

  const { collab, synced, connected, peers } = useCollab(
    workspaceId,
    user ?? { id: 'anon', name: 'anon' },
    onFilesChanged,
  );

  useEffect(() => {
    if (!activeFileId && files.length > 0) setActiveFileId(files[0].id);
    if (activeFileId && !files.some((f) => f.id === activeFileId)) {
      setActiveFileId(files[0]?.id ?? null);
    }
  }, [files, activeFileId]);

  const invalidateFiles = () =>
    queryClient.invalidateQueries({ queryKey: ['ws-files', workspaceId] });

  const createMutation = useMutation({
    mutationFn: (path: string) => createFile(workspaceId, path),
    onSuccess: (file) => {
      invalidateFiles();
      setActiveFileId(file.id);
    },
  });
  const renameMutation = useMutation({
    mutationFn: ({ fileId, path }: { fileId: string; path: string }) =>
      renameFile(workspaceId, fileId, path),
    onSuccess: invalidateFiles,
  });
  const deleteMutation = useMutation({
    mutationFn: (fileId: string) => deleteFile(workspaceId, fileId),
    onSuccess: invalidateFiles,
  });

  if (!workspace) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400 text-sm">
        Loading workspace…
      </div>
    );
  }

  const isViewer = workspace.my_role === 'viewer';
  const activeFile = files.find((f) => f.id === activeFileId);

  return (
    <div className="h-full flex flex-col relative">
      <header className="flex items-center gap-3 px-4 py-2 border-b border-gray-200 bg-white">
        <Link to="/workspaces" className="text-gray-400 hover:text-gray-700">
          <ArrowLeft size={17} />
        </Link>
        <h1 className="font-semibold text-gray-900 truncate">{workspace.name}</h1>
        {isViewer && (
          <span className="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
            <Eye size={11} /> view only
          </span>
        )}
        <div className="flex-1" />
        <PresenceBar peers={peers} connected={connected} />
        <button
          onClick={() => setShowShare((s) => !s)}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <Share2 size={13} /> Share
        </button>
      </header>

      {showShare && (
        <SharePanel
          workspaceId={workspaceId}
          isOwner={workspace.my_role === 'owner'}
          onClose={() => setShowShare(false)}
        />
      )}

      <div className="flex-1 flex min-h-0">
        <FileTree
          files={files}
          activeFileId={activeFileId}
          canEdit={!isViewer}
          onSelect={setActiveFileId}
          onCreate={(path) => createMutation.mutate(path)}
          onRename={(fileId, path) => renameMutation.mutate({ fileId, path })}
          onDelete={(fileId) => deleteMutation.mutate(fileId)}
        />
        <main className="flex-1 min-w-0">
          {collab && synced && activeFile ? (
            <CollabEditor
              key={activeFile.id}
              collab={collab}
              fileId={activeFile.id}
              path={activeFile.path}
              readOnly={isViewer}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400 text-sm">
              {connected ? 'Syncing document…' : 'Connecting…'}
            </div>
          )}
        </main>
        {workspace.problem_id && (
          <ChallengePanel
            workspace={workspace}
            collab={collab}
            activeFileId={activeFileId}
          />
        )}
      </div>
    </div>
  );
}
