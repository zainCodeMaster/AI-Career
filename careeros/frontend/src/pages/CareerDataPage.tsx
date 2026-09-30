import { useEffect, useState } from 'react';
import { CareerApi, type CareerRecord, type Certification, type Education, type Skill, type WorkExperience } from '../api/career';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { PageHeader } from '../components/layout/PageHeader';

type FormValue = string | boolean;
type FormData = Record<string, FormValue>;
type FieldSpec = { key: string; label: string; type?: 'text' | 'date' | 'number' | 'url' | 'checkbox'; required?: boolean };

type SectionProps<T extends CareerRecord> = {
  title: string;
  description: string;
  fields: FieldSpec[];
  records: T[];
  onCreate: (data: Record<string, unknown>) => Promise<T>;
  onUpdate: (id: string, data: Record<string, unknown>) => Promise<T>;
  onDelete: (id: string) => Promise<void>;
  summary: (record: T) => string;
};

function toFormData(record: CareerRecord, fields: FieldSpec[]): FormData {
  return Object.fromEntries(fields.map(({ key, type }) => {
    const value = (record as unknown as Record<string, unknown>)[key];
    if (type === 'checkbox') return [key, Boolean(value)];
    return [key, value == null ? '' : String(value)];
  }));
}

function toPayload(data: FormData, fields: FieldSpec[]): Record<string, unknown> {
  return Object.fromEntries(fields.map(({ key, type }) => {
    const value = data[key];
    if (type === 'checkbox') return [key, Boolean(value)];
    if (type === 'number') return [key, value === '' ? null : Number(value)];
    return [key, value === '' ? null : value];
  }));
}

