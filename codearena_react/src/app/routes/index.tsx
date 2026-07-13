import { lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RootLayout } from '@/app/layouts/RootLayout';
import { ArenaLayout } from '@/app/layouts/ArenaLayout';
import { ProtectedRoute } from './ProtectedRoute';

// Lazy-loaded pages — each gets its own chunk
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'));
const ProblemsPage = lazy(() => import('@/pages/problems/ProblemsPage'));
const ProblemPage = lazy(() => import('@/pages/problems/ProblemPage'));
const WorkspacesPage = lazy(() => import('@/pages/workspaces/WorkspacesPage'));
const WorkspacePage = lazy(() => import('@/pages/workspaces/WorkspacePage'));
const NotFoundPage = lazy(() => import('@/pages/not-found/NotFoundPage'));

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      // ── Public routes ──────────────────────────────
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },

      // ── Protected routes ───────────────────────────
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <ArenaLayout />,
            children: [
              { index: true, element: <Navigate to="/problems" replace /> },
              { path: 'problems', element: <ProblemsPage /> },
              { path: 'problems/:slug', element: <ProblemPage /> },
              { path: 'workspaces', element: <WorkspacesPage /> },
              { path: 'workspaces/:workspaceId', element: <WorkspacePage /> },
            ],
          },
        ],
      },

      // ── Catch-all ──────────────────────────────────
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
