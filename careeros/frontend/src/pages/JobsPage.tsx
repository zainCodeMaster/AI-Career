import { useEffect, useState } from 'react';
import { JobsApi, type JobSummary, type SourceSummary } from '../api/jobs';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { PageHeader } from '../components/layout/PageHeader';
import { Badge } from '../components/ui/Badge';
import { SkeletonCard } from '../components/ui/Skeleton';
import { Briefcase, MapPin, Building2, DollarSign, Globe, Filter, X, Search, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function JobsPage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState('');
  const [city, setCity] = useState('');
  const [workplace, setWorkplace] = useState<'any' | 'remote' | 'hybrid' | 'onsite'>('any');
  const [employmentType, setEmploymentType] = useState('');
  const [eligibility, setEligibility] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [sources, setSources] = useState<SourceSummary[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const fetchJobs = async (pageNum = 1) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await JobsApi.list({
        keyword: keyword || undefined,
        city: city || undefined,
        remote: workplace === 'remote',
        hybrid: workplace === 'hybrid',
        onsite: workplace === 'onsite',
        employment_type: employmentType || undefined,
        is_pakistan: eligibility === '' ? undefined : eligibility === 'eligible',
        page: pageNum,
        page_size: 20,
      });
      if (pageNum === 1) {
        setJobs(resp.items);
      } else {
        setJobs((prev) => [...prev, ...resp.items]);
      }
      setTotal(resp.total);
      setHasMore(pageNum * 20 < resp.total);
      setPage(pageNum);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSaved = async () => {
    try {
      const resp = await JobsApi.saved();
      setSavedIds(new Set(resp.map((s) => s.job.id)));
    } catch {
      // ignore — not critical
    }
  };

  const fetchSources = async () => {
    try {
      setSources(await JobsApi.sources());
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchJobs();
    fetchSaved();
    fetchSources();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleSave = async (jobId: string) => {
    try {
      if (savedIds.has(jobId)) {
        await JobsApi.unsave(jobId);
        setSavedIds((prev) => {
          const next = new Set(prev);
          next.delete(jobId);
          return next;
        });
      } else {
        await JobsApi.save(jobId);
        setSavedIds((prev) => new Set(prev).add(jobId));
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const runDiscovery = async () => {
    setError(null);
    try {
      const result = await JobsApi.triggerDiscovery();
      await fetchJobs();
      // Use a toast instead of alert in production
      alert(
        `Discovery: ${result.sources_succeeded}/${result.sources_attempted} sources ok; ` +
          `${result.jobs_created} new, ${result.jobs_updated} updated, ${result.jobs_expired} expired.`
      );
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const resetFilters = () => {
    setKeyword('');
    setCity('');
    setWorkplace('any');
    setEmploymentType('');
    setEligibility('');
    setTimeout(() => fetchJobs(), 0);
  };

  const hasActiveFilters = keyword || city || workplace !== 'any' || employmentType || eligibility;

  const formatSalary = (job: JobSummary) => {
    if (!job.salary_min && !job.salary_max) return null;
    const currency = job.salary_currency || 'PKR';
    if (job.salary_min && job.salary_max) {
      return `${currency} ${job.salary_min.toLocaleString()} – ${job.salary_max.toLocaleString()}`;
    }
    if (job.salary_min) return `${currency} ${job.salary_min.toLocaleString()}+`;
    if (job.salary_max) return `Up to ${currency} ${job.salary_max.toLocaleString()}`;
    return null;
  };

  const getEligibilityBadge = (job: JobSummary) => {
    if (job.eligibility === 'eligible') return <Badge variant="success" dot>Pakistan Eligible</Badge>;
    if (job.eligibility === 'ineligible') return <Badge variant="error" dot>Not Eligible</Badge>;
    return <Badge variant="neutral" dot>Eligibility Unknown</Badge>;
  };

  const getWorkplaceBadge = (job: JobSummary) => {
    if (job.is_remote) return <Badge variant="primary" dot><Globe size={12} /> Remote</Badge>;
    if (job.workplace_type === 'hybrid') return <Badge variant="info" dot>Hybrid</Badge>;
    return <Badge variant="neutral" dot>On-site</Badge>;
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Jobs"
        subtitle={`${total} job${total === 1 ? '' : 's'} found across ${sources.length} source${sources.length === 1 ? '' : 's'}`}
        action={
          <Button onClick={runDiscovery} size="sm" leftIcon={<Search size={16} />}>
            Run Discovery
          </Button>
        }
      />

      <Card variant="hover" className="mb-6">
        <div className="p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Input
              label="Keyword"
              placeholder="e.g. Python, React, Marketing"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              leftIcon={<Search size={18} />}
            />
            <Input
              label="City"
              placeholder="e.g. Lahore, Karachi, Remote"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              leftIcon={<MapPin size={18} />}
            />
            <div>
              <label className="label">Workplace</label>
              <select
                value={workplace}
                onChange={(e) => setWorkplace(e.target.value as 'any' | 'remote' | 'hybrid' | 'onsite')}
                className="input"
              >
                <option value="any">Any workplace</option>
                <option value="remote">Remote only</option>
                <option value="hybrid">Hybrid only</option>
                <option value="onsite">On-site only</option>
              </select>
            </div>
            <div>
              <label className="label">Employment Type</label>
              <select
                value={employmentType}
                onChange={(e) => setEmploymentType(e.target.value)}
                className="input"
              >
                <option value="">Any type</option>
                <option value="full_time">Full-time</option>
                <option value="part_time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
                <option value="temporary">Temporary</option>
              </select>
            </div>
            <div>
              <label className="label">Pakistan Eligibility</label>
              <select
                value={eligibility}
                onChange={(e) => setEligibility(e.target.value)}
                className="input"
              >
                <option value="">Any</option>
                <option value="eligible">Eligible</option>
                <option value="ineligible">Not Eligible</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button onClick={() => fetchJobs()} leftIcon={<Filter size={16} />}>
              Search
            </Button>
            {hasActiveFilters && (
              <Button variant="ghost" onClick={resetFilters} leftIcon={<X size={16} />}>
                Clear filters
              </Button>
            )}
            <Button variant="outline" onClick={runDiscovery} leftIcon={<Search size={16} />}>
              Run Discovery
            </Button>
          </div>
        </div>
      </Card>

      {error && <ErrorState message={error} onRetry={() => fetchJobs()} className="mb-6" />}

      {loading && jobs.length === 0 && (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <EmptyState
          title="No jobs found"
          description="Try adjusting your filters or run discovery to find more opportunities."
          icon={<Briefcase size={48} />}
          action={
            <Button onClick={() => fetchJobs()} variant="secondary" leftIcon={<RefreshCw size={16} />}>
              Refresh
            </Button>
          }
        />
      )}

      <div className="space-y-4" role="list" aria-label="Job listings">
        {jobs.map((job) => (
          <Card key={job.id} variant="hover" className="group" role="listitem">
            <div className="p-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <h3 className="text-h3 text-text-primary truncate hover:text-brand-400 transition-colors cursor-pointer"
                        onClick={() => navigate(`/jobs/${job.id}`)}>
                      {job.title}
                    </h3>
                    {job.eligibility === 'ineligible' && (
                      <Badge variant="error" dot>Not Eligible</Badge>
                    )}
                  </div>
                  <p className="text-body text-text-secondary mt-1 flex items-center gap-2">
                    <Building2 size={16} className="text-text-muted" />
                    {job.company_name}
                  </p>
                  <div className="flex flex-wrap items-center gap-3 mt-2 text-metadata text-text-muted">
                    {job.city || job.province || job.country ? (
                      <>
                        <MapPin size={14} />
                        <span>{[job.city, job.province, job.country].filter(Boolean).join(', ')}</span>
                      </>
                    ) : null}
                    {job.is_remote && <span className="flex items-center gap-1"><Globe size={14} /> Remote</span>}
                    {job.workplace_type && !job.is_remote && <span>{job.workplace_type.replace('_', ' ')}</span>}
                    {job.employment_type && <span>{job.employment_type.replace('_', ' ')}</span>}
                    {formatSalary(job) && <span className="flex items-center gap-1"><DollarSign size={14} /> {formatSalary(job)}</span>}
                  </div>
                  <p className="text-caption mt-2 text-text-muted">Source: {job.source}</p>
                </div>
                <div className="flex flex-col items-end gap-3 shrink-0">
                  {job.source_url && (
                    <a
                      href={job.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-body-sm text-brand-400 hover:text-brand-300 flex items-center gap-1"
                    >
                      View original
                      <Briefcase size={14} />
                    </a>
                  )}
                  <Button
                    onClick={() => toggleSave(job.id)}
                    variant={savedIds.has(job.id) ? 'primary' : 'secondary'}
                    size="sm"
                    leftIcon={savedIds.has(job.id) ? null : undefined}
                  >
                    {savedIds.has(job.id) ? 'Saved' : 'Save'}
                  </Button>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-surface-border flex flex-wrap items-center gap-3">
                {getWorkplaceBadge(job)}
                {getEligibilityBadge(job)}
                {job.eligibility_reason && (
                  <span className="text-caption text-text-muted flex-1 text-right sm:text-left">
                    {job.eligibility_reason}
                  </span>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {hasMore && (
        <div className="mt-6 text-center">
          <Button variant="secondary" onClick={() => fetchJobs(page + 1)} disabled={loading}>
            {loading ? 'Loading...' : 'Load more jobs'}
          </Button>
        </div>
      )}
    </div>
  );
}

export default JobsPage;