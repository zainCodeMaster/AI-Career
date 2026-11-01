/**
 * CareerOS API client — Phase 7 CRM.
 */

export type ApplicationStatus =
  | 'saved'
  | 'ready_to_apply'
  | 'applied'
  | 'application_viewed'
  | 'screening'
  | 'interview'
  | 'technical_interview'
  | 'final_interview'
  | 'offer'
  | 'accepted'
  | 'rejected'
  | 'withdrawn'
  | 'expired'
  | 'on_hold';

export type ApplicationPriority = 'low' | 'medium' | 'high' | 'urgent';
export type ApplicationSource = 'manual' | 'ai' | 'automation' | 'system';
export type ActorType = 'manual' | 'ai' | 'automation' | 'system';
export type ActivityEventType =
  | 'application_created'
  | 'job_saved'
  | 'application_submitted'
  | 'status_changed'
  | 'resume_attached'
  | 'cover_letter_attached'
  | 'contact_added'
  | 'email_logged'
  | 'email_sent'
  | 'interview_scheduled'
  | 'interview_completed'
  | 'follow_up_created'
  | 'follow_up_completed'
  | 'offer_received'
  | 'rejected'
  | 'withdrawn'
  | 'ai_recommendation_generated'
  | 'automation_executed';
export type ContactRole = 'recruiter' | 'hiring_manager' | 'interviewer' | 'referral' | 'other';
export type InterviewType = 'hr_screen' | 'technical' | 'coding' | 'system_design' | 'behavioral' | 'final' | 'other';
export type InterviewStatus = 'scheduled' | 'completed' | 'cancelled' | 'no_show' | 'rescheduled';
export type InterviewOutcome = 'passed' | 'failed' | 'pending' | 'unknown';
export type FollowUpType = 'recruiter_follow_up' | 'status_check' | 'interview_prep' | 'thank_you_note' | 'deadline' | 'custom';
export type FollowUpStatus = 'pending' | 'done' | 'snoozed' | 'cancelled';
export type OfferStatus = 'received' | 'accepted' | 'declined' | 'expired' | 'negotiating';

