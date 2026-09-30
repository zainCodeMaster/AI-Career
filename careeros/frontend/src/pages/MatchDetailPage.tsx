import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { MatchingApi, type JobMatch } from '../api/matching';
import { JobsApi, type JobDetail } from '../api/jobs';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { PageHeader } from '../components/layout/PageHeader';
import { Button } from '../components/ui/Button';
import { CrmApi } from '../api/crm';

export function MatchDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [match, setMatch] = useState<JobMatch | null>(null);
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tracking, setTracking] = useState(false);

  const load = async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const [matchResult, jobResult] = await Promise.all([
        MatchingApi.detail(jobId),
        JobsApi.get(jobId),
      ]);
      setMatch(matchResult);
      setJob(jobResult);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load match details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // load is scoped to the route's job id.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  if (loading) return <div className="mx-auto max-w-content"><PageHeader title="Match details" /><p className="py-12 text-center text-body text-neutral-600">Loading match details...</p></div>;
  if (error || !match || !job) return <div className="mx-auto max-w-content"><PageHeader title="Match details" /><ErrorState message={error || 'Match details are unavailable.'} onRetry={() => void load()} /></div>;

  const trackApplication = async () => {
    setTracking(true);
    setError(null);
    try {
      const application = await CrmApi.createApplication({
        name: `${job.title} at ${job.company_name}`,
        job_id: job.id,
        job_title_snapshot: job.title,
        source: 'manual',
        priority: 'medium',
      });
      window.location.href = `/applications/${application.id}`;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to track application');
    } finally {
      setTracking(false);
    }
  };

  return (
    <div className="mx-auto max-w-content space-y-5">
      <PageHeader title={job.title} description={`${job.company_name} · ${[job.city, job.province].filter(Boolean).join(', ') || 'Location not listed'}`} />
      <div className="flex flex-wrap gap-2"><Button onClick={trackApplication} disabled={tracking}>{tracking ? 'Creating application...' : 'Track application'}</Button><Link to={`/jobs/${job.id}`} className="inline-flex items-center rounded-md border border-neutral-200 px-3 py-2 text-body-sm text-neutral-700 hover:bg-neutral-50">View job</Link></div>
      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-label text-neutral-500">Backend match score</p>
            <p className="text-numeric mt-1 text-3xl font-semibold text-primary-dark">{Math.round(match.overall_score)}%</p>
          </div>
          <Link to="/matches" className="text-body-sm text-primary hover:underline">Back to matches</Link>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {Object.entries(match.breakdown).map(([key, value]) => <div key={key} className="rounded-md bg-neutral-50 p-3"><p className="text-caption capitalize text-neutral-500">{key.replace('_', ' ')}</p><p className="text-numeric mt-1 text-lg text-neutral-900">{Math.round(value)}%</p></div>)}
        </div>
      </Card>
      <Card>
        <h2 className="text-h3 text-neutral-900">Why this match</h2>
        <ul className="mt-3 space-y-2 text-body text-neutral-700">{match.explanation.map((item) => <li key={item}>{item}</li>)}</ul>
      </Card>
      <div className="grid gap-5 md:grid-cols-2">
        <Card><h2 className="text-h3 text-neutral-900">Matched skills</h2><p className="mt-3 text-body text-neutral-700">{match.matched_skills.length ? match.matched_skills.join(', ') : 'No matched skills returned.'}</p></Card>
        <Card><h2 className="text-h3 text-neutral-900">Skills to strengthen</h2><p className="mt-3 text-body text-neutral-700">{match.missing_skills.length ? match.missing_skills.join(', ') : 'No missing skills returned.'}</p></Card>
      </div>
    </div>
  );
}