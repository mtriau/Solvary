import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { UserPlus, X } from 'lucide-react';
import { addMember, fetchMembers, removeMember } from '@/shared/lib/api';
import type { MemberRole } from '@/shared/types/api';

interface Props {
  workspaceId: string;
  isOwner: boolean;
  onClose: () => void;
}

export default function SharePanel({ workspaceId, isOwner, onClose }: Props) {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<Exclude<MemberRole, 'owner'>>('editor');
  const [error, setError] = useState<string | null>(null);

  const { data: members = [] } = useQuery({
    queryKey: ['ws-members', workspaceId],
    queryFn: () => fetchMembers(workspaceId),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['ws-members', workspaceId] });

  const addMutation = useMutation({
    mutationFn: () => addMember(workspaceId, email, role),
    onSuccess: () => {
      setEmail('');
      setError(null);
      invalidate();
    },
    onError: (e: Error) => setError(e.message),
  });

  const removeMutation = useMutation({
    mutationFn: (memberId: string) => removeMember(workspaceId, memberId),
    onSuccess: invalidate,
  });

  return (
    <div className="absolute right-4 top-14 z-20 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">Members</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-700">
          <X size={16} />
        </button>
      </div>

      {isOwner && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (email.trim()) addMutation.mutate();
          }}
          className="flex gap-1.5 mb-3"
        >
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="teammate@email.com"
            className="flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as 'editor' | 'viewer')}
            className="px-1.5 py-1.5 text-sm border border-gray-300 rounded"
          >
            <option value="editor">editor</option>
            <option value="viewer">viewer</option>
          </select>
          <button
            type="submit"
            disabled={addMutation.isPending}
            className="px-2 py-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
            title="Add member"
          >
            <UserPlus size={15} />
          </button>
        </form>
      )}
      {error && <p className="text-xs text-red-600 mb-2">{error}</p>}

      <ul className="space-y-1.5 max-h-56 overflow-y-auto">
        {members.map((m) => (
          <li key={m.id} className="flex items-center gap-2 text-sm">
            <img src={m.avatar_url} alt="" className="w-6 h-6 rounded-full" />
            <span className="flex-1 truncate text-gray-800">{m.name}</span>
            <span className="text-xs text-gray-400">{m.role}</span>
            {isOwner && m.role !== 'owner' && (
              <button
                onClick={() => removeMutation.mutate(m.id)}
                className="text-gray-300 hover:text-red-600"
                title="Remove"
              >
                <X size={13} />
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