export interface ApplicationSummary {
  id: string;
  user_id: string;
  name: string | null;
  job_id: string | null;
  company_id: string | null;
  status: ApplicationStatus;
  priority: ApplicationPriority;
  source: ApplicationSource;
  notes: string | null;
  job_title_snapshot: string | null;
  applied_at: string | null;
  deadline_at: string | null;
  last_activity_at: string | null;
  next_action_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationResponse extends ApplicationSummary {
  job?: {
    id: string;
    title: string;
    company_name: string;
  };
  company?: {
    id: string;
    name: string;
    normalized_name: string;
    domain?: string | null;
    industry?: string | null;
    location?: string | null;
  };
  resume_version?: {
    id: string;
    name: string;
    version_number: number;
  };
  primary_contact?: ContactResponse;
  activities: ApplicationActivityResponse[];
  documents: ApplicationDocumentResponse[];
  interviews: InterviewResponse[];
  follow_ups: FollowUpResponse[];
  offer?: OfferResponse;
  rejection?: RejectionResponse;
  recommendations: RecommendationResponse[];
}

export interface ApplicationListResponse {
  items: ApplicationSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApplicationCreate {
  name?: string | null;
  priority?: ApplicationPriority;
  source?: ApplicationSource;
  notes?: string | null;
  application_url?: string | null;
  external_application_id?: string | null;
  job_id?: string | null;
  company_id?: string | null;
  job_title_snapshot?: string | null;
  resume_version_id?: string | null;
  cover_letter_document_id?: string | null;
  primary_contact_id?: string | null;
  deadline_at?: string | null;
}

export interface ApplicationUpdate {
  status?: ApplicationStatus;
  previous_status?: string | null;
  priority?: ApplicationPriority;
  source?: ApplicationSource;
  notes?: string | null;
  application_url?: string | null;
  external_application_id?: string | null;
  resume_version_id?: string | null;
  cover_letter_document_id?: string | null;
  primary_contact_id?: string | null;
  deadline_at?: string | null;
}

export interface ApplicationTransitionRequest {
  to_status: ApplicationStatus;
  reason?: string | null;
  metadata?: Record<string, any>;
}

export interface ApplicationTransitionResponse {
  application_id: string;
  from_status: string;
  to_status: string;
  transitioned_at: string;
  message?: string | null;
}

export interface StateTransitionResponse {
  from_status: ApplicationStatus;
  to_status: ApplicationStatus;
  allowed: boolean;
  requires_reason?: boolean;
  message?: string | null;
}

export interface StateMachineInfoResponse {
  current_status: ApplicationStatus;
  allowed_transitions: StateTransitionResponse[];
  is_terminal: boolean;
  can_reopen?: boolean;
}

export interface CompanyResponse {
  id: string;
  name: string;
  normalized_name: string;
  canonical_name?: string | null;
  domain?: string | null;
  website?: string | null;
  industry?: string | null;
  location?: string | null;
  size?: string | null;
  description?: string | null;
  logo_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactResponse {
  id: string;
  user_id: string;
  company_id?: string | null;
  name: string;
  title?: string | null;
  email?: string | null;
  linkedin_url?: string | null;
  phone?: string | null;
  notes?: string | null;
  relationship_status?: string | null;
  last_contacted_at?: string | null;
  next_follow_up_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationContactResponse {
  id: string;
  application_id: string;
  contact: ContactResponse;
  role: ContactRole;
  created_at: string;
}

export interface InterviewResponse {
  id: string;
  application_id: string;
  user_id: string;
  interview_type: InterviewType;
  scheduled_at: string;
  duration_minutes?: number | null;
  timezone?: string | null;
  location_or_meeting_url?: string | null;
  interviewer_contact_ids?: string[] | null;
  status: InterviewStatus;
  notes?: string | null;
  preparation_notes?: string | null;
  outcome: InterviewOutcome;
  feedback?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FollowUpResponse {
  id: string;
  application_id?: string | null;
  contact_id?: string | null;
  follow_up_type: FollowUpType;
  title: string;
  notes?: string | null;
  due_at: string;
  priority: string;
  status: FollowUpStatus;
  reminder_at?: string | null;
  completed_at?: string | null;
  created_by: ActorType;
  created_at: string;
  updated_at: string;
}

export interface OfferResponse {
  id: string;
  application_id: string;
  user_id: string;
  base_salary?: number | null;
  currency?: string | null;
  bonus?: number | null;
  equity_notes?: string | null;
  employment_type?: string | null;
  location?: string | null;
  work_mode?: string | null;
  start_date?: string | null;
  expires_at?: string | null;
  benefits_notes?: string | null;
  status: OfferStatus;
  document_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RejectionResponse {
  id: string;
  application_id: string;
  user_id: string;
  stage?: string | null;
  reason?: string | null;
  details?: string | null;
  rejected_at: string;
  is_employer_initiated: boolean;
  created_at: string;
}

export interface RecommendationResponse {
  id: string;
  application_id?: string | null;
  recommendation_type: string;
  severity: string;
  title: string;
  explanation?: string | null;
  evidence?: string[] | null;
  suggested_action?: string | null;
  confidence?: number | null;
  generated_at: string;
  model?: string | null;
  provider?: string | null;
  prompt_version?: string | null;
  dismissed: boolean;
  dismissed_at?: string | null;
  expires_at?: string | null;
  created_at: string;
}

export interface ApplicationActivityResponse {
  id: string;
  application_id: string;
  event_type: ActivityEventType;
  occurred_at: string;
  actor_type: ActorType;
  actor_id?: string | null;
  related_entity_type?: string | null;
  related_entity_id?: string | null;
  title: string;
  description?: string | null;
  event_metadata?: Record<string, any> | null;
}

export interface ApplicationDocumentResponse {
  id: string;
  application_id: string;
  user_id: string;
  document_type: string;
  file_url?: string | null;
  file_name?: string | null;
  file_size?: number | null;
  mime_type?: string | null;
  document_metadata?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationStatsResponse {
  total: number;
  active: number;
  saved: number;
  ready_to_apply: number;
  applied: number;
  screening: number;
  interview: number;
  technical_interview: number;
  final_interview: number;
  offer: number;
  accepted: number;
  rejected: number;
  withdrawn: number;
  expired: number;
  on_hold: number;
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
  upcoming_interviews: number;
  pending_follow_ups: number;
  stale_applications: number;
}

export interface PipelineStageResponse {
  status: ApplicationStatus;
  label: string;
  count: number;
  applications: ApplicationSummary[];
}

export interface PipelineResponse {
  stages: PipelineStageResponse[];
  total: number;
}

export interface FunnelStageResponse {
  stage: ApplicationStatus;
  count: number;
  conversion_rate: number;
}

export interface FunnelResponse {
  stages: FunnelStageResponse[];
  total_applications: number;
  total_offers: number;
  total_rejections: number;
  average_days_to_offer?: number | null;
}

export interface ActivityFeedResponse {
  items: ApplicationActivityResponse[];
  total: number;
  page: number;
  page_size: number;
}

import { apiClient } from './client';

export const CrmApi = {
  // Applications
  listApplications(params: Record<string, any> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return apiClient.get<ApplicationListResponse>(`/applications?${qs.toString()}`);
  },
  getApplication(id: string) {
    return apiClient.get<ApplicationResponse>(`/applications/${id}`);
  },
  createApplication(data: ApplicationCreate) {
    return apiClient.post<ApplicationResponse, ApplicationCreate>(`/applications`, data);
  },
  updateApplication(id: string, data: ApplicationUpdate) {
    return apiClient.patch<ApplicationResponse, ApplicationUpdate>(`/applications/${id}`, data);
  },
  deleteApplication(id: string) {
    return apiClient.delete<void>(`/applications/${id}`);
  },
  transitionApplication(id: string, data: ApplicationTransitionRequest) {
    return apiClient.post<ApplicationTransitionResponse, ApplicationTransitionRequest>(`/applications/${id}/transitions`, data);
  },
  getApplicationTimeline(id: string, params: Record<string, any> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return apiClient.get<ActivityFeedResponse>(`/applications/${id}/timeline?${qs.toString()}`);
  },
  getApplicationOffer(id: string) {
    return apiClient.get<OfferResponse | null>(`/applications/${id}/offer`);
  },
  upsertApplicationOffer(id: string, data: Record<string, any>) {
    return apiClient.put<OfferResponse, Record<string, any>>(`/applications/${id}/offer`, data);
  },
  createApplicationDocument(id: string, data: { document_type: string; file_url?: string | null; file_name?: string | null; file_size?: number | null; mime_type?: string | null; document_metadata?: Record<string, unknown> | null }) {
    return apiClient.post<ApplicationDocumentResponse, { document_type: string; file_url?: string | null; file_name?: string | null; file_size?: number | null; mime_type?: string | null; document_metadata?: Record<string, unknown> | null }>(`/applications/${id}/documents`, data);
  },
  deleteApplicationDocument(id: string) {
    return apiClient.delete<void>(`/applications/documents/${id}`);
  },
  getStateMachineInfo(status?: string) {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return apiClient.get<StateMachineInfoResponse>(`/applications/state-machine${qs}`);
  },

  // Dashboard / Pipeline / Analytics
  getDashboardStats() {
    return apiClient.get<ApplicationStatsResponse>(`/crm/dashboard`);
  },
  getPipeline() {
    return apiClient.get<PipelineResponse>(`/crm/pipeline`);
  },
  getAnalytics() {
    return apiClient.get<FunnelResponse>(`/crm/analytics`);
  },

  // Companies
  listCompanies() {
    return apiClient.get<CompanyResponse[]>(`/companies`);
  },
  createCompany(data: { name: string; website?: string | null; industry?: string | null; location?: string | null; size?: string | null; description?: string | null; logo_url?: string | null }) {
    return apiClient.post<CompanyResponse, { name: string; website?: string | null; industry?: string | null; location?: string | null; size?: string | null; description?: string | null; logo_url?: string | null }>(`/companies`, data);
  },
  updateCompany(id: string, data: Record<string, unknown>) {
    return apiClient.patch<CompanyResponse, Record<string, unknown>>(`/companies/${id}`, data);
  },
  deleteCompany(id: string) {
    return apiClient.delete<void>(`/companies/${id}`);
  },

  // Contacts
  listContacts() {
    return apiClient.get<ContactResponse[]>(`/contacts`);
  },
  createContact(data: { name: string; title?: string | null; email?: string | null; linkedin_url?: string | null; phone?: string | null; notes?: string | null; relationship_status?: string | null; company_id?: string | null }) {
    return apiClient.post<ContactResponse, { name: string; title?: string | null; email?: string | null; linkedin_url?: string | null; phone?: string | null; notes?: string | null; relationship_status?: string | null; company_id?: string | null }>(`/contacts`, data);
  },
  updateContact(id: string, data: Record<string, unknown>) {
    return apiClient.patch<ContactResponse, Record<string, unknown>>(`/contacts/${id}`, data);
  },
  deleteContact(id: string) {
    return apiClient.delete<void>(`/contacts/${id}`);
  },

  // Interviews
  listInterviews(params: Record<string, any> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return apiClient.get<InterviewResponse[]>(`/interviews?${qs.toString()}`);
  },
  createInterview(data: { application_id: string; interview_type: InterviewType; scheduled_at: string; duration_minutes?: number | null; timezone?: string | null; location_or_meeting_url?: string | null; interviewer_contact_ids?: string[] | null; notes?: string | null; preparation_notes?: string | null; feedback?: string | null }) {
    return apiClient.post<InterviewResponse, { application_id: string; interview_type: InterviewType; scheduled_at: string; duration_minutes?: number | null; timezone?: string | null; location_or_meeting_url?: string | null; interviewer_contact_ids?: string[] | null; notes?: string | null; preparation_notes?: string | null; feedback?: string | null }>(`/interviews`, data);
  },
  updateInterview(id: string, data: Record<string, unknown>) {
    return apiClient.patch<InterviewResponse, Record<string, unknown>>(`/interviews/${id}`, data);
  },
  deleteInterview(id: string) {
    return apiClient.delete<void>(`/interviews/${id}`);
  },

  // Follow-ups
  listFollowUps(params: Record<string, any> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return apiClient.get<FollowUpResponse[]>(`/follow-ups?${qs.toString()}`);
  },
  createFollowUp(data: { application_id?: string | null; contact_id?: string | null; follow_up_type: FollowUpType; title: string; notes?: string | null; due_at: string; priority?: string; reminder_at?: string | null }) {
    return apiClient.post<FollowUpResponse, { application_id?: string | null; contact_id?: string | null; follow_up_type: FollowUpType; title: string; notes?: string | null; due_at: string; priority?: string; reminder_at?: string | null }>(`/follow-ups`, data);
  },
  updateFollowUp(id: string, data: Record<string, unknown>) {
    return apiClient.patch<FollowUpResponse, Record<string, unknown>>(`/follow-ups/${id}`, data);
  },
  deleteFollowUp(id: string) {
    return apiClient.delete<void>(`/follow-ups/${id}`);
  },
  completeFollowUp(id: string) {
    return apiClient.post<FollowUpResponse, {}>(`/follow-ups/${id}/complete`, {});
  },

  // Recommendations
  listRecommendations(applicationId?: string) {
    const qs = applicationId ? `?application_id=${encodeURIComponent(applicationId)}` : "";
    return apiClient.get<RecommendationResponse[]>(`/recommendations${qs}`);
  },
};
