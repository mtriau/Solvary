import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Experimental React-Compiler-era rules; they flag the external-store
      // subscription patterns our Yjs/awareness integration is built on
      // (setState inside provider event-effects, Y.Doc construction in
      // effects). Revisit if/when we adopt the React Compiler.
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/refs': 'off',
      // HMR-granularity hint, not a correctness issue; constant exports
      // (route lazy() consts, context hooks) are idiomatic here
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
])
