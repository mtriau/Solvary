import { useState } from 'react';
import { FilePlus, FileText, Pencil, Trash2 } from 'lucide-react';
import type { WorkspaceFile } from '@/shared/types/api';

interface Props {
  files: WorkspaceFile[];
  activeFileId: string | null;
  canEdit: boolean;
  onSelect: (fileId: string) => void;
  onCreate: (path: string) => void;
  onRename: (fileId: string, path: string) => void;
  onDelete: (fileId: string) => void;
}

export default function FileTree({
  files,
  activeFileId,
  canEdit,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}: Props) {
  const [creating, setCreating] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [draft, setDraft] = useState('');

  const submitCreate = () => {
    if (draft.trim()) onCreate(draft.trim());
    setCreating(false);
    setDraft('');
  };
  const submitRename = (fileId: string) => {
    if (draft.trim()) onRename(fileId, draft.trim());
    setRenamingId(null);
    setDraft('');
  };

  return (
    <div className="w-56 border-r border-gray-200 bg-gray-50 flex flex-col">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Files
        </span>
        {canEdit && (
          <button
            onClick={() => {
              setCreating(true);
              setDraft('');
            }}
            className="text-gray-400 hover:text-gray-700"
            title="New file"
          >
            <FilePlus size={15} />
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto py-1">
        {files.map((f) =>
          renamingId === f.id ? (
            <input
              key={f.id}
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={() => submitRename(f.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submitRename(f.id);
                if (e.key === 'Escape') setRenamingId(null);
              }}
              className="mx-2 my-0.5 w-[calc(100%-1rem)] px-2 py-1 text-sm border border-indigo-300 rounded"
            />
          ) : (
            <div
              key={f.id}
              className={`group flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer ${
                f.id === activeFileId
                  ? 'bg-indigo-50 text-indigo-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => onSelect(f.id)}
            >
              <FileText size={14} className="shrink-0 opacity-60" />
              <span className="truncate flex-1">{f.path}</span>
              {canEdit && (
                <span className="hidden group-hover:flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setRenamingId(f.id);
                      setDraft(f.path);
                    }}
                    className="text-gray-400 hover:text-gray-700"
                    title="Rename"
                  >
                    <Pencil size={12} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(f.id);
                    }}
                    className="text-gray-400 hover:text-red-600"
                    title="Delete"
                  >
                    <Trash2 size={12} />
                  </button>
                </span>
              )}
            </div>
          ),
        )}
        {creating && (
          <input
            autoFocus
            value={draft}
            placeholder="filename.py"
            onChange={(e) => setDraft(e.target.value)}
            onBlur={submitCreate}
            onKeyDown={(e) => {
              if (e.key === 'Enter') submitCreate();
              if (e.key === 'Escape') setCreating(false);
            }}
            className="mx-2 my-0.5 w-[calc(100%-1rem)] px-2 py-1 text-sm border border-indigo-300 rounded"
          />
        )}
      </div>
    </div>
  );
}
