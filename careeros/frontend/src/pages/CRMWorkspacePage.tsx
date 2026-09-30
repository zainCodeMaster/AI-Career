import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CrmApi, type CompanyResponse, type ContactResponse, type FollowUpResponse, type InterviewResponse } from '../api/crm';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { PageHeader } from '../components/layout/PageHeader';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="space-y-3"><h2 className="text-h3 text-neutral-900">{title}</h2>{children}</section>;
}

export function CRMWorkspacePage() {
  const queryClient = useQueryClient();
  const [companyName, setCompanyName] = useState('');
  const [editingCompanyId, setEditingCompanyId] = useState<string | null>(null);
  const [contactName, setContactName] = useState('');
  const [contactCompanyId, setContactCompanyId] = useState('');
  const [editingContactId, setEditingContactId] = useState<string | null>(null);
  const [followUpTitle, setFollowUpTitle] = useState('');
  const [followUpDue, setFollowUpDue] = useState('');
  const [interviewApplicationId, setInterviewApplicationId] = useState('');
  const [interviewType, setInterviewType] = useState('hr_screen');
  const [interviewScheduledAt, setInterviewScheduledAt] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const companies = useQuery({ queryKey: ['crm', 'companies'], queryFn: CrmApi.listCompanies });
  const contacts = useQuery({ queryKey: ['crm', 'contacts'], queryFn: CrmApi.listContacts });
  const interviews = useQuery({ queryKey: ['crm', 'interviews'], queryFn: () => CrmApi.listInterviews() });
  const followUps = useQuery({ queryKey: ['crm', 'follow-ups'], queryFn: () => CrmApi.listFollowUps() });
  const applications = useQuery({ queryKey: ['crm', 'applications', 'interview-picker'], queryFn: () => CrmApi.listApplications({ page_size: 100 }) });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['crm'] });
  const mutation = useMutation({
    mutationFn: async (action: () => Promise<unknown>) => action(),
    onSuccess: () => { setMessage('Saved successfully.'); setError(null); refresh(); },
    onError: (caught: Error) => { setError(caught.message); setMessage(null); },
  });

  const isLoading = companies.isLoading || contacts.isLoading || interviews.isLoading || followUps.isLoading || applications.isLoading;
  const loadError = companies.error || contacts.error || interviews.error || followUps.error || applications.error;
  if (isLoading) return <div className="mx-auto max-w-content"><PageHeader title="CRM Workspace" /><p className="py-12 text-center text-body text-neutral-600">Loading CRM records...</p></div>;
  if (loadError) return <div className="mx-auto max-w-content"><PageHeader title="CRM Workspace" /><ErrorState message={(loadError as Error).message} onRetry={refresh} /></div>;

  const companyItems = companies.data ?? [];
  const contactItems = contacts.data ?? [];
  const interviewItems = interviews.data ?? [];
  const followUpItems = followUps.data ?? [];
  const applicationItems = applications.data?.items ?? [];

  return (
    <div className="mx-auto max-w-content space-y-6">
      <PageHeader title="CRM Workspace" description="Manage companies, contacts, interviews, and follow-ups connected to your applications." />
      {message && <p className="rounded-md border border-primary-light bg-primary-light p-3 text-body-sm text-primary-dark" role="status">{message}</p>}
      {error && <p className="rounded-md border border-error-light bg-error-light p-3 text-body-sm text-error-dark" role="alert">{error}</p>}
      <Card><Section title="Companies"><div className="flex flex-col gap-2 sm:flex-row"><Input aria-label="Company name" value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="Company name" /><Button disabled={!companyName.trim() || mutation.isPending} onClick={() => mutation.mutate(() => editingCompanyId ? CrmApi.updateCompany(editingCompanyId, { name: companyName.trim() }) : CrmApi.createCompany({ name: companyName.trim() }))}>{editingCompanyId ? 'Save company' : 'Add company'}</Button>{editingCompanyId && <Button variant="secondary" onClick={() => { setEditingCompanyId(null); setCompanyName(''); }}>Cancel</Button>}</div><div className="space-y-2">{companyItems.length === 0 ? <EmptyState title="No companies" description="Add companies as you organize your applications." /> : companyItems.map((company: CompanyResponse) => <div key={company.id} className="flex items-center justify-between border-b border-neutral-100 py-2"><span>{company.name}</span><div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => { setEditingCompanyId(company.id); setCompanyName(company.name); }}>Edit</Button><Button size="sm" variant="secondary" onClick={() => mutation.mutate(() => CrmApi.deleteCompany(company.id))}>Delete</Button></div></div>)}</div></Section></Card>
      <Card><Section title="Contacts"><div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]"><Input aria-label="Contact name" value={contactName} onChange={(event) => setContactName(event.target.value)} placeholder="Contact name" /><select aria-label="Contact company" value={contactCompanyId} onChange={(event) => setContactCompanyId(event.target.value)} className="rounded-md border border-neutral-200 bg-white px-3 py-2 text-body"><option value="">No company</option>{companyItems.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}</select><Button disabled={!contactName.trim() || mutation.isPending} onClick={() => mutation.mutate(() => editingContactId ? CrmApi.updateContact(editingContactId, { name: contactName.trim() }) : CrmApi.createContact({ name: contactName.trim(), company_id: contactCompanyId || null }))}>{editingContactId ? 'Save contact' : 'Add contact'}</Button></div><div className="space-y-2">{contactItems.length === 0 ? <EmptyState title="No contacts" description="Add recruiters, hiring managers, or referrals." /> : contactItems.map((contact: ContactResponse) => <div key={contact.id} className="flex items-center justify-between border-b border-neutral-100 py-2"><span>{contact.name}{contact.title ? ` · ${contact.title}` : ''}</span><div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => { setEditingContactId(contact.id); setContactName(contact.name); setContactCompanyId(contact.company_id || ''); }}>Edit</Button><Button size="sm" variant="secondary" onClick={() => mutation.mutate(() => CrmApi.deleteContact(contact.id))}>Delete</Button></div></div>)}</div></Section></Card>
      <Card><Section title="Interviews"><div className="grid gap-2 sm:grid-cols-3"><select aria-label="Interview application" value={interviewApplicationId} onChange={(event) => setInterviewApplicationId(event.target.value)} className="rounded-md border border-neutral-200 bg-white px-3 py-2 text-body"><option value="">Application</option>{applicationItems.map((application) => <option key={application.id} value={application.id}>{application.name || application.job_title_snapshot || application.id}</option>)}</select><select aria-label="Interview type" value={interviewType} onChange={(event) => setInterviewType(event.target.value)} className="rounded-md border border-neutral-200 bg-white px-3 py-2 text-body"><option value="hr_screen">HR screen</option><option value="technical">Technical</option><option value="behavioral">Behavioral</option><option value="final">Final</option><option value="other">Other</option></select><Input aria-label="Interview date and time" type="datetime-local" value={interviewScheduledAt} onChange={(event) => setInterviewScheduledAt(event.target.value)} /></div><Button disabled={!interviewApplicationId || !interviewScheduledAt || mutation.isPending} onClick={() => mutation.mutate(() => CrmApi.createInterview({ application_id: interviewApplicationId, interview_type: interviewType as 'hr_screen', scheduled_at: new Date(interviewScheduledAt).toISOString() }))}>Schedule interview</Button><p className="text-body-sm text-neutral-600">Interviews remain linked to the selected application and are persisted by the CRM API.</p>{interviewItems.length === 0 ? <EmptyState title="No interviews" description="Schedule the next interview from an application." /> : interviewItems.map((interview: InterviewResponse) => <div key={interview.id} className="border-b border-neutral-100 py-2 text-body">{interview.interview_type.replace(/_/g, ' ')} · {new Date(interview.scheduled_at).toLocaleString()} · {interview.status}</div>)}</Section></Card>
      <Card><Section title="Follow-ups"><div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]"><Input aria-label="Follow-up title" value={followUpTitle} onChange={(event) => setFollowUpTitle(event.target.value)} placeholder="Follow-up title" /><Input aria-label="Follow-up due date" type="datetime-local" value={followUpDue} onChange={(event) => setFollowUpDue(event.target.value)} /><Button disabled={!followUpTitle.trim() || !followUpDue || mutation.isPending} onClick={() => mutation.mutate(() => CrmApi.createFollowUp({ title: followUpTitle.trim(), due_at: new Date(followUpDue).toISOString(), follow_up_type: 'custom' }))}>Add follow-up</Button></div><div className="space-y-2">{followUpItems.length === 0 ? <EmptyState title="No follow-ups" description="Track the next action for an application or contact." /> : followUpItems.map((followUp: FollowUpResponse) => <div key={followUp.id} className="flex items-center justify-between border-b border-neutral-100 py-2"><span>{followUp.title} · due {new Date(followUp.due_at).toLocaleDateString()}</span><Button size="sm" variant="secondary" onClick={() => mutation.mutate(() => followUp.status === 'pending' ? CrmApi.completeFollowUp(followUp.id) : CrmApi.deleteFollowUp(followUp.id))}>{followUp.status === 'pending' ? 'Complete' : 'Delete'}</Button></div>)}</div></Section></Card>
    </div>
  );
}
