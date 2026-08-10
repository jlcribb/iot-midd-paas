CREATE TABLE IF NOT EXISTS public.project_control_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_email TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT project_control_memberships_actor_email_normalized
        CHECK (actor_email = lower(btrim(actor_email)) AND btrim(actor_email) <> ''),
    CONSTRAINT project_control_memberships_role_valid
        CHECK (role IN ('viewer', 'operator', 'admin')),
    CONSTRAINT project_control_memberships_actor_project_unique
        UNIQUE (actor_email, project_id)
);

CREATE INDEX IF NOT EXISTS idx_project_control_memberships_actor_enabled
ON public.project_control_memberships(actor_email, enabled, project_id);
