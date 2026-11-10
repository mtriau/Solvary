import { useState, type FormEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import { Loader2, Sparkles } from 'lucide-react';
import { useAssistStream } from '../hooks/useAssistStream';

interface Props {
  problemId: string;
  /** The buffer the user is working on — sent along so hints are concrete. */
  code: string;
  language: string;
  /** Free-text summary of the latest verdict, e.g. "wrong_answer on test 3". */
  verdictSummary: string | null;
  /** Set on the interview review page: unlocks the session's private problems. */
  interviewSessionId?: string;
}

const QUICK_PROMPTS = [
  { label: 'Explain the problem', question: 'Explain what this problem is asking, in plain words.' },
  { label: 'Give me a hint', question: 'Give me one hint toward a solution, without the full answer.' },
  { label: 'Why did it fail?', question: 'Why did my code get this verdict? Point me at the bug.', needsVerdict: true },
];

/** "Ask AI" — tutoring assistant over the problem + current code (design decision #12). */
export function AssistPanel({
  problemId,
  code,
  language,
  verdictSummary,
  interviewSessionId,
}: Props) {
  const [question, setQuestion] = useState('');
  const { answer, isStreaming, error, ask } = useAssistStream();

  const send = (q: string) => {
    if (!q.trim() || isStreaming) return;
    void ask({
      question: q.trim(),
      problem_id: problemId,
      code: code.trim() ? code : undefined,
      language,
      verdict: verdictSummary ?? undefined,
      interview_session_id: interviewSessionId,
    });
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    send(question);
  };

  return (
    <div className="py-3 space-y-3 text-sm">
      <div className="flex flex-wrap gap-1.5">
        {QUICK_PROMPTS.filter((p) => !p.needsVerdict || verdictSummary).map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => send(p.question)}
            disabled={isStreaming}
            className="px-2 py-0.5 rounded-full border border-gray-200 bg-gray-50 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-50"
          >
            {p.label}
          </button>
        ))}
      </div>

      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about the problem or your code…"
          maxLength={2000}
          className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={isStreaming || !question.trim()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {isStreaming ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          Ask
        </button>
      </form>

      {error && (
        <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {(answer || isStreaming) && (
        <div className="prose prose-sm max-w-none text-gray-700 border border-gray-200 rounded-lg px-4 py-3 bg-white [&_pre]:bg-gray-50 [&_pre]:border [&_pre]:border-gray-200 [&_pre]:rounded-lg [&_pre]:p-3">
          <ReactMarkdown>{answer || '…'}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
