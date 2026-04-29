ALTER TABLE public.projects
ADD COLUMN IF NOT EXISTS parametric_control_enabled BOOLEAN NOT NULL DEFAULT FALSE;
