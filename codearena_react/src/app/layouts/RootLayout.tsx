import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { ErrorBoundary } from '@/shared/components/ErrorBoundary';
import { AuthProvider } from '@/app/providers/AuthProvider';

export function RootLayout() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Suspense
          fallback={
            <div className="h-screen flex items-center justify-center">
              <Loader2 className="animate-spin text-gray-400" size={32} />
            </div>
          }
        >
          <Outlet />
        </Suspense>
      </AuthProvider>
    </ErrorBoundary>
  );
}
