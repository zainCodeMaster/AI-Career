import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { CrmApi, type ApplicationResponse, type ApplicationTransitionRequest, type ApplicationStatus } from '../api/crm';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ErrorState } from '../components/ui/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/layout/PageHeader';

const STATUS_LABEL: Record<string, string> = {
  saved: 'Saved',
  ready_to_apply: 'Ready to Apply',
  applied: 'Applied',
  application_viewed: 'Application Viewed',
  screening: 'Screening',
  interview: 'Interview',
  technical_interview: 'Technical Interview',
  final_interview: 'Final Interview',
  offer: 'Offer',
  accepted: 'Accepted',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
  expired: 'Expired',
  on_hold: 'On Hold',
};

const PRIORITY_LABEL: Record<string, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  urgent: 'Urgent',
};

const SOURCE_LABEL: Record<string, string> = {
  manual: 'Manual',
  ai: 'AI',
  automation: 'Automation',
  system: 'System',
};

const STATUS_VARIANT: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
  saved: 'default',
  ready_to_apply: 'info',
  applied: 'primary',
  application_viewed: 'info',
  screening: 'warning',
  interview: 'warning',
  technical_interview: 'warning',
  final_interview: 'warning',
  offer: 'success',
  accepted: 'success',
  rejected: 'error',
  withdrawn: 'default',
  expired: 'default',
  on_hold: 'warning',
};

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [transitionTo, setTransitionTo] = useState<string>('');
  const [transitionReason, setTransitionReason] = useState('');
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [transitionSuccess, setTransitionSuccess] = useState<string | null>(null);
  const [offerSalary, setOfferSalary] = useState('');
  const [offerCurrency, setOfferCurrency] = useState('');
  const [offerStatus, setOfferStatus] = useState('received');
  const [documentType, setDocumentType] = useState('resume');
  const [documentName, setDocumentName] = useState('');
  const [documentUrl, setDocumentUrl] = useState('');

  const { data: application, isLoading, error } = useQuery<ApplicationResponse>({
    queryKey: ['crm', 'applications', id],
    queryFn: () => CrmApi.getApplication(id!),
    enabled: !!id,
  });

  const { data: timeline } = useQuery({
    queryKey: ['crm', 'applications', id, 'timeline'],
    queryFn: () => CrmApi.getApplicationTimeline(id!),
    enabled: !!id,
  });

  const { data: offer } = useQuery({
    queryKey: ['crm', 'applications', id, 'offer'],
    queryFn: () => CrmApi.getApplicationOffer(id!),
    enabled: !!id,
  });

  const { data: recommendations } = useQuery({
    queryKey: ['crm', 'applications', id, 'recommendations'],
    queryFn: () => CrmApi.listRecommendations(id!),
    enabled: !!id,
  });

  const recommendationsList = recommendations ?? [];

  const transitionMutation = useMutation({
    mutationFn: (data: ApplicationTransitionRequest) =>
      CrmApi.transitionApplication(id!, data),
    onSuccess: () => {
      setTransitionSuccess('Status transitioned successfully');
      setTransitionError(null);
      setTransitionTo('');
      setTransitionReason('');
      queryClient.invalidateQueries({ queryKey: ['crm'] });
    },
    onError: (e: Error) => {
      setTransitionError(e.message);
      setTransitionSuccess(null);
    },
  });

  const offerMutation = useMutation({
    mutationFn: () => CrmApi.upsertApplicationOffer(id!, {
      base_salary: offerSalary ? Number(offerSalary) : null,
      currency: offerCurrency || null,
      status: offerStatus,
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['crm', 'applications', id] }),
  });

  const documentMutation = useMutation({
    mutationFn: () => CrmApi.createApplicationDocument(id!, {
      document_type: documentType,
      file_name: documentName || null,
      file_url: documentUrl || null,
    }),
    onSuccess: () => {
      setDocumentName('');
      setDocumentUrl('');
      queryClient.invalidateQueries({ queryKey: ['crm', 'applications', id] });
    },
  });

  const handleTransition = (e: React.FormEvent) => {
    e.preventDefault();
    if (!transitionTo) return;
    setTransitionError(null);
    setTransitionSuccess(null);
    transitionMutation.mutate({
      to_status: transitionTo as ApplicationStatus,
      reason: transitionReason || undefined,
    });
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-content">
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-neutral-200 border-t-primary" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-content">
        <ErrorState message={(error as Error).message} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  if (!application) {
    return (
      <div className="mx-auto max-w-content">
        <EmptyState title="Application not found" description="The application you're looking for doesn't exist or you don't have access to it." />
      </div>
    );
  }

  const app = application;

  return (
    <div className="mx-auto max-w-content">
      <Button onClick={() => navigate('/applications')} variant="ghost" size="sm" className="mb-4">
        ← Back to Applications
      </Button>

      <PageHeader
        title={app.name || 'Untitled Application'}
        description={
          <span className="flex items-center gap-2 mt-1">
            {app.job_title_snapshot || 'No job title'} · {app.company?.name || 'No company'}
            <Badge variant={STATUS_VARIANT[app.status] || 'default'}>{STATUS_LABEL[app.status] || app.status}</Badge>
          </span>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
        <Card>
          <p className="text-label text-neutral-500">Priority</p>
          <p className="text-numeric text-lg text-neutral-900 mt-2">{PRIORITY_LABEL[app.priority] || app.priority}</p>
        </Card>
        <Card>
          <p className="text-label text-neutral-500">Source</p>
          <p className="text-numeric text-lg text-neutral-900 mt-2">{SOURCE_LABEL[app.source] || app.source}</p>
        </Card>
        <Card>
          <p className="text-label text-neutral-500">Applied</p>
          <p className="text-numeric text-lg text-neutral-900 mt-2">
            {app.applied_at ? new Date(app.applied_at).toLocaleDateString() : 'Not applied'}
          </p>
        </Card>
      </div>

      {app.notes && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-2">Notes</h2>
          <p className="text-body text-neutral-700">{app.notes}</p>
        </Card>
      )}

      <Card className="mb-6">
        <h2 className="text-h3 text-neutral-900 mb-3">Status Transition</h2>
        <form onSubmit={handleTransition}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label className="text-label text-neutral-700 mb-1 block">New Status</label>
              <select
                value={transitionTo}
                onChange={(e) => setTransitionTo(e.target.value)}
                className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="">Select status…</option>
                {Object.entries(STATUS_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-label text-neutral-700 mb-1 block">Reason (optional)</label>
              <Input
                value={transitionReason}
                onChange={(e) => setTransitionReason(e.target.value)}
                placeholder="Reason for change"
              />
            </div>
            <div className="flex items-end">
              <Button type="submit" disabled={transitionMutation.isPending || !transitionTo} className="w-full">
                {transitionMutation.isPending ? 'Transitioning…' : 'Transition'}
              </Button>
            </div>
          </div>
        </form>
        {transitionError && <p className="text-body-sm text-error mt-2">{transitionError}</p>}
        {transitionSuccess && <p className="text-body-sm text-success mt-2">{transitionSuccess}</p>}
      </Card>

      {app.job && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-2">Job</h2>
          <p className="text-body">
            <strong>{app.job.title}</strong> at {app.job.company_name}
          </p>
        </Card>
      )}

      {app.company && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-2">Company</h2>
          <p className="text-body">
            <strong>{app.company.name}</strong>
            {app.company.industry && ` · ${app.company.industry}`}
            {app.company.location && ` · ${app.company.location}`}
          </p>
        </Card>
      )}

      {app.primary_contact && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-2">Primary Contact</h2>
          <p className="text-body">
            <strong>{app.primary_contact.name}</strong>
            {app.primary_contact.title && ` · ${app.primary_contact.title}`}
            {app.primary_contact.email && ` · ${app.primary_contact.email}`}
          </p>
        </Card>
      )}

      {app.interviews && app.interviews.length > 0 && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-3">Interviews</h2>
          <ul className="space-y-2">
            {app.interviews.map((inv) => (
              <li key={inv.id} className="text-body text-neutral-700">
                <strong>{inv.interview_type.replace(/_/g, ' ')}</strong> — {inv.status}
                {inv.scheduled_at && ` · ${new Date(inv.scheduled_at).toLocaleString()}`}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {app.follow_ups && app.follow_ups.length > 0 && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-3">Follow-ups</h2>
          <ul className="space-y-2">
            {app.follow_ups.map((fu) => (
              <li key={fu.id} className="text-body text-neutral-700">
                <strong>{fu.follow_up_type.replace(/_/g, ' ')}</strong> — {fu.status}
                {fu.due_at && ` · Due: ${new Date(fu.due_at).toLocaleDateString()}`}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {offer && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-2">Offer</h2>
          <p className="text-body text-neutral-700">
            Status: {offer.status}
            {offer.base_salary && ` · $${offer.base_salary.toLocaleString()}`}
            {offer.currency && ` ${offer.currency}`}
          </p>
        </Card>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <h2 className="text-h3 text-neutral-900 mb-3">Offer details</h2>
          <form className="space-y-3" onSubmit={(event) => { event.preventDefault(); offerMutation.mutate(); }}>
            <div className="grid gap-3 sm:grid-cols-2">
              <Input label="Base salary" type="number" min="0" value={offerSalary} onChange={(event) => setOfferSalary(event.target.value)} />
              <Input label="Currency" value={offerCurrency} onChange={(event) => setOfferCurrency(event.target.value)} placeholder="USD" />
            </div>
            <select aria-label="Offer status" value={offerStatus} onChange={(event) => setOfferStatus(event.target.value)} className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body">
              {['received', 'negotiating', 'accepted', 'declined', 'expired'].map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
            <Button type="submit" disabled={offerMutation.isPending}>{offerMutation.isPending ? 'Saving...' : 'Save offer'}</Button>
            {offerMutation.isError && <p className="text-body-sm text-error" role="alert">{(offerMutation.error as Error).message}</p>}
          </form>
        </Card>
        <Card>
          <h2 className="text-h3 text-neutral-900 mb-3">Application documents</h2>
          <p className="mb-3 text-body-sm text-neutral-600">Attach document metadata or an existing secure URL. Binary upload is not claimed here.</p>
          <form className="space-y-3" onSubmit={(event) => { event.preventDefault(); documentMutation.mutate(); }}>
            <select aria-label="Document type" value={documentType} onChange={(event) => setDocumentType(event.target.value)} className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body"><option value="resume">Resume</option><option value="cover_letter">Cover letter</option><option value="other">Other</option></select>
            <Input label="File name" value={documentName} onChange={(event) => setDocumentName(event.target.value)} />
            <Input label="Secure file URL" type="url" value={documentUrl} onChange={(event) => setDocumentUrl(event.target.value)} />
            <Button type="submit" disabled={documentMutation.isPending}>{documentMutation.isPending ? 'Attaching...' : 'Attach document'}</Button>
            {documentMutation.isError && <p className="text-body-sm text-error" role="alert">{(documentMutation.error as Error).message}</p>}
          </form>
          {app.documents.length > 0 && <ul className="mt-4 space-y-2">{app.documents.map((document) => <li key={document.id} className="flex items-center justify-between gap-2 border-t border-neutral-100 pt-2 text-body-sm"><span>{document.file_name || document.document_type}</span><Button size="sm" variant="secondary" onClick={() => void CrmApi.deleteApplicationDocument(document.id).then(() => queryClient.invalidateQueries({ queryKey: ['crm', 'applications', id] }))}>Remove</Button></li>)}</ul>}
        </Card>
      </div>

      {recommendationsList.length > 0 && (
        <Card className="mb-6">
          <h2 className="text-h3 text-neutral-900 mb-3">Recommendations</h2>
          <ul className="space-y-2">
            {recommendationsList.map((rec) => (
              <li key={rec.id} className="text-body text-neutral-700">
                <strong>{rec.title}</strong> — {rec.severity}
                {rec.explanation && ` · ${rec.explanation}`}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {timeline && timeline.items.length > 0 && (
        <Card>
          <h2 className="text-h3 text-neutral-900 mb-3">Timeline</h2>
          <ul className="space-y-3">
            {timeline.items.map((event) => (
              <li key={event.id} className="border-l-2 border-neutral-200 pl-4 py-1">
                <p className="text-body font-medium text-neutral-900">{event.title}</p>
                <p className="text-metadata">
                  {new Date(event.occurred_at).toLocaleString()} · {event.event_type}
                </p>
                {event.description && (
                  <p className="text-caption text-neutral-500 mt-1">{event.description}</p>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

export default ApplicationDetailPage;
