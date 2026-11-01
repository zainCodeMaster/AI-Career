import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/layout/PageHeader';
import { AlertTriangle } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="mx-auto max-w-content">
      <PageHeader title="Page Not Found" description="The page you&apos;re looking for doesn&apos;t exist." />
      <Card className="max-w-md mx-auto text-center py-12">
        <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle size={24} className="text-error" aria-hidden="true" />
        </div>
        <h2 className="text-h3 text-text-primary mb-2">Page Not Found</h2>
        <p className="text-body text-text-muted mb-6">
          We couldn&apos;t find the page you&apos;re looking for. It may have been moved or deleted.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-3">
          <Link to="/dashboard">
            <Button variant="primary">Go to Dashboard</Button>
          </Link>
          <Link to="/jobs">
            <Button variant="secondary">Browse Jobs</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
