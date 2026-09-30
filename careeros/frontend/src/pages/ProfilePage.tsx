import { useEffect, useState, type FormEvent } from 'react';
import { ProfileApi, type CareerProfileCreate, type CareerProfileResponse } from '../api/profile';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { PageHeader } from '../components/layout/PageHeader';

const EMPTY_PROFILE: CareerProfileCreate = {
  professional_title: '',
  summary: '',
  phone: '',
  location: '',
  linkedin_url: '',
  github_url: '',
  portfolio_url: '',
  years_of_experience: null,
  preferred_job_title: '',
  preferred_location: '',
  remote_preference: '',
};

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return 'Unable to load career profile';
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString();
}

export function ProfilePage() {
  const [profile, setProfile] = useState<CareerProfileResponse | null>(null);
  const [formData, setFormData] = useState<CareerProfileCreate>({ ...EMPTY_PROFILE });
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadProfile = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await ProfileApi.getProfile();
      setProfile(data);
      setFormData({
        professional_title: data.professional_title ?? '',
        summary: data.summary ?? '',
        phone: data.phone ?? '',
        location: data.location ?? '',
        linkedin_url: data.linkedin_url ?? '',
        github_url: data.github_url ?? '',
        portfolio_url: data.portfolio_url ?? '',
        years_of_experience: data.years_of_experience ?? null,
        preferred_job_title: data.preferred_job_title ?? '',
        preferred_location: data.preferred_location ?? '',
        remote_preference: data.remote_preference ?? '',
      });
    } catch (caught) {
      setProfile(null);
      setFormData({ ...EMPTY_PROFILE });
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadProfile();
  }, []);

  const handleChange = (field: keyof CareerProfileCreate, value: string | number | null) => {
    setFormData((current) => ({ ...current, [field]: value }));
    setError(null);
    setSuccessMessage(null);
  };

  const resetForm = () => {
    if (profile) {
      setFormData({
        professional_title: profile.professional_title ?? '',
        summary: profile.summary ?? '',
        phone: profile.phone ?? '',
        location: profile.location ?? '',
        linkedin_url: profile.linkedin_url ?? '',
        github_url: profile.github_url ?? '',
        portfolio_url: profile.portfolio_url ?? '',
        years_of_experience: profile.years_of_experience ?? null,
        preferred_job_title: profile.preferred_job_title ?? '',
        preferred_location: profile.preferred_location ?? '',
        remote_preference: profile.remote_preference ?? '',
      });
      setIsEditing(false);
    } else {
      setFormData({ ...EMPTY_PROFILE });
      setIsEditing(false);
    }
    setError(null);
    setSuccessMessage(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setIsSaving(true);

    try {
      const nextProfile = profile
        ? await ProfileApi.updateProfile(formData)
        : await ProfileApi.createProfile(formData);
      setProfile(nextProfile);
      setFormData({
        professional_title: nextProfile.professional_title ?? '',
        summary: nextProfile.summary ?? '',
        phone: nextProfile.phone ?? '',
        location: nextProfile.location ?? '',
        linkedin_url: nextProfile.linkedin_url ?? '',
        github_url: nextProfile.github_url ?? '',
        portfolio_url: nextProfile.portfolio_url ?? '',
        years_of_experience: nextProfile.years_of_experience ?? null,
        preferred_job_title: nextProfile.preferred_job_title ?? '',
        preferred_location: nextProfile.preferred_location ?? '',
        remote_preference: nextProfile.remote_preference ?? '',
      });
      setIsEditing(false);
      setSuccessMessage(
        profile ? 'Profile updated successfully.' : 'Profile created successfully.'
      );
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-content">
        <PageHeader title="Career Profile" />
        <div className="flex h-64 items-center justify-center" role="status" aria-live="polite">
          <div className="flex items-center gap-3 text-body text-neutral-600">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-neutral-200 border-t-primary" />
            Loading profile...
          </div>
        </div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="mx-auto max-w-content">
        <PageHeader title="Career Profile" />
        <ErrorState
          title="Unable to load profile"
          message={error}
          onRetry={() => void loadProfile()}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-content">
      <PageHeader
        title={profile ? 'My Career Profile' : 'Create Career Profile'}
        description="Keep your career details and job preferences ready for resumes and matching."
      />

      <Card className="w-full max-w-5xl p-4 sm:p-6 lg:p-8">
        {successMessage && (
          <div
            className="mb-5 rounded-md border border-primary-light bg-primary-light p-3 text-body-sm text-primary-dark"
            role="status"
          >
            {successMessage}
          </div>
        )}

        {profile && !isEditing ? (
          <>
            <div className="grid gap-6 md:grid-cols-2">
              <section className="space-y-3">
                <div>
                  <h2 className="text-body font-semibold text-neutral-900">Professional summary</h2>
                  <p className="mt-2 whitespace-pre-line text-body text-neutral-700">
                    {profile.professional_title || 'Not provided'}
                  </p>
                  <p className="mt-1 whitespace-pre-line text-body text-neutral-600">
                    {profile.summary || 'No summary added.'}
                  </p>
                </div>

                <div>
                  <h2 className="text-body font-semibold text-neutral-900">Contact</h2>
                  <dl className="mt-2 grid gap-3 text-body">
                    <div>
                      <dt className="text-caption text-neutral-500">Phone</dt>
                      <dd>{profile.phone || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-caption text-neutral-500">Location</dt>
                      <dd>{profile.location || '-'}</dd>
                    </div>
                  </dl>
                </div>
              </section>

              <section className="space-y-3">
                <div>
                  <h2 className="text-body font-semibold text-neutral-900">
                    Experience and preferences
                  </h2>
                  <dl className="mt-2 grid gap-3 text-body">
                    <div>
                      <dt className="text-caption text-neutral-500">Years of experience</dt>
                      <dd>{profile.years_of_experience ?? '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-caption text-neutral-500">Preferred job title</dt>
                      <dd>{profile.preferred_job_title || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-caption text-neutral-500">Preferred location</dt>
                      <dd>{profile.preferred_location || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-caption text-neutral-500">Remote preference</dt>
                      <dd>{profile.remote_preference || '-'}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h2 className="text-body font-semibold text-neutral-900">Links</h2>
                  <ul className="mt-2 grid gap-2 text-body">
                    {[
                      ['LinkedIn', profile.linkedin_url],
                      ['GitHub', profile.github_url],
                      ['Portfolio', profile.portfolio_url],
                    ].map(([label, url]) => (
                      <li key={label}>
                        {url ? (
                          <a
                            href={url}
                            className="text-primary hover:underline"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {label}
                          </a>
                        ) : (
                          <span className="text-neutral-500">{label}: Not provided</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </section>
            </div>

            <div className="mt-6 flex flex-col gap-3 border-t border-neutral-200 pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-caption text-neutral-500">
                Created {formatDate(profile.created_at)}
                {profile.updated_at && <> · Updated {formatDate(profile.updated_at)}</>}
              </p>
              <Button type="button" variant="secondary" onClick={() => setIsEditing(true)}>
                Edit Profile
              </Button>
            </div>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <section className="space-y-4">
              <h2 className="text-h3 text-neutral-900">Professional details</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  id="professional_title"
                  label="Professional title"
                  type="text"
                  value={formData.professional_title ?? ''}
                  onChange={(event) => handleChange('professional_title', event.target.value)}
                  placeholder="e.g., Senior Software Engineer"
                  maxLength={255}
                />
                <Input
                  id="years_of_experience"
                  label="Years of experience"
                  type="number"
                  value={formData.years_of_experience ?? ''}
                  onChange={(event) =>
                    handleChange(
                      'years_of_experience',
                      event.target.value === '' ? null : Number(event.target.value)
                    )
                  }
                  min="0"
                  max="80"
                  placeholder="e.g., 5"
                />
              </div>
              <div>
                <label htmlFor="summary" className="mb-1 block text-label text-neutral-700">
                  Professional summary
                </label>
                <textarea
                  id="summary"
                  value={formData.summary ?? ''}
                  onChange={(event) => handleChange('summary', event.target.value)}
                  placeholder="Brief summary of your background, strengths, and career goals"
                  rows={5}
                  maxLength={5000}
                  className="w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-body placeholder:text-neutral-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-primary hover:border-neutral-300"
                />
              </div>
            </section>

            <section className="space-y-4 border-t border-neutral-200 pt-6">
              <h2 className="text-h3 text-neutral-900">Contact and links</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  id="phone"
                  label="Phone"
                  type="tel"
                  value={formData.phone ?? ''}
                  onChange={(event) => handleChange('phone', event.target.value)}
                  placeholder="e.g., +1-555-123-4567"
                  maxLength={20}
                />
                <Input
                  id="location"
                  label="Location"
                  type="text"
                  value={formData.location ?? ''}
                  onChange={(event) => handleChange('location', event.target.value)}
                  placeholder="e.g., New York, NY"
                  maxLength={255}
                />
                <Input
                  id="linkedin_url"
                  label="LinkedIn URL"
                  type="url"
                  value={formData.linkedin_url ?? ''}
                  onChange={(event) => handleChange('linkedin_url', event.target.value)}
                  placeholder="https://linkedin.com/in/yourname"
                  maxLength={512}
                />
                <Input
                  id="github_url"
                  label="GitHub URL"
                  type="url"
                  value={formData.github_url ?? ''}
                  onChange={(event) => handleChange('github_url', event.target.value)}
                  placeholder="https://github.com/yourname"
                  maxLength={512}
                />
                <Input
                  id="portfolio_url"
                  label="Portfolio URL"
                  type="url"
                  value={formData.portfolio_url ?? ''}
                  onChange={(event) => handleChange('portfolio_url', event.target.value)}
                  placeholder="https://yourportfolio.com"
                  maxLength={512}
                  className="md:col-span-2"
                />
              </div>
            </section>

            <section className="space-y-4 border-t border-neutral-200 pt-6">
              <h2 className="text-h3 text-neutral-900">Job preferences</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  id="preferred_job_title"
                  label="Preferred job title"
                  type="text"
                  value={formData.preferred_job_title ?? ''}
                  onChange={(event) => handleChange('preferred_job_title', event.target.value)}
                  placeholder="e.g., Software Engineer"
                  maxLength={255}
                />
                <Input
                  id="preferred_location"
                  label="Preferred location"
                  type="text"
                  value={formData.preferred_location ?? ''}
                  onChange={(event) => handleChange('preferred_location', event.target.value)}
                  placeholder="e.g., Remote, New York"
                  maxLength={255}
                />
                <Input
                  id="remote_preference"
                  label="Remote preference"
                  type="text"
                  value={formData.remote_preference ?? ''}
                  onChange={(event) => handleChange('remote_preference', event.target.value)}
                  placeholder="e.g., Fully Remote, Hybrid, On-site"
                  maxLength={50}
                  className="md:col-span-2"
                />
              </div>
            </section>

            {error && (
              <p
                className="rounded-md border border-error-light bg-error-light p-3 text-body-sm text-error-dark"
                role="alert"
              >
                {error}
              </p>
            )}

            <div className="flex flex-col-reverse gap-3 border-t border-neutral-200 pt-5 sm:flex-row sm:justify-end">
              <Button type="button" variant="secondary" onClick={resetForm} disabled={isSaving}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={isSaving}>
                {isSaving ? 'Saving...' : profile ? 'Save Changes' : 'Create Profile'}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
