import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CrmApi, type ApplicationSummary, type ApplicationPriority, type ApplicationSource } from '../api/crm';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { PageHeader } from '../components/layout/PageHeader';

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'saved', label: 'Saved' },
  { value: 'ready_to_apply', label: 'Ready to Apply' },
  { value: 'applied', label: 'Applied' },
  { value: 'screening', label: 'Screening' },
  { value: 'interview', label: 'Interview' },
  { value: 'offer', label: 'Offer' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'withdrawn', label: 'Withdrawn' },
  { value: 'on_hold', label: 'On Hold' },
] as const;

const PRIORITY_OPTIONS = [
  { value: '', label: 'All priorities' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
] as const;

export function ApplicationsPage() {
  const [status, setStatus] = useState<string>('');
  const [priority, setPriority] = useState<ApplicationPriority>('medium');
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data, isLoading, error: listError, refetch } = useQuery({
    queryKey: ['crm', 'applications', { status, priority, search }],
    queryFn: () =>
      CrmApi.listApplications({
        status: status || undefined,
        priority: priority || undefined,
        search: search || undefined,
        page_size: 50,
      }),
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; notes?: string; priority?: ApplicationPriority; source?: ApplicationSource }) =>
      CrmApi.createApplication(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm'] });
      setShowForm(false);
      setName('');
      setCompanyName('');
      setError(null);
    },
    onError: (e: Error) => {
      setError(e.message);
    },
  });

  const applications = data?.items ?? [];

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createMutation.mutate({
      name: name.trim(),
      notes: companyName || undefined,
      priority: 'medium',
      source: 'manual',
    });
  };

  return (
    <div className="mx-auto max-w-content">
      <PageHeader
        title="Applications"
        description={`${data?.total ?? 0} total`}
        action={
          <Button onClick={() => setShowForm(!showForm)} size="sm">
            {showForm ? 'Cancel' : 'New Application'}
          </Button>
        }
      />

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate}>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Input
                label="Application name"
                placeholder="e.g. Senior Engineer at Acme"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <Input
                label="Company / notes"
                placeholder="Company or notes"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>
            {error && <p className="text-body-sm text-error mt-2">{error}</p>}
            <div className="mt-4 flex gap-2">
              <Button type="submit" size="sm">Create</Button>
              <Button type="button" onClick={() => setShowForm(false)} variant="secondary" size="sm">Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      <Card className="mb-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Input
            placeholder="Search by name, company, job title…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as ApplicationPriority)}
            className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            {PRIORITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="mt-3">
          <Button onClick={() => refetch()} variant="secondary" size="sm">Refresh</Button>
        </div>
      </Card>

      {listError && <ErrorState message={(listError as Error).message} onRetry={refetch} className="mb-4" />}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-neutral-200 border-t-primary" />
        </div>
      )}

      {!isLoading && applications.length === 0 && (
        <EmptyState
          title="No applications yet"
          description="Add your first application to start tracking your career pipeline."
          action={
            <Button onClick={() => setShowForm(true)} size="sm">New Application</Button>
          }
        />
      )}

      <div className="space-y-3">
        {applications.map((app: ApplicationSummary) => (
          <Card
            key={app.id}
            className="cursor-pointer hover:border-neutral-300 transition-colors"
            onClick={() => navigate(`/applications/${app.id}`)}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-h3 text-neutral-900 truncate">{app.name || 'Untitled Application'}</h3>
                <p className="text-body text-neutral-500 mt-1">
                  {app.job_title_snapshot || 'No job title'} · {app.status.replace(/_/g, ' ')}
                </p>
                <p className="text-metadata mt-1">
                  Priority: {app.priority} · Source: {app.source}
                </p>
                {app.deadline_at && (
                  <p className="text-metadata mt-1">
                    Deadline: {new Date(app.deadline_at).toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className="flex flex-col items-end gap-2 shrink-0">
                <Badge variant="primary">{app.status.replace(/_/g, ' ')}</Badge>
                <span className="text-metadata">{app.priority}</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default ApplicationsPage;
