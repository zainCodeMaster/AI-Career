import { useEffect, useState } from "react";
import { JobsApi, type JobSummary, type SourceSummary } from "../api/jobs";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { PageHeader } from "../components/layout/PageHeader";

export function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState("");
  const [city, setCity] = useState("");
  const [remote, setRemote] = useState<boolean | null>(null);
  const [internship, setInternship] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [sources, setSources] = useState<SourceSummary[]>([]);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await JobsApi.list({
        keyword: keyword || undefined,
        city: city || undefined,
        remote: remote === null ? undefined : remote,
        internship: internship || undefined,
        page: 1,
        page_size: 20,
      });
      setJobs(resp.items);
      setTotal(resp.total);
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
      alert(
        `Discovery: ${result.sources_succeeded}/${result.sources_attempted} sources ok; ` +
          `${result.jobs_created} new, ${result.jobs_updated} updated, ${result.jobs_expired} expired.`
      );
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-content">
      <PageHeader
        title="Jobs"
        description={`${total} job${total === 1 ? "" : "s"} across ${sources.length} source${sources.length === 1 ? "" : "s"}`}
        action={
          <Button onClick={runDiscovery} size="sm">
            Run discovery
          </Button>
        }
      />

      <Card className="mb-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <Input
            placeholder="Keyword (e.g. Python)"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
          <Input
            placeholder="City (e.g. Lahore)"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />
          <select
            value={remote === null ? "" : remote ? "remote" : "onsite"}
            onChange={(e) =>
              setRemote(e.target.value === "" ? null : e.target.value === "remote")
            }
            className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="">Any workplace</option>
            <option value="remote">Remote only</option>
            <option value="onsite">On-site only</option>
          </select>
          <label className="flex items-center gap-2 text-body">
            <input
              type="checkbox"
              checked={internship}
              onChange={(e) => setInternship(e.target.checked)}
              className="h-4 w-4 rounded border-neutral-300 text-primary focus:ring-primary"
            />
            Internships only
          </label>
        </div>
        <div className="mt-3 flex gap-2">
          <Button onClick={fetchJobs} variant="secondary" size="sm">
            Search
          </Button>
          <Button
            onClick={() => {
              setKeyword("");
              setCity("");
              setRemote(null);
              setInternship(false);
              setTimeout(fetchJobs, 0);
            }}
            variant="secondary"
            size="sm"
          >
            Reset
          </Button>
        </div>
      </Card>

      {error && <ErrorState message={error} onRetry={fetchJobs} className="mb-4" />}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-neutral-200 border-t-primary" />
        </div>
      )}

      {!loading && jobs.length === 0 && (
        <EmptyState
          title="No jobs found"
          description="Try adjusting your filters or run discovery to find more opportunities."
          action={
            <Button onClick={fetchJobs} variant="secondary" size="sm">
              Refresh
            </Button>
          }
        />
      )}

      <div className="space-y-3">
        {jobs.map((job) => (
          <Card key={job.id} className="hover:border-neutral-300 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <button type="button" onClick={() => (window.location.href = `/jobs/${job.id}`)} className="text-left text-h3 text-neutral-900 truncate hover:text-primary">
                  {job.title}
                </button>
                <p className="text-body text-neutral-700 mt-1">{job.company_name}</p>
                <p className="text-metadata mt-1">
                  {[job.city, job.province, job.country].filter(Boolean).join(", ") || "—"}
                  {job.is_remote ? " · Remote" : ""}
                  {job.employment_type ? ` · ${job.employment_type.replace("_", " ")}` : ""}
                  {job.salary_min || job.salary_max
                    ? ` · ${job.salary_currency || ""} ${job.salary_min ?? ""}${
                        job.salary_min && job.salary_max ? "–" : ""
                      }${job.salary_max ?? ""}`
                    : ""}
                </p>
                <p className="text-caption mt-1">source: {job.source}</p>
              </div>
              <div className="flex flex-col items-end gap-2 shrink-0">
                {job.source_url && (
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-body-sm text-primary hover:underline"
                  >
                    View original ↗
                  </a>
                )}
                <Button
                  onClick={() => toggleSave(job.id)}
                  variant={savedIds.has(job.id) ? "primary" : "secondary"}
                  size="sm"
                >
                  {savedIds.has(job.id) ? "Saved ✓" : "Save"}
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default JobsPage;
