import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { JobsApi, type JobDetail } from '../api/jobs';
import { MatchingApi, type JobMatch } from '../api/matching';
import { CrmApi } from '../api/crm';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { PageHeader } from '../components/layout/PageHeader';

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [match, setMatch] = useState<JobMatch | null>(null);
  const [saved, setSaved] = useState(false);
  const [applicationName, setApplicationName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [applying, setApplying] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [jobResult, matchResult, savedJobs] = await Promise.all([
        JobsApi.get(id),
        MatchingApi.detail(id).catch(() => null),
        JobsApi.saved(),
      ]);
      setJob(jobResult);
      setMatch(matchResult);
      setSaved(savedJobs.some((item) => item.job.id === id));
      setApplicationName(`${jobResult.title} at ${jobResult.company_name}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load job details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // load is scoped to the route job id.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const toggleSave = async () => {
    if (!id) return;
    setSaving(true);
    setError(null);
    try {
      if (saved) await JobsApi.unsave(id);
      else await JobsApi.save(id);
      setSaved(!saved);
      setMessage(saved ? 'Job removed from saved jobs.' : 'Job saved.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to update saved job');
    } finally {
      setSaving(false);
    }
  };

  const trackApplication = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id || !job || !applicationName.trim()) return;
    setApplying(true);
    setError(null);
    try {
      const application = await CrmApi.createApplication({
        name: applicationName.trim(),
        job_id: id,
        job_title_snapshot: job.title,
        source: 'manual',
        priority: 'medium',
      });
      setMessage('Application tracked successfully.');
      navigate(`/applications/${application.id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to track application');
    } finally {
      setApplying(false);
    }
  };

  if (loading) return <div className="mx-auto max-w-content"><PageHeader title="Job details" /><p className="py-12 text-center text-body text-neutral-600">Loading job details...</p></div>;
  if (error && !job) return <div className="mx-auto max-w-content"><PageHeader title="Job details" /><ErrorState message={error} onRetry={() => void load()} /></div>;
  if (!job) return null;

  return (
    <div className="mx-auto max-w-content space-y-5">
      <PageHeader title={job.title} description={`${job.company_name} · ${[job.city, job.province, job.country].filter(Boolean).join(', ') || 'Location not listed'}`} action={<Button variant="secondary" onClick={() => navigate('/jobs')}>Back to jobs</Button>} />
      {error && <ErrorState message={error} className="mb-4" />}
      {message && <p className="rounded-md border border-primary-light bg-primary-light p-3 text-body-sm text-primary-dark" role="status">{message}</p>}
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => void toggleSave()} disabled={saving}>{saving ? 'Saving...' : saved ? 'Remove saved job' : 'Save job'}</Button>
        {match && <Link to={`/matches/${job.id}`} className="inline-flex items-center rounded-md border border-neutral-200 px-3 py-2 text-body-sm text-neutral-700 hover:bg-neutral-50">View match details ({Math.round(match.overall_score)}%)</Link>}
        {job.source_url && <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center rounded-md border border-neutral-200 px-3 py-2 text-body-sm text-neutral-700 hover:bg-neutral-50">Open source</a>}
      </div>
      <Card>
        <div className="grid gap-3 text-body sm:grid-cols-3">
          <div><p className="text-caption text-neutral-500">Workplace</p><p>{job.is_remote ? 'Remote' : job.workplace_type || 'Not specified'}</p></div>
          <div><p className="text-caption text-neutral-500">Employment</p><p>{job.employment_type || 'Not specified'}</p></div>
          <div><p className="text-caption text-neutral-500">Source</p><p>{job.source}</p></div>
        </div>
      </Card>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <Card className="space-y-5">
          <section><h2 className="text-h3 text-neutral-900">Description</h2><p className="mt-2 whitespace-pre-line text-body text-neutral-700">{job.description || 'No description provided by the source.'}</p></section>
          <section><h2 className="text-h3 text-neutral-900">Requirements</h2><p className="mt-2 whitespace-pre-line text-body text-neutral-700">{job.requirements || 'No requirements provided by the source.'}</p></section>
          {job.responsibilities && <section><h2 className="text-h3 text-neutral-900">Responsibilities</h2><p className="mt-2 whitespace-pre-line text-body text-neutral-700">{job.responsibilities}</p></section>}
        </Card>
        <Card>
          <h2 className="text-h3 text-neutral-900">Track application</h2>
          <p className="mt-2 text-body-sm text-neutral-600">Create a real CRM application linked to this job.</p>
          <form onSubmit={trackApplication} className="mt-4 space-y-3">
            <Input label="Application name" value={applicationName} onChange={(event) => setApplicationName(event.target.value)} required />
            <Button type="submit" disabled={applying || !applicationName.trim()} className="w-full">{applying ? 'Creating...' : 'Track application'}</Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