function RecordSection<T extends CareerRecord>({ title, description, fields, records, onCreate, onUpdate, onDelete, summary }: SectionProps<T>) {
  const emptyForm = Object.fromEntries(fields.map(({ key, type }) => [key, type === 'checkbox' ? false : ''])) as FormData;
  const [form, setForm] = useState<FormData>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = toPayload(form, fields);
      if (editingId) await onUpdate(editingId, payload);
      else await onCreate(payload);
      setForm(emptyForm);
      setEditingId(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : `Unable to save ${title.toLowerCase()}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-h3 text-neutral-900">{title}</h2>
        <p className="mt-1 text-body-sm text-neutral-600">{description}</p>
      </div>
      <div className="space-y-2">
        {records.length === 0 && <p className="rounded-md bg-neutral-50 p-3 text-body-sm text-neutral-600">No records added yet.</p>}
        {records.map((record) => (
          <div key={record.id} className="flex flex-col gap-2 rounded-md border border-neutral-200 p-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-body text-neutral-800">{summary(record)}</p>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => { setEditingId(record.id); setForm(toFormData(record, fields)); }}>Edit</Button>
              <Button size="sm" variant="secondary" onClick={() => void onDelete(record.id)}>Delete</Button>
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="grid gap-3 border-t border-neutral-200 pt-4 sm:grid-cols-2">
        {fields.map((field) => field.type === 'checkbox' ? (
          <label key={field.key} className="flex items-center gap-2 text-body sm:col-span-2">
            <input type="checkbox" checked={Boolean(form[field.key])} onChange={(event) => setForm({ ...form, [field.key]: event.target.checked })} />
            {field.label}
          </label>
        ) : (
          <Input key={field.key} label={field.label} type={field.type || 'text'} required={field.required} value={String(form[field.key] || '')} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })} />
        ))}
        {error && <p className="text-body-sm text-error sm:col-span-2" role="alert">{error}</p>}
        <div className="flex gap-2 sm:col-span-2">
          <Button type="submit" disabled={saving}>{saving ? 'Saving...' : editingId ? 'Save changes' : `Add ${title.toLowerCase().replace(/s$/, '')}`}</Button>
          {editingId && <Button type="button" variant="secondary" onClick={() => { setEditingId(null); setForm(emptyForm); }}>Cancel</Button>}
        </div>
      </form>
    </Card>
  );
}

const skillFields: FieldSpec[] = [
  { key: 'name', label: 'Skill name', required: true },
  { key: 'category', label: 'Category' },
  { key: 'proficiency', label: 'Proficiency' },
  { key: 'years_of_experience', label: 'Years of experience', type: 'number' },
];
const educationFields: FieldSpec[] = [
  { key: 'institution', label: 'Institution', required: true },
  { key: 'degree', label: 'Degree' },
  { key: 'field_of_study', label: 'Field of study' },
  { key: 'start_date', label: 'Start date', type: 'date' },
  { key: 'end_date', label: 'End date', type: 'date' },
  { key: 'grade', label: 'Grade' },
];
const experienceFields: FieldSpec[] = [
  { key: 'company', label: 'Company', required: true },
  { key: 'job_title', label: 'Job title', required: true },
  { key: 'location', label: 'Location' },
  { key: 'start_date', label: 'Start date', type: 'date', required: true },
  { key: 'end_date', label: 'End date', type: 'date' },
  { key: 'is_current', label: 'This is my current role', type: 'checkbox' },
];
const certificationFields: FieldSpec[] = [
  { key: 'name', label: 'Certification name', required: true },
  { key: 'issuing_organization', label: 'Issuing organization' },
  { key: 'issue_date', label: 'Issue date', type: 'date' },
  { key: 'expiry_date', label: 'Expiry date', type: 'date' },
  { key: 'credential_id', label: 'Credential ID' },
  { key: 'credential_url', label: 'Credential URL', type: 'url' },
];

export function CareerDataPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [education, setEducation] = useState<Education[]>([]);
  const [experience, setExperience] = useState<WorkExperience[]>([]);
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    setLoading(true); setError(null);
    try {
      const [nextSkills, nextEducation, nextExperience, nextCertifications] = await Promise.all([
        CareerApi.listSkills(), CareerApi.listEducation(), CareerApi.listExperience(), CareerApi.listCertifications(),
      ]);
      setSkills(nextSkills); setEducation(nextEducation); setExperience(nextExperience); setCertifications(nextCertifications);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load career data');
    } finally { setLoading(false); }
  };

  useEffect(() => { void reload(); }, []);

  if (loading) return <div className="mx-auto max-w-content"><PageHeader title="Career Data" /><p className="py-12 text-center text-body text-neutral-600">Loading career data...</p></div>;
  if (error) return <div className="mx-auto max-w-content"><PageHeader title="Career Data" /><ErrorState message={error} onRetry={() => void reload()} /></div>;

  const refresh = async <T extends CareerRecord>(setter: (records: T[]) => void, list: () => Promise<T[]>) => setter(await list());
  const mutate = async <T extends CareerRecord, R>(setter: (records: T[]) => void, list: () => Promise<T[]>, action: () => Promise<R>): Promise<R> => {
    const result = await action();
    await refresh(setter, list);
    return result;
  };

  return (
    <div className="mx-auto max-w-content space-y-5">
      <PageHeader title="Career Data" description="Keep the experience, skills, education, and certifications used by resumes and matching up to date." />
      <RecordSection title="Skills" description="Skills used in your profile and job matching." fields={skillFields} records={skills} summary={(item) => `${item.name}${item.proficiency ? ` · ${item.proficiency}` : ''}`} onCreate={(data) => mutate(setSkills, CareerApi.listSkills, () => CareerApi.createSkill(data as Omit<Skill, keyof CareerRecord>)) as Promise<Skill>} onUpdate={(id, data) => mutate(setSkills, CareerApi.listSkills, () => CareerApi.updateSkill(id, data as Partial<Omit<Skill, keyof CareerRecord>>)) as Promise<Skill>} onDelete={(id) => mutate(setSkills, CareerApi.listSkills, () => CareerApi.deleteSkill(id)) as Promise<void>} />
      <RecordSection title="Education" description="Education history available to your resumes." fields={educationFields} records={education} summary={(item) => `${item.degree || 'Education'} · ${item.institution}`} onCreate={(data) => mutate(setEducation, CareerApi.listEducation, () => CareerApi.createEducation(data as Omit<Education, keyof CareerRecord>)) as Promise<Education>} onUpdate={(id, data) => mutate(setEducation, CareerApi.listEducation, () => CareerApi.updateEducation(id, data as Partial<Omit<Education, keyof CareerRecord>>)) as Promise<Education>} onDelete={(id) => mutate(setEducation, CareerApi.listEducation, () => CareerApi.deleteEducation(id)) as Promise<void>} />
      <RecordSection title="Experience" description="Work history used for matching and resume content." fields={experienceFields} records={experience} summary={(item) => `${item.job_title} · ${item.company}`} onCreate={(data) => mutate(setExperience, CareerApi.listExperience, () => CareerApi.createExperience(data as Omit<WorkExperience, keyof CareerRecord>)) as Promise<WorkExperience>} onUpdate={(id, data) => mutate(setExperience, CareerApi.listExperience, () => CareerApi.updateExperience(id, data as Partial<Omit<WorkExperience, keyof CareerRecord>>)) as Promise<WorkExperience>} onDelete={(id) => mutate(setExperience, CareerApi.listExperience, () => CareerApi.deleteExperience(id)) as Promise<void>} />
      <RecordSection title="Certifications" description="Credentials and verification links you want to keep on record." fields={certificationFields} records={certifications} summary={(item) => `${item.name}${item.issuing_organization ? ` · ${item.issuing_organization}` : ''}`} onCreate={(data) => mutate(setCertifications, CareerApi.listCertifications, () => CareerApi.createCertification(data as Omit<Certification, keyof CareerRecord>)) as Promise<Certification>} onUpdate={(id, data) => mutate(setCertifications, CareerApi.listCertifications, () => CareerApi.updateCertification(id, data as Partial<Omit<Certification, keyof CareerRecord>>)) as Promise<Certification>} onDelete={(id) => mutate(setCertifications, CareerApi.listCertifications, () => CareerApi.deleteCertification(id)) as Promise<void>} />
    </div>
  );
}
