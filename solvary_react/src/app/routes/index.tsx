import { lazy } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { RootLayout } from '@/app/layouts/RootLayout';
import { ArenaLayout } from '@/app/layouts/ArenaLayout';
import { ProtectedRoute } from './ProtectedRoute';

// Lazy-loaded pages — each gets its own chunk
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'));
const HomePage = lazy(() => import('@/pages/home/HomePage'));
const ProblemsPage = lazy(() => import('@/pages/problems/ProblemsPage'));
const ProblemPage = lazy(() => import('@/pages/problems/ProblemPage'));
const DrillsPage = lazy(() => import('@/pages/drills/DrillsPage'));
const DrillPage = lazy(() => import('@/pages/drills/DrillPage'));
const WorkspacesPage = lazy(() => import('@/pages/workspaces/WorkspacesPage'));
const WorkspacePage = lazy(() => import('@/pages/workspaces/WorkspacePage'));
const InterviewsPage = lazy(() => import('@/pages/interviews/InterviewsPage'));
const InterviewSessionPage = lazy(() => import('@/pages/interviews/InterviewSessionPage'));
const InterviewReviewPage = lazy(() => import('@/pages/interviews/InterviewReviewPage'));
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
              { index: true, element: <HomePage /> },
              { path: 'problems', element: <ProblemsPage /> },
              { path: 'problems/:slug', element: <ProblemPage /> },
              { path: 'drills', element: <DrillsPage /> },
              { path: 'drills/:slug', element: <DrillPage /> },
              { path: 'workspaces', element: <WorkspacesPage /> },
              { path: 'workspaces/:workspaceId', element: <WorkspacePage /> },
              { path: 'interviews', element: <InterviewsPage /> },
              { path: 'interviews/sessions/:sessionId', element: <InterviewSessionPage /> },
              {
                path: 'interviews/sessions/:sessionId/review',
                element: <InterviewReviewPage />,
              },
            ],
          },
        ],
      },

      // ── Catch-all ──────────────────────────────────
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
