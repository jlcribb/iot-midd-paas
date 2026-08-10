export interface ProjectControlUiState {
  canManage: boolean;
  isAccessLoading: boolean;
  message: string;
}

export function resolveProjectControlUiState(input: {
  projectId: string | null;
  isAccessLoading: boolean;
  hasAccessSnapshot: boolean;
  allowedProjectIds: string[];
  manageableProjectIds: string[];
}): ProjectControlUiState {
  if (!input.projectId) {
    return { canManage: false, isAccessLoading: input.isAccessLoading, message: "Seleccioná un proyecto para consultar su capacidad de control." };
  }

  if (input.isAccessLoading) {
    return { canManage: false, isAccessLoading: true, message: "Verificando permisos de control..." };
  }

  if (!input.hasAccessSnapshot) {
    return { canManage: false, isAccessLoading: false, message: "Iniciá sesión para administrar el control paramétrico." };
  }

  if (input.manageableProjectIds.includes(input.projectId)) {
    return { canManage: true, isAccessLoading: false, message: "Tu rol permite cambiar este control para el proyecto seleccionado." };
  }

  if (input.allowedProjectIds.includes(input.projectId)) {
    return { canManage: false, isAccessLoading: false, message: "Tu rol permite consultar este estado, pero no cambiarlo." };
  }

  return { canManage: false, isAccessLoading: false, message: "Este proyecto está fuera de tu scope de control." };
}
