CREATE TABLE IF NOT EXISTS public.project_control_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    variable TEXT NOT NULL,
    context_selector JSONB NOT NULL DEFAULT '{}'::jsonb,
    policy_type TEXT NOT NULL DEFAULT 'proportional',
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    priority INTEGER NOT NULL DEFAULT 0,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT project_control_policies_variable_not_blank CHECK (btrim(variable) <> ''),
    CONSTRAINT project_control_policies_policy_type_not_blank CHECK (btrim(policy_type) <> ''),
    CONSTRAINT project_control_policies_priority_nonnegative CHECK (priority >= 0),
    CONSTRAINT project_control_policies_version_positive CHECK (version >= 1),
    CONSTRAINT project_control_policies_context_selector_object CHECK (jsonb_typeof(context_selector) = 'object'),
    CONSTRAINT project_control_policies_params_object CHECK (jsonb_typeof(params) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_project_control_policies_project_variable_enabled
ON public.project_control_policies(project_id, variable, enabled);

CREATE INDEX IF NOT EXISTS idx_project_control_policies_priority_version
ON public.project_control_policies(project_id, variable, priority DESC, version DESC);

CREATE INDEX IF NOT EXISTS idx_project_control_policies_context_selector
ON public.project_control_policies USING GIN (context_selector);
