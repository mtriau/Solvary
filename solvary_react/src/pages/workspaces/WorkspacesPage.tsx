import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Users } from 'lucide-react';
import { createWorkspace, fetchWorkspaces } from '@/shared/lib/api';

export default function WorkspacesPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [language, setLanguage] = useState('python');

  const { data: workspaces = [], isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: fetchWorkspaces,
  });

  const createMutation = useMutation({
    mutationFn: () => createWorkspace({ name, language }),
    onSuccess: () => {
      setName('');
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Workspaces</h1>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) createMutation.mutate();
        }}
        className="flex gap-2 mb-8"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New workspace name…"
          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="px-2 py-2 text-sm border border-gray-300 rounded-lg"
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
        </select>
        <button
          type="submit"
          disabled={createMutation.isPending || !name.trim()}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          <Plus size={16} /> Create
        </button>
      </form>

      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : workspaces.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Users size={36} className="mx-auto mb-3 opacity-50" />
          <p className="text-sm">No workspaces yet — create one to start collaborating.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {workspaces.map((ws) => (
            <Link
              key={ws.id}
              to={`/workspaces/${ws.id}`}
              className="block p-4 bg-white border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-sm transition"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900 truncate">{ws.name}</span>
                <span className="text-[11px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
                  {ws.my_role}
                </span>
              </div>
              <span className="text-xs text-gray-400">{ws.language}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
