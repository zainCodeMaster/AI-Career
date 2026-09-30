import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ResumesApi, type ResumeSummary } from "../api/resumes";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { PageHeader } from "../components/layout/PageHeader";

export function ResumesPage() {
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [building, setBuilding] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [name, setName] = useState("");
  const navigate = useNavigate();

  const fetchResumes = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await ResumesApi.list({ page_size: 50 });
      setResumes(resp.items);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const createResume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const resume = await ResumesApi.create({ name: name.trim() });
      navigate(`/resumes/${resume.id}`);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const buildFromProfile = async () => {
    setBuilding(true);
    setError(null);
    setMessage(null);
    try {
      const resume = await ResumesApi.buildFromProfile('Profile Resume');
      setMessage('Resume built from your saved career profile.');
      navigate(`/resumes/${resume.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBuilding(false);
    }
  };

  const deleteResume = async (id: string) => {
    if (!confirm("Delete this resume? This action cannot be undone.")) return;
    try {
      await ResumesApi.delete(id);
      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-content">
      <PageHeader
        title="Resumes"
        description={`${resumes.length} resume${resumes.length === 1 ? "" : "s"}`}
        action={
          <div className="flex flex-wrap gap-2">
            <form onSubmit={createResume} className="flex gap-2">
              <Input placeholder="New resume name" value={name} onChange={(e) => setName(e.target.value)} className="w-48" />
              <Button type="submit" size="sm">Create</Button>
            </form>
            <Button type="button" variant="secondary" size="sm" onClick={() => void buildFromProfile()} disabled={building}>{building ? "Building…" : "Build from profile"}</Button>
          </div>
        }
      />

      {error && <ErrorState message={error} onRetry={fetchResumes} className="mb-4" />}
      {message && <p className="mb-4 rounded-md border border-primary-light bg-primary-light p-3 text-body-sm text-primary-dark" role="status">{message}</p>}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-neutral-200 border-t-primary" />
        </div>
      )}

      {!loading && resumes.length === 0 && (
        <EmptyState
          title="No resumes yet"
          description="Create your first resume to get started with tailored applications."
          action={
            <form onSubmit={createResume} className="flex gap-2">
              <Input
                placeholder="New resume name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-48"
              />
              <Button type="submit" size="sm">Create</Button>
            </form>
          }
        />
      )}

      <div className="space-y-3">
        {resumes.map((resume) => (
          <Card key={resume.id}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-h3 text-neutral-900">{resume.name}</h3>
                <p className="text-metadata mt-1">
                  {resume.resume_type} · {resume.status} · v{resume.version_number}
                </p>
                <p className="text-caption mt-1">
                  Updated {new Date(resume.updated_at).toLocaleString()}
                </p>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button onClick={() => navigate(`/resumes/${resume.id}`)} variant="secondary" size="sm">
                  Open
                </Button>
                <Button onClick={() => deleteResume(resume.id)} variant="destructive" size="sm">
                  Delete
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default ResumesPage;
