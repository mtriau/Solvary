import { Users } from 'lucide-react';

/**
 * Placeholder — M3 replaces this with the workspace list and the
 * collaborative Monaco + Yjs editor.
 */
export default function WorkspacesPage() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-4">
      <Users size={40} className="text-gray-300 mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Workspaces</h2>
      <p className="text-gray-500 max-w-sm">
        Collaborative workspaces land in M3 — live multi-cursor editing,
        presence, and shared runs.
      </p>
    </div>
  );
}
