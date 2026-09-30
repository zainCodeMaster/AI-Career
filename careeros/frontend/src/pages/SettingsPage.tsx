import { useEffect, useState } from 'react';
import { JobsApi, type JobPreferences } from '../api/jobs';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { PageHeader } from '../components/layout/PageHeader';

const EMPTY: JobPreferences = {
  target_roles: [], preferred_cities: [], preferred_provinces: [], remote_preference: null,
  employment_types: [], experience_level: null, min_salary: null, salary_currency: null,
  sector_preference: null, selected_industries: [],
};

export function SettingsPage() {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState<JobPreferences>(EMPTY);
  const [roles, setRoles] = useState('');
  const [cities, setCities] = useState('');
  const [remote, setRemote] = useState('');
  const [salary, setSalary] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    JobsApi.getPreferences().then((data) => {
      setPreferences(data);
      setRoles(data.target_roles.join(', '));
      setCities(data.preferred_cities.join(', '));
      setRemote(data.remote_preference || '');
      setSalary(data.min_salary == null ? '' : String(data.min_salary));
    }).catch((caught) => setError(caught instanceof Error ? caught.message : 'Unable to load settings')).finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true); setError(null); setMessage(null);
    try {
      const data = await JobsApi.updatePreferences({
        ...preferences,
        target_roles: roles.split(',').map((item) => item.trim()).filter(Boolean),
        preferred_cities: cities.split(',').map((item) => item.trim()).filter(Boolean),
        remote_preference: remote || null,
        min_salary: salary ? Number(salary) : null,
      });
      setPreferences(data);
      setMessage('Job preferences saved.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to save settings');
    } finally { setSaving(false); }
  };

  if (loading) return <div className="mx-auto max-w-content"><PageHeader title="Settings" /><p className="py-12 text-center text-body text-neutral-600">Loading settings...</p></div>;

  return (
    <div className="mx-auto max-w-content">
      <PageHeader title="Settings" description="Control the preferences used to discover and rank jobs." />
      {error && <ErrorState message={error} className="mb-5" />}
      <Card className="max-w-3xl space-y-6">
        <section>
          <h2 className="text-h3 text-neutral-900">Account</h2>
          <p className="mt-2 text-body text-neutral-700">{user?.full_name || 'CareerOS user'} · {user?.email}</p>
        </section>
        <section className="space-y-4 border-t border-neutral-200 pt-5">
          <h2 className="text-h3 text-neutral-900">Job preferences</h2>
          <Input label="Target roles" value={roles} onChange={(event) => setRoles(event.target.value)} placeholder="Software Engineer, Data Analyst" />
          <Input label="Preferred cities" value={cities} onChange={(event) => setCities(event.target.value)} placeholder="Lahore, Islamabad" />
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Remote preference" value={remote} onChange={(event) => setRemote(event.target.value)} placeholder="remote, hybrid, onsite" />
            <Input label="Minimum salary" type="number" min="0" value={salary} onChange={(event) => setSalary(event.target.value)} />
          </div>
        </section>
        {message && <p className="rounded-md border border-primary-light bg-primary-light p-3 text-body-sm text-primary-dark" role="status">{message}</p>}
        <Button onClick={save} disabled={saving}>{saving ? 'Saving...' : 'Save preferences'}</Button>
      </Card>
    </div>
  );
}
