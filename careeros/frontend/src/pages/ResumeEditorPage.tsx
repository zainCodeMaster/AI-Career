import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ResumesApi, type ResumeDetail, type ResumeSection, type ATSAnalysisResponse, type TailorResponse, type ResumeSummary } from "../api/resumes";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { PageHeader } from "../components/layout/PageHeader";

type Tab = "editor" | "ats" | "tailor" | "versions";

const TABS: { key: Tab; label: string }[] = [
  { key: "editor", label: "Editor" },
  { key: "ats", label: "ATS Analysis" },
  { key: "tailor", label: "Tailor" },
  { key: "versions", label: "Versions" },
];

export function ResumeEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [resume, setResume] = useState<ResumeDetail | null>(null);
  const [sections, setSections] = useState<ResumeSection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("editor");
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [status, setStatus] = useState("draft");
  const [rawJson, setRawJson] = useState("");

  const [atsJobId, setAtsJobId] = useState("");
  const [atsResult, setAtsResult] = useState<ATSAnalysisResponse | null>(null);
  const [atsLoading, setAtsLoading] = useState(false);

  const [tailorJobId, setTailorJobId] = useState("");
  const [tailorName, setTailorName] = useState("");
  const [tailorResult, setTailorResult] = useState<TailorResponse | null>(null);
  const [tailorLoading, setTailorLoading] = useState(false);

  const [versions, setVersions] = useState<ResumeSummary[]>([]);

  const [sectionType, setSectionType] = useState("summary");
  const [sectionTitle, setSectionTitle] = useState("");
  const [sectionContent, setSectionContent] = useState("");
  const [importText, setImportText] = useState("");
  const [importing, setImporting] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [exporting, setExporting] = useState(false);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [r, s] = await Promise.all([ResumesApi.get(id), ResumesApi.listSections(id)]);
      setResume(r);
      setSections(s);
      setName(r.name);
      setStatus(r.status);
      setRawJson(JSON.stringify(r.structured_data, null, 2));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // load is intentionally scoped to the resume id for this editor.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const saveDetails = async () => {
    if (!id) return;
    setSaving(true);
    try {
      const updated = await ResumesApi.update(id, {
        name,
        status,
        structured_data: JSON.parse(rawJson),
      });
      setResume(updated);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const addSection = async () => {
    if (!id) return;
    try {
      const section = await ResumesApi.createSection(id, {
        section_type: sectionType,
        section_title: sectionTitle || undefined,
        content: sectionContent,
        display_order: sections.length,
      });
      setSections((prev) => [...prev, section]);
      setSectionTitle("");
      setSectionContent("");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const removeSection = async (sectionId: string) => {
    try {
      await ResumesApi.deleteSection(sectionId);
      setSections((prev) => prev.filter((s) => s.id !== sectionId));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const runATS = async () => {
    if (!id || !atsJobId) return;
    setAtsLoading(true);
    setAtsResult(null);
    try {
      const result = await ResumesApi.analyzeATS({ resume_id: id, job_id: atsJobId });
      setAtsResult(result);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAtsLoading(false);
    }
  };

  const runTailor = async () => {
    if (!id || !tailorJobId) return;
    setTailorLoading(true);
    setTailorResult(null);
    try {
      const result = await ResumesApi.tailor({
        base_resume_id: id,
        target_job_id: tailorJobId,
        name: tailorName || `Tailored from ${resume?.name || "Resume"}`,
      });
      setTailorResult(result);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setTailorLoading(false);
    }
  };

  const loadVersions = async () => {
    if (!id) return;
    try {
      const all = await ResumesApi.listVersions(id);
      setVersions(all);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const importResumeText = async () => {
    if (!id || !importText.trim()) return;
    setImporting(true);
    setError(null);
    try {
      const imported = await ResumesApi.importText(id, importText.trim());
      setResume(imported);
      setRawJson(JSON.stringify(imported.structured_data, null, 2));
      setImportText("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setImporting(false);
    }
  };

  const importResumeFile = async () => {
    if (!id || !importFile) return;
    setImporting(true);
    setError(null);
    try {
      const imported = await ResumesApi.importFile(id, importFile);
      setResume(imported);
      setRawJson(JSON.stringify(imported.structured_data, null, 2));
      setImportFile(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setImporting(false);
    }
  };

  const exportResume = async () => {
    if (!id) return;
    setExporting(true);
    setError(null);
    try {
      const blob = await ResumesApi.exportText(id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${resume?.name || "resume"}.txt`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-content">
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-neutral-200 border-t-primary" />
        </div>
      </div>
    );
  }

  if (!resume) {
    return (
      <div className="mx-auto max-w-content">
        <ErrorState title="Resume not found" message={error || "The resume you're looking for doesn't exist."} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-content">
      <PageHeader
        title={resume.name}
        description={`${resume.resume_type} · ${resume.status} · v${resume.version_number}`}
        action={
          <div className="flex gap-2">
            <Button onClick={() => void exportResume()} variant="secondary" size="sm" disabled={exporting}>
              {exporting ? "Exporting..." : "Export TXT"}
            </Button>
            <Button onClick={() => navigate("/resumes")} variant="secondary" size="sm">
              Back
            </Button>
          </div>
        }
      />

      {error && <ErrorState message={error} className="mb-4" />}

      <Card className="mb-6">
        <h2 className="text-h3 text-neutral-900">Import resume file</h2>
        <p className="mt-1 text-body-sm text-neutral-600">Supported formats: TXT, PDF, and DOCX. Files are parsed by the authenticated backend and are limited to 10MB.</p>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div>
            <label htmlFor="resume-file" className="mb-1 block text-label text-neutral-700">Resume file</label>
            <input id="resume-file" type="file" accept=".txt,.pdf,.docx" onChange={(event) => setImportFile(event.target.files?.[0] || null)} className="block w-full text-body-sm" />
          </div>
          <Button type="button" onClick={() => void importResumeFile()} disabled={importing || !importFile}>{importing ? 'Importing...' : 'Import file'}</Button>
        </div>
      </Card>

      <nav className="mb-4 flex gap-1 border-b border-neutral-200">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-body-sm transition-colors ${
              tab === t.key
                ? "border-b-2 border-primary font-semibold text-primary"
                : "text-neutral-500 hover:text-neutral-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "editor" && (
        <div className="space-y-4">
          <Card>
            <h3 className="text-h3 text-neutral-900 mb-3">Details</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Input
                label="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <div>
                <label className="text-label text-neutral-700 mb-1 block">Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="draft">Draft</option>
                  <option value="ready">Ready</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>
            <Button onClick={saveDetails} disabled={saving} size="sm" className="mt-3">
              {saving ? "Saving…" : "Save"}
            </Button>
          </Card>

          <Card>
            <h3 className="text-h3 text-neutral-900 mb-3">Structured Data (JSON)</h3>
            <textarea
              className="h-64 w-full rounded-md border border-neutral-200 bg-white p-3 font-mono text-body-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              value={rawJson}
              onChange={(e) => setRawJson(e.target.value)}
            />
          </Card>

          <Card>
            <h3 className="text-h3 text-neutral-900 mb-3">Import plain text</h3>
            <textarea
              className="h-48 w-full rounded-md border border-neutral-200 bg-white p-3 text-body focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              placeholder="Paste resume text here. The backend parser will extract supported sections."
            />
            <Button onClick={() => void importResumeText()} disabled={importing || !importText.trim()} className="mt-3">
              {importing ? "Importing…" : "Import text"}
            </Button>
          </Card>

          <Card>
            <h3 className="text-h3 text-neutral-900 mb-3">Add Section</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Input
                placeholder="Section type (e.g. summary)"
                value={sectionType}
                onChange={(e) => setSectionType(e.target.value)}
              />
              <Input
                placeholder="Title (optional)"
                value={sectionTitle}
                onChange={(e) => setSectionTitle(e.target.value)}
              />
              <Input
                placeholder="Content"
                value={sectionContent}
                onChange={(e) => setSectionContent(e.target.value)}
              />
            </div>
            <Button onClick={addSection} size="sm" className="mt-3">Add Section</Button>
          </Card>

          <Card>
            <h3 className="text-h3 text-neutral-900 mb-3">Sections</h3>
            {sections.length === 0 ? (
              <p className="text-metadata text-neutral-500">No sections yet.</p>
            ) : (
              <ul className="space-y-2">
                {sections.map((s) => (
                  <li key={s.id} className="flex items-start justify-between gap-3 rounded-md border border-neutral-200 p-3">
                    <div className="flex-1 min-w-0">
                      <span className="text-body font-medium text-neutral-900">{s.section_type}</span>
                      {s.section_title && <span className="text-metadata text-neutral-500 ml-2">— {s.section_title}</span>}
                      <p className="text-body-sm text-neutral-600 mt-1">{s.content}</p>
                    </div>
                    <Button onClick={() => removeSection(s.id)} variant="danger" size="sm">Remove</Button>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}

      {tab === "ats" && (
        <div className="space-y-4">
          <Card>
            <h3 className="text-h3 text-text-primary mb-3">Run ATS Analysis</h3>
            <p className="text-body-sm text-text-muted mb-3">
              Rule-based analysis comparing resume content against job keywords. Results are deterministic estimates, not AI-generated.
            </p>
            <div className="flex gap-2">
              <Input
                placeholder="Job ID"
                value={atsJobId}
                onChange={(e) => setAtsJobId(e.target.value)}
                className="flex-1"
              />
              <Button onClick={runATS} disabled={atsLoading || !atsJobId}>
                {atsLoading ? "Analyzing…" : "Analyze"}
              </Button>
            </div>
          </Card>

          {atsResult && (
            <div className="space-y-4">
              <Card>
                <h3 className="text-h3 text-neutral-900 mb-3">Overall Score: {atsResult.overall_score}/100</h3>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {Object.entries(atsResult.breakdown).map(([key, value]) => (
                    <div key={key} className="rounded-md border border-neutral-200 p-3">
                      <div className="text-caption text-neutral-500">{key.replace(/_/g, " ")}</div>
                      <div className="text-numeric text-xl text-neutral-900 mt-1">{value}</div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card>
                <h3 className="text-h3 text-neutral-900 mb-3">Keywords</h3>
                <div className="mb-2">
                  <span className="text-body-sm font-medium text-success-dark">Matched:</span>{" "}
                  <span className="text-body text-neutral-700">{atsResult.matched_keywords.join(", ") || "—"}</span>
                </div>
                <div>
                  <span className="text-body-sm font-medium text-error-dark">Missing:</span>{" "}
                  <span className="text-body text-neutral-700">{atsResult.missing_keywords.join(", ") || "—"}</span>
                </div>
              </Card>

              <Card>
                <h3 className="text-h3 text-neutral-900 mb-3">Skills</h3>
                <div className="mb-2">
                  <span className="text-body-sm font-medium text-success-dark">Matched:</span>{" "}
                  <span className="text-body text-neutral-700">{atsResult.matched_skills.join(", ") || "—"}</span>
                </div>
                <div>
                  <span className="text-body-sm font-medium text-error-dark">Missing:</span>{" "}
                  <span className="text-body text-neutral-700">{atsResult.missing_skills.join(", ") || "—"}</span>
                </div>
              </Card>

              <Card>
                <h3 className="text-h3 text-neutral-900 mb-3">Recommendations</h3>
                <ul className="list-disc space-y-1 pl-5">
                  {atsResult.recommendations.map((r, i) => (
                    <li key={i} className="text-body text-neutral-700">{r}</li>
                  ))}
                </ul>
              </Card>
            </div>
          )}
        </div>
      )}

      {tab === "tailor" && (
        <div className="space-y-4">
          <Card>
            <h3 className="text-h3 text-text-primary mb-3">Tailor Resume for Job</h3>
            <p className="text-body-sm text-text-muted mb-3">
              Rule-based tailoring that emphasizes relevant keywords and experience. Results are deterministic estimates, not AI-generated unless AI is configured in Settings.
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Input
                placeholder="Target Job ID"
                value={tailorJobId}
                onChange={(e) => setTailorJobId(e.target.value)}
              />
              <Input
                placeholder="Tailored resume name"
                value={tailorName}
                onChange={(e) => setTailorName(e.target.value)}
              />
            </div>
            <Button onClick={runTailor} disabled={tailorLoading || !tailorJobId} className="mt-3">
              {tailorLoading ? "Tailoring…" : "Tailor Resume"}
            </Button>
          </Card>

          {tailorResult && (
            <div className="space-y-4">
              <Card>
                <h3 className="text-h3 text-neutral-900 mb-3">Tailored Resume Created</h3>
                <p className="text-body text-neutral-600">ID: {tailorResult.tailored_resume_id}</p>
                <p className="text-body text-neutral-600">ATS Score: {tailorResult.ats_analysis.overall_score}/100</p>
                <Button onClick={() => navigate(`/resumes/${tailorResult.tailored_resume_id}`)} variant="secondary" size="sm" className="mt-2">
                  Open Tailored Resume
                </Button>
              </Card>

              <Card>
                <h3 className="text-h3 text-neutral-900 mb-3">Changes</h3>
                <ul className="space-y-2">
                  {tailorResult.tailoring_changes.map((change: any, i: number) => (
                    <li key={i} className="rounded-md border border-neutral-200 p-3">
                      <span className="text-body font-medium text-neutral-900">{change.section}</span>
                      <span className="text-metadata text-neutral-500">: {change.change_type}</span>
                      <span className="text-body text-neutral-700"> — {change.description}</span>
                    </li>
                  ))}
                </ul>
              </Card>

              <Card>
                <h3 className="text-h3 text-neutral-900 mb-3">Recommendations</h3>
                <ul className="list-disc space-y-1 pl-5">
                  {tailorResult.recommendations.map((r, i) => (
                    <li key={i} className="text-body text-neutral-700">{r}</li>
                  ))}
                </ul>
              </Card>
            </div>
          )}
        </div>
      )}

      {tab === "versions" && (
        <div className="space-y-4">
          <Card>
            <div className="flex items-center justify-between">
              <h3 className="text-h3 text-neutral-900">Version History</h3>
              <Button onClick={loadVersions} variant="secondary" size="sm">Refresh</Button>
            </div>
          </Card>
          {versions.length === 0 ? (
            <EmptyState
              title="No versions loaded"
              description="Click Refresh to load version history."
            />
          ) : (
            <ul className="space-y-3">
              {versions.map((v) => (
                <li key={v.id}>
                  <Card>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-h3 text-neutral-900">{v.name}</h3>
                        <p className="text-metadata mt-1">
                          {v.resume_type} · {v.status} · v{v.version_number}
                        </p>
                        <p className="text-caption mt-1">
                          Updated {new Date(v.updated_at).toLocaleString()}
                        </p>
                      </div>
                      <Button onClick={() => navigate(`/resumes/${v.id}`)} variant="secondary" size="sm">
                        Open
                      </Button>
                    </div>
                  </Card>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export default ResumeEditorPage;
