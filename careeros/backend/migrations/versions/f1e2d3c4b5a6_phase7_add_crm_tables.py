"""Add Phase 7 Career CRM tables.

Revision ID: f1e2d3c4b5a6
Revises: e5f6a7b8c9d0
Create Date: 2026-09-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create companies table
    op.create_table('companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=512), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=512), nullable=True),
        sa.Column('size', sa.String(length=64), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain', name='uq_companies_domain'),
        sa.UniqueConstraint('normalized_name', name='uq_companies_normalized_name'),
    )
    op.create_index('ix_companies_industry', 'companies', ['industry'], unique=False)

    # Create user_company_links table
    op.create_table('user_company_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('relationship_status', sa.String(length=64), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'company_id', name='uq_user_company_link'),
    )
    op.create_index('ix_user_company_links_user_company', 'user_company_links', ['user_id', 'company_id'], unique=False)

    # Create applications table
    op.create_table('applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_match_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_title_snapshot', sa.String(length=512), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='saved'),
        sa.Column('previous_status', sa.String(length=32), nullable=True),
        sa.Column('priority', sa.String(length=32), nullable=False, server_default='medium'),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='manual'),
        sa.Column('resume_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cover_letter_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('primary_contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deadline_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_action_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('application_url', sa.String(length=1024), nullable=True),
        sa.Column('external_application_id', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('match_snapshot', sa.JSON(), nullable=True),
        sa.Column('automation_metadata', sa.JSON(), nullable=True),
        sa.Column('automation_state', sa.String(length=32), nullable=False, server_default='not_attempted'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cover_letter_document_id'], ['application_documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['primary_contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resume_version_id'], ['resumes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_applications_user_status', 'applications', ['user_id', 'status'], unique=False)
    op.create_index('ix_applications_user_next_action', 'applications', ['user_id', 'next_action_at'], unique=False)
    op.create_index('ix_applications_user_deadline', 'applications', ['user_id', 'deadline_at'], unique=False)
    op.create_index('ix_applications_user_created', 'applications', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_applications_company', 'applications', ['company_id'], unique=False)
    op.create_index('ix_applications_job', 'applications', ['job_id'], unique=False)
    op.create_index('uq_active_application_per_user_job', 'applications', ['user_id', 'job_id'], unique=True, postgresql_where=sa.text("status IN ('saved', 'ready_to_apply', 'applied', 'application_viewed', 'screening', 'interview', 'technical_interview', 'final_interview', 'on_hold', 'offer')"))

    # Create application_activities table
    op.create_table('application_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor_type', sa.String(length=32), nullable=False, server_default='manual'),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_entity_type', sa.String(length=64), nullable=True),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_application_activities_app_occurred', 'application_activities', ['application_id', sa.text('occurred_at DESC')], unique=False)

    # Create application_documents table
    op.create_table('application_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', sa.String(length=64), nullable=False),
        sa.Column('file_url', sa.String(length=512), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=128), nullable=True),
        sa.Column('document_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_application_documents_app_type', 'application_documents', ['application_id', 'document_type'], unique=False)

    # Create contacts table
    op.create_table('contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('linkedin_url', sa.String(length=512), nullable=True),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('relationship_status', sa.String(length=64), nullable=True),
        sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_follow_up_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_contacts_user_company', 'contacts', ['user_id', 'company_id'], unique=False)

    # Create application_contacts table
    op.create_table('application_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='other'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', 'contact_id', name='uq_application_contact'),
    )
    op.create_index('ix_application_contacts_application', 'application_contacts', ['application_id'], unique=False)
    op.create_index('ix_application_contacts_contact', 'application_contacts', ['contact_id'], unique=False)

    # Create interviews table
    op.create_table('interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interview_type', sa.String(length=32), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('timezone', sa.String(length=64), nullable=True),
        sa.Column('location_or_meeting_url', sa.String(length=1024), nullable=True),
        sa.Column('interviewer_contact_ids', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='scheduled'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('preparation_notes', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_interviews_user_application', 'interviews', ['user_id', 'application_id'], unique=False)
    op.create_index('ix_interviews_scheduled', 'interviews', ['scheduled_at'], unique=False)

    # Create follow_ups table
    op.create_table('follow_ups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('follow_up_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('reminder_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=32), nullable=False, server_default='manual'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_follow_ups_user_status_due', 'follow_ups', ['user_id', 'status', 'due_at'], unique=False)

    # Create offers table
    op.create_table('offers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('base_salary', sa.Integer(), nullable=True, comment='Base salary in minor units (e.g. cents)'),
        sa.Column('currency', sa.String(length=8), nullable=True),
        sa.Column('bonus', sa.Integer(), nullable=True, comment='Bonus in minor units'),
        sa.Column('equity_notes', sa.Text(), nullable=True),
        sa.Column('employment_type', sa.String(length=64), nullable=True),
        sa.Column('location', sa.String(length=512), nullable=True),
        sa.Column('work_mode', sa.String(length=32), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('benefits_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='received'),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', name='uq_offers_application_id'),
    )
    op.create_index('ix_offers_user_application', 'offers', ['user_id', 'application_id'], unique=False)

    # Create rejections table
    op.create_table('rejections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.String(length=64), nullable=True, comment='Stage at which rejection occurred'),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_employer_initiated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', name='uq_rejections_application_id'),
    )
    op.create_index('ix_rejections_user_application', 'rejections', ['user_id', 'application_id'], unique=False)

    # Create recommendations table
    op.create_table('recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommendation_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='info'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('suggested_action', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('model', sa.String(length=128), nullable=True),
        sa.Column('provider', sa.String(length=128), nullable=True),
        sa.Column('prompt_version', sa.String(length=32), nullable=True),
        sa.Column('dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_recommendations_user_app', 'recommendations', ['user_id', 'application_id'], unique=False)
    op.create_index('ix_recommendations_dismissed', 'recommendations', ['dismissed'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_recommendations_dismissed', table_name='recommendations')
    op.drop_index('ix_recommendations_user_app', table_name='recommendations')
    op.drop_table('recommendations')

    op.drop_index('ix_rejections_user_application', table_name='rejections')
    op.drop_constraint('uq_rejections_application_id', 'rejections', type_='unique')
    op.drop_table('rejections')

    op.drop_index('ix_offers_user_application', table_name='offers')
    op.drop_constraint('uq_offers_application_id', 'offers', type_='unique')
    op.drop_table('offers')

    op.drop_index('ix_follow_ups_user_status_due', table_name='follow_ups')
    op.drop_table('follow_ups')

    op.drop_index('ix_interviews_scheduled', table_name='interviews')
    op.drop_index('ix_interviews_user_application', table_name='interviews')
    op.drop_table('interviews')

    op.drop_index('ix_application_contacts_contact', table_name='application_contacts')
    op.drop_index('ix_application_contacts_application', table_name='application_contacts')
    op.drop_constraint('uq_application_contact', 'application_contacts', type_='unique')
    op.drop_table('application_contacts')

    op.drop_index('ix_contacts_user_company', table_name='contacts')
    op.drop_table('contacts')

    op.drop_index('ix_application_documents_app_type', table_name='application_documents')
    op.drop_table('application_documents')

    op.drop_index('ix_application_activities_app_occurred', table_name='application_activities')
    op.drop_table('application_activities')

    op.drop_index('uq_active_application_per_user_job', table_name='applications')
    op.drop_index('ix_applications_job', table_name='applications')
    op.drop_index('ix_applications_company', table_name='applications')
    op.drop_index('ix_applications_user_created', table_name='applications')
    op.drop_index('ix_applications_user_deadline', table_name='applications')
    op.drop_index('ix_applications_user_next_action', table_name='applications')
    op.drop_index('ix_applications_user_status', table_name='applications')
    op.drop_table('applications')

    op.drop_index('ix_user_company_links_user_company', table_name='user_company_links')
    op.drop_table('user_company_links')

    op.drop_index('ix_companies_industry', table_name='companies')
    op.drop_constraint('uq_companies_normalized_name', 'companies', type_='unique')
    op.drop_constraint('uq_companies_domain', 'companies', type_='unique')
    op.drop_table('companies')
