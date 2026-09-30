import { useEffect, useState } from 'react';
import { JobsApi, type DiscoveryRunSummary, type SourceHealthEntry, type SourceSummary } from '../api/jobs';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { PageHeader } from '../components/layout/PageHeader';

function formatDate(value: string | null): string {
  if (!value) return 'Never';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown' : date.toLocaleString();
}

export function JobDiscoveryPage() {
  const [sources, setSources] = useState<SourceSummary[]>([]);
  const [health, setHealth] = useState<SourceHealthEntry[]>([]);
  const [runs, setRuns] = useState<DiscoveryRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sourceResult, healthResult, runResult] = await Promise.all([
        JobsApi.sources(),
        JobsApi.sourceHealth(),
        JobsApi.discoveryRuns({ page: 1, page_size: 20 }),
      ]);
      setSources(sourceResult);
      setHealth(healthResult.sources);
      setRuns(runResult.items);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load discovery status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  if (loading) return <div className="mx-auto max-w-content"><PageHeader title="Job Discovery" /><p className="py-12 text-center text-body text-neutral-600">Loading source status...</p></div>;
  if (error) return <div className="mx-auto max-w-content"><PageHeader title="Job Discovery" /><ErrorState message={error} onRetry={() => void load()} /></div>;

  return (
    <div className="mx-auto max-w-content space-y-5">
      <PageHeader title="Job Discovery" description="Inspect configured sources, their latest health, and real discovery run history." action={<Button onClick={() => void load()} variant="secondary">Refresh status</Button>} />
      <Card>
        <h2 className="text-h3 text-neutral-900">Source health</h2>
        {health.length === 0 ? <EmptyState title="No source health data" description="No configured source status was returned by the backend." /> : <div className="mt-3 space-y-2">{health.map((entry) => <div key={entry.source_id} className="rounded-md border border-neutral-200 p-3"><div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-body font-medium text-neutral-900">{entry.source_name}</p><p className="text-caption text-neutral-500">Last run: {formatDate(entry.last_run_at)} · {entry.total_jobs_discovered} jobs discovered</p></div><span className="rounded-full bg-neutral-100 px-2 py-1 text-caption capitalize text-neutral-700">{entry.status}</span></div>{entry.last_error && <p className="mt-2 text-body-sm text-error">{entry.last_error}</p>}</div>)}</div>}
      </Card>
      <Card>
        <h2 className="text-h3 text-neutral-900">Configured sources</h2>
        {sources.length === 0 ? <EmptyState title="No configured sources" description="The backend returned no job source metadata." /> : <div className="mt-3 grid gap-3 md:grid-cols-2">{sources.map((source) => <div key={source.id} className="rounded-md border border-neutral-200 p-3"><p className="text-body font-medium text-neutral-900">{source.name}</p><p className="mt-1 text-caption text-neutral-500">{source.category} · {source.integration_method} · {source.country}</p><p className="mt-2 text-body-sm text-neutral-700">{source.enabled ? 'Enabled' : 'Disabled'} · Last success: {formatDate(source.last_success_at)}</p></div>)}</div>}
      </Card>
      <Card>
        <h2 className="text-h3 text-neutral-900">Discovery history</h2>
        {runs.length === 0 ? <EmptyState title="No discovery runs" description="Run discovery from the Jobs page to create history." /> : <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[640px] text-left text-body-sm"><thead><tr className="border-b border-neutral-200 text-caption text-neutral-500"><th className="px-3 py-2">Started</th><th className="px-3 py-2">Status</th><th className="px-3 py-2">Found</th><th className="px-3 py-2">Created</th><th className="px-3 py-2">Errors</th></tr></thead><tbody>{runs.map((run) => <tr key={run.id} className="border-b border-neutral-100"><td className="px-3 py-2">{formatDate(run.started_at)}</td><td className="px-3 py-2 capitalize">{run.status}</td><td className="px-3 py-2">{run.jobs_found}</td><td className="px-3 py-2">{run.jobs_created}</td><td className="px-3 py-2">{run.error_count}</td></tr>)}</tbody></table></div>}
      </Card>
    </div>
  );
}
