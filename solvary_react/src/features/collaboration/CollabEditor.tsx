import { useEffect, useRef, useState } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import { MonacoBinding } from 'y-monaco';
import * as Y from 'yjs';
import type { CollabState } from './useCollab';

const EXT_LANGUAGES: Record<string, string> = {
  py: 'python',
  js: 'javascript',
  ts: 'typescript',
  json: 'json',
  md: 'markdown',
  html: 'html',
  css: 'css',
};

export function languageForPath(path: string): string {
  const ext = path.split('.').pop() ?? '';
  return EXT_LANGUAGES[ext] ?? 'plaintext';
}

interface Props {
  collab: CollabState;
  fileId: string;
  path: string;
  readOnly: boolean;
}

/** Monaco bound to the file's Y.Text via y-monaco. Keyed by fileId from the
 * parent so each file switch remounts cleanly (binding per mount). */
export default function CollabEditor({ collab, fileId, path, readOnly }: Props) {
  const bindingRef = useRef<MonacoBinding | null>(null);
  const [mapVersion, setMapVersion] = useState(0);

  const filesMap = collab.doc.getMap<Y.Text>('files');
  const ytext = filesMap.get(fileId);

  // A just-created file's Y.Text may still be in flight — re-render on map changes
  useEffect(() => {
    const onChange = () => setMapVersion((v) => v + 1);
    filesMap.observe(onChange);
    return () => filesMap.unobserve(onChange);
  }, [filesMap]);

  useEffect(() => () => bindingRef.current?.destroy(), [fileId]);

  if (!ytext) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400 text-sm">
        Loading file… {mapVersion ? '' : ''}
      </div>
    );
  }

  const onMount: OnMount = (editor) => {
    const model = editor.getModel();
    if (!model) return;
    bindingRef.current = new MonacoBinding(
      ytext,
      model,
      new Set([editor]),
      collab.provider.awareness,
    );
  };

  return (
    <Editor
      height="100%"
      language={languageForPath(path)}
      onMount={onMount}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        scrollBeyondLastLine: false,
        automaticLayout: true,
      }}
    />
  );
}
