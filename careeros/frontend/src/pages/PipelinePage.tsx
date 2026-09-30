import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CrmApi, type PipelineResponse, type ApplicationSummary, type ApplicationStatus } from '../api/crm';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { PageHeader } from '../components/layout/PageHeader';

const ALL_STATUSES: ApplicationStatus[] = [
  'saved',
  'ready_to_apply',
  'applied',
  'application_viewed',
  'screening',
  'interview',
  'technical_interview',
  'final_interview',
  'offer',
  'accepted',
  'rejected',
  'withdrawn',
  'expired',
  'on_hold',
];

const STATUS_LABEL: Record<ApplicationStatus, string> = {
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

export function PipelinePage() {
  const [transitioningId, setTransitioningId] = useState<string | null>(null);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: pipeline, isLoading, error } = useQuery<PipelineResponse>({
    queryKey: ['crm', 'pipeline'],
    queryFn: CrmApi.getPipeline,
  });

  const transitionMutation = useMutation({
    mutationFn: ({ applicationId, toStatus }: { applicationId: string; toStatus: ApplicationStatus }) =>
      CrmApi.transitionApplication(applicationId, { to_status: toStatus }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm'] });
      setTransitioningId(null);
      setTransitionError(null);
    },
    onError: (e: Error) => {
      setTransitionError(e.message);
      setTransitioningId(null);
    },
  });

  const handleTransition = (applicationId: string, toStatus: ApplicationStatus) => {
    setTransitioningId(applicationId);
    setTransitionError(null);
    transitionMutation.mutate({ applicationId, toStatus });
  };

  return (
    <div className="mx-auto max-w-content">
      <PageHeader title="Pipeline" description="Drag-free status management" />

      {error && <ErrorState message={(error as Error).message} onRetry={() => window.location.reload()} className="mb-4" />}

      {transitionError && (
        <ErrorState message={transitionError} className="mb-4" />
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-neutral-200 border-t-primary" />
        </div>
      )}

      {!isLoading && pipeline && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {pipeline.stages.map((stage) => (
            <div key={stage.status} className="rounded-md border border-neutral-200 bg-surface-muted p-3">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-h3 text-neutral-900">{stage.label}</h3>
                <span className="text-metadata text-neutral-500">{stage.count}</span>
              </div>
              <div className="space-y-2">
                {stage.applications.map((app: ApplicationSummary) => (
                  <Card
                    key={app.id}
                    className="cursor-pointer hover:border-neutral-300 transition-colors"
                    onClick={() => navigate(`/applications/${app.id}`)}
                  >
                    <p className="text-body font-medium text-neutral-900 truncate">{app.name || 'Untitled'}</p>
                    <p className="text-metadata mt-1 truncate">{app.job_title_snapshot || 'No job title'}</p>
                    <div className="mt-3" onClick={(e) => e.stopPropagation()}>
                      <select
                        value=""
                        onChange={(e) => {
                          const target = e.target.value as ApplicationStatus;
                          if (target && target !== app.status) {
                            handleTransition(app.id, target);
                          }
                        }}
                        disabled={transitioningId === app.id}
                        className="w-full rounded-md border border-neutral-200 bg-white px-2 py-1 text-caption focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50"
                      >
                        <option value="">Move to…</option>
                        {ALL_STATUSES.filter((s) => s !== app.status).map((s) => (
                          <option key={s} value={s}>
                            {STATUS_LABEL[s]}
                          </option>
                        ))}
                      </select>
                    </div>
                  </Card>
                ))}
                {stage.applications.length === 0 && (
                  <p className="text-caption text-neutral-400 text-center py-4">No applications</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default PipelinePage;
