/**
 * Web Speech API — recognition side. TypeScript's lib.dom ships the
 * `SpeechRecognitionResult*` types but not the `SpeechRecognition`
 * constructor (Chrome exposes it as `webkitSpeechRecognition`). Own names
 * are used so this never collides with a future lib.dom addition.
 */

interface SolvarySpeechRecognitionAlternative {
  readonly transcript: string;
  readonly confidence: number;
}

interface SolvarySpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly length: number;
  item(index: number): SolvarySpeechRecognitionAlternative;
  [index: number]: SolvarySpeechRecognitionAlternative;
}

interface SolvarySpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SolvarySpeechRecognitionResult;
  [index: number]: SolvarySpeechRecognitionResult;
}

interface SolvarySpeechRecognitionEvent extends Event {
  readonly resultIndex: number;
  readonly results: SolvarySpeechRecognitionResultList;
}

interface SolvarySpeechRecognitionErrorEvent extends Event {
  /** "not-allowed" | "no-speech" | "aborted" | "network" | "audio-capture" | … */
  readonly error: string;
  readonly message?: string;
}

interface SolvarySpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onstart: ((this: SolvarySpeechRecognition, ev: Event) => void) | null;
  onend: ((this: SolvarySpeechRecognition, ev: Event) => void) | null;
  onerror: ((this: SolvarySpeechRecognition, ev: SolvarySpeechRecognitionErrorEvent) => void) | null;
  onresult: ((this: SolvarySpeechRecognition, ev: SolvarySpeechRecognitionEvent) => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

interface SolvarySpeechRecognitionCtor {
  new (): SolvarySpeechRecognition;
}

interface Window {
  SpeechRecognition?: SolvarySpeechRecognitionCtor;
  webkitSpeechRecognition?: SolvarySpeechRecognitionCtor;
}
