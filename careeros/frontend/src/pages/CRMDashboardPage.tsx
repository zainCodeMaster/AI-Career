import { useQuery } from '@tanstack/react-query';
import { CrmApi, type ApplicationStatsResponse, type PipelineResponse, type FunnelResponse } from '../api/crm';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { PageHeader } from '../components/layout/PageHeader';
import { Skeleton } from '../components/ui/Skeleton';

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <Card>
      <p className="text-label text-neutral-500">{label}</p>
      <p className="text-numeric text-2xl text-neutral-900 mt-2">{value}</p>
    </Card>
  );
}

export function CRMDashboardPage() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery<ApplicationStatsResponse>({
    queryKey: ['crm', 'dashboard'],
    queryFn: CrmApi.getDashboardStats,
  });

  const { data: pipeline, isLoading: pipelineLoading, error: pipelineError } = useQuery<PipelineResponse>({
    queryKey: ['crm', 'pipeline'],
    queryFn: CrmApi.getPipeline,
  });

  const { data: analytics, isLoading: analyticsLoading, error: analyticsError } = useQuery<FunnelResponse>({
    queryKey: ['crm', 'analytics'],
    queryFn: CrmApi.getAnalytics,
  });

  const hasError = statsError || pipelineError || analyticsError;
  const errorMessage = (statsError || pipelineError || analyticsError) as Error | undefined;

  if (statsLoading || pipelineLoading || analyticsLoading) {
    return (
      <div className="mx-auto max-w-content">
        <PageHeader title="CRM Dashboard" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-8 w-12 mt-2" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="mx-auto max-w-content">
        <PageHeader title="CRM Dashboard" />
        <ErrorState message={errorMessage?.message || "Failed to load dashboard"} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  if (!stats || !pipeline || !analytics) {
    return (
      <div className="mx-auto max-w-content">
        <PageHeader title="CRM Dashboard" />
        <EmptyState title="No data available" description="Dashboard data will appear here once you have applications." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-content">
      <PageHeader title="CRM Dashboard" description="Career pipeline overview and analytics" />

      <section className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total Applications" value={stats.total} />
        <StatCard label="Active" value={stats.active} />
        <StatCard label="Offers" value={stats.offer} />
        <StatCard label="Accepted" value={stats.accepted} />
      </section>

      <section className="mb-6">
        <h2 className="text-h3 text-neutral-900 mb-3">Pipeline</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {pipeline.stages.map((stage) => (
            <Card key={stage.status}>
              <p className="text-label text-neutral-500">{stage.label}</p>
              <p className="text-numeric text-2xl text-neutral-900 mt-2">{stage.count}</p>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-h3 text-neutral-900 mb-3">Analytics</h2>
        <Card>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-label text-neutral-500">Total Applications</p>
              <p className="text-numeric text-lg text-neutral-900 mt-1">{analytics.total_applications}</p>
            </div>
            <div>
              <p className="text-label text-neutral-500">Total Offers</p>
              <p className="text-numeric text-lg text-neutral-900 mt-1">{analytics.total_offers}</p>
            </div>
            <div>
              <p className="text-label text-neutral-500">Total Rejections</p>
              <p className="text-numeric text-lg text-neutral-900 mt-1">{analytics.total_rejections}</p>
            </div>
            <div>
              <p className="text-label text-neutral-500">Avg Days to Offer</p>
              <p className="text-numeric text-lg text-neutral-900 mt-1">
                {analytics.average_days_to_offer != null ? analytics.average_days_to_offer.toFixed(1) : "—"}
              </p>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

export default CRMDashboardPage;
