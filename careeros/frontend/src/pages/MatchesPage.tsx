import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MatchingApi, type MatchFeedItem } from '../api/matching';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { PageHeader } from '../components/layout/PageHeader';

export function MatchesPage() {
  const [items, setItems] = useState<MatchFeedItem[]>([]);
  const [profileCompleteness, setProfileCompleteness] = useState('partial');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMatches = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await MatchingApi.list({ page: 1, page_size: 20 });
      setItems(response.items);
      setProfileCompleteness(response.profile_completeness);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load matches');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadMatches(); }, []);

  return (
    <div className="mx-auto max-w-content">
      <PageHeader title="Job Matches" description={`Ranked opportunities based on your profile (${profileCompleteness} profile).`} />
      {loading && <div className="py-12 text-center text-body text-neutral-600">Loading matches...</div>}
      {!loading && error && <ErrorState message={error} onRetry={() => void loadMatches()} />}
      {!loading && !error && items.length === 0 && <EmptyState title="No matches yet" description="Complete your career profile and refresh job discovery to generate matches." />}
      {!loading && !error && (
        <div className="space-y-3">
          {items.map(({ job, match }) => (
            <Card key={job.id}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <h2 className="text-h3 text-neutral-900">{job.title}</h2>
                  <p className="mt-1 text-body text-neutral-700">{job.company_name}</p>
                  <p className="mt-1 text-metadata">{[job.city, job.province].filter(Boolean).join(', ') || 'Location not listed'}{job.is_remote ? ' · Remote' : ''}</p>
                  <ul className="mt-3 space-y-1 text-body-sm text-neutral-700">
                    {match.explanation.slice(0, 3).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                  <Link to={`/matches/${job.id}`} className="mt-3 inline-block text-body-sm text-primary hover:underline">View match details</Link>
                </div>
                <div className="flex shrink-0 flex-col items-start gap-2 sm:items-end">
                  <span className="text-numeric text-2xl font-semibold text-primary-dark">{Math.round(match.overall_score)}%</span>
                  {job.source_url && <a className="text-body-sm text-primary hover:underline" href={job.source_url} target="_blank" rel="noopener noreferrer">View original</a>}
                  <Link className="text-body-sm text-primary hover:underline" to={`/matches/${job.id}`}>View match details</Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
      {!loading && !error && items.length > 0 && <Button className="mt-5" variant="secondary" onClick={() => void loadMatches()}>Refresh matches</Button>}
    </div>
  );
}
