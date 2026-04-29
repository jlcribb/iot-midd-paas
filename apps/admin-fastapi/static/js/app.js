// Configuración
const API_BASE = '/api';

// Estado global
let currentSection = 'dashboard';
let currentEditId = null;
let clientes = [];
let proyectos = [];
let unidades = [];
let unidadesLegacy = [];
let coreProjects = [];
let unidadesProyectoFilter = '';
let dispositivosUnidadFilter = '';

function getTopologyCanvasBaseUrl() {
    const configured = window.localStorage.getItem('topology_canvas_url');
    if (configured && configured.trim()) {
        return configured.trim();
    }

    const current = new URL(window.location.href);
    const candidate = new URL(`${current.protocol}//${current.hostname}${current.port ? `:${current.port}` : ''}`);
    if (candidate.port === '9000' || candidate.port === '8080') {
        candidate.port = '3000';
    } else if (!candidate.port) {
        candidate.port = '3000';
    }
    candidate.pathname = '/';
    candidate.search = '';
    candidate.hash = '';
    return candidate.toString();
}

function openTopologyCanvas(projectId = '') {
    try {
        const url = new URL(getTopologyCanvasBaseUrl());
        if (projectId) {
            url.searchParams.set('projectId', projectId);
            url.searchParams.set('viewType', 'logical');
        }
        window.open(url.toString(), '_blank', 'noopener,noreferrer');
    } catch (error) {
        console.error('Error abriendo canvas:', error);
        showError('No se pudo abrir el canvas topológico');
    }
}

function openTopologyCanvasFromCurrentContext() {
    let projectId = '';
    if (currentSection === 'unidades' && unidadesProyectoFilter) {
        projectId = unidadesProyectoFilter;
    } else if (currentSection === 'dispositivos' && dispositivosUnidadFilter) {
        const sector = unidades.find((item) => String(item.id) === String(dispositivosUnidadFilter));
        projectId = sector?.project_id || '';
    }
    openTopologyCanvas(projectId);
}

// Utilidades
function showSection(section) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    document.getElementById(section).classList.add('active');
    event.target.classList.add('active');
    
    currentSection = section;
    
    // Cargar datos según la sección
    switch(section) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'proyectos':
            loadProyectos();
            break;
        case 'unidades':
            loadUnidades();
            break;
        case 'dispositivos':
            loadDispositivos();
            break;
        case 'usuarios':
            loadUsuarios();
            break;
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/core/stats`);
        const data = await response.json();
        
        document.getElementById('total-proyectos').textContent = data.total_projects ?? 0;
        document.getElementById('proyectos-activos').textContent = data.active_projects ?? 0;
        document.getElementById('proyectos-en-curso').textContent = data.archived_projects ?? 0;
        document.getElementById('total-unidades').textContent = data.total_sectors ?? 0;
        
        const tbody = document.getElementById('proyectos-tbody');
        const projects = data.projects || [];
        if (projects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No hay proyectos core</td></tr>';
            return;
        }
        tbody.innerHTML = projects.map(p => `
            <tr>
                <td>${p.name}</td>
                <td><span class="badge badge-${getEstadoBadgeClass(p.status)}">${getEstadoLabel(p.status)}</span></td>
                <td>${p.total_sectors ?? 0}</td>
                <td>${p.active_assets ?? 0}/${p.total_assets ?? 0}</td>
                <td>${p.legacy_project_id || '-'}</td>
                <td>${p.id}</td>
                <td class="actions-cell">
                    <button class="btn btn-sm btn-primary" onclick="viewProyectoEstado('${p.id}')">Ver</button>
                    <button class="btn btn-sm btn-secondary" onclick="openTopologyCanvas('${p.id}')">Canvas</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando dashboard:', error);
        showError('Error al cargar el dashboard');
    }
}

function getEstadoBadgeClass(estado) {
    const value = String(estado || '').toLowerCase();
    const estados = {
        activo: 'success',
        active: 'success',
        online: 'success',
        planificado: 'info',
        planned: 'info',
        draft: 'info',
        pausado: 'warning',
        maintenance: 'warning',
        inactive: 'secondary',
        archived: 'secondary',
        cerrado: 'secondary',
        cancelado: 'danger',
        fault: 'danger',
        error: 'danger',
    };
    return estados[value] || 'info';
}

function getEstadoLabel(estado) {
    const value = String(estado || '').toLowerCase();
    const labels = {
        active: 'activo',
        inactive: 'inactivo',
        draft: 'borrador',
        archived: 'archivado',
        planned: 'planificado',
        maintenance: 'mantenimiento',
        online: 'en línea',
        offline: 'fuera de línea',
        fault: 'falla',
        retired: 'retirado',
        provisioning: 'provisionando',
    };
    return labels[value] || estado || '-';
}

async function viewProyectoEstado(proyectoId) {
    try {
        const response = await fetch(`${API_BASE}/core/projects`);
        const data = await response.json();
        const proyecto = (data || []).find((p) => String(p.id) === String(proyectoId));
        if (!proyecto) {
            showError('Proyecto core no encontrado');
            return;
        }
        alert(
            `Proyecto Core:\n\n` +
            `Nombre: ${proyecto.name}\n` +
            `Estado: ${getEstadoLabel(proyecto.status)}\n` +
            `Sectores: ${proyecto.total_sectors ?? 0}\n` +
            `Assets: ${proyecto.active_assets ?? 0}/${proyecto.total_assets ?? 0}`
        );
    } catch (error) {
        console.error('Error obteniendo estado:', error);
        showError('Error al obtener el estado del proyecto');
    }
}

// Proyectos
async function loadProyectos() {
    try {
        await loadCoreProjects();
        
        const tbody = document.getElementById('proyectos-list-tbody');
        if (coreProjects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No hay proyectos</td></tr>';
            return;
        }
        
        tbody.innerHTML = coreProjects.map(p => {
            const legacyProjectId = p.legacy_project_id || '';
            const actions = legacyProjectId
                ? `
                    <button class="btn btn-sm btn-primary" onclick="editProyecto('${legacyProjectId}')">Editar</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProyecto('${legacyProjectId}')">Eliminar</button>
                  `
                : `<span class="badge badge-secondary">Solo core</span>`;
            return `
            <tr>
                <td>${p.name}</td>
                <td><span class="badge badge-${getEstadoBadgeClass(p.status)}">${getEstadoLabel(p.status)}</span></td>
                <td>${p.total_sectors ?? 0}</td>
                <td>${p.active_assets ?? 0}/${p.total_assets ?? 0}</td>
                <td>${legacyProjectId || '-'}</td>
                <td class="actions-cell">
                    ${actions}
                    <button class="btn btn-sm btn-secondary" onclick="openTopologyCanvas('${p.id}')">Canvas</button>
                </td>
            </tr>
        `;
        }).join('');
    } catch (error) {
        console.error('Error cargando proyectos:', error);
        showError('Error al cargar proyectos');
    }
}

async function loadCoreProjects() {
    try {
        const response = await fetch(`${API_BASE}/core/projects`);
        coreProjects = await response.json();
    } catch (error) {
        console.error('Error cargando proyectos core:', error);
        coreProjects = [];
    }
}

async function loadProyectosList() {
    try {
        const response = await fetch(`${API_BASE}/proyectos/`);
        proyectos = await response.json();
    } catch (error) {
        console.error('Error cargando proyectos para select:', error);
        proyectos = [];
    }
}

async function loadUnidadesList() {
    try {
        const response = await fetch(`${API_BASE}/core/sectors?active=true`);
        unidades = await response.json();
    } catch (error) {
        console.error('Error cargando sectores para select:', error);
        unidades = [];
    }
}

async function loadUnidadesLegacyList() {
    try {
        const response = await fetch(`${API_BASE}/unidades/`);
        unidadesLegacy = await response.json();
    } catch (error) {
        console.error('Error cargando unidades legacy para formulario:', error);
        unidadesLegacy = [];
    }
}

function populateUnidadesProyectoFilter() {
    const filter = document.getElementById('unidades-proyecto-filter');
    if (!filter) return;
    
    const currentValue = filter.value || unidadesProyectoFilter;
    const options = [
        '<option value="">Todos los proyectos</option>',
        ...coreProjects.map((p) => `<option value="${p.id}">${p.name}</option>`)
    ];
    filter.innerHTML = options.join('');
    
    const exists = coreProjects.some((p) => String(p.id) === String(currentValue));
    filter.value = exists ? currentValue : '';
    unidadesProyectoFilter = filter.value;
}

function populateDispositivosUnidadFilter() {
    const filter = document.getElementById('dispositivos-unidad-filter');
    if (!filter) return;
    
    const currentValue = filter.value || dispositivosUnidadFilter;
    const options = [
        '<option value="">Todos los sectores</option>',
        ...unidades.map((u) => `<option value="${u.id}">${u.name} (${u.project_name || getProyectoNombreById(u.project_id)})</option>`)
    ];
    filter.innerHTML = options.join('');
    
    const exists = unidades.some((u) => String(u.id) === String(currentValue));
    filter.value = exists ? currentValue : '';
    dispositivosUnidadFilter = filter.value;
}

function onUnidadesProyectoFilterChange() {
    const filter = document.getElementById('unidades-proyecto-filter');
    unidadesProyectoFilter = filter ? filter.value : '';
    loadUnidades();
}

function onDispositivosUnidadFilterChange() {
    const filter = document.getElementById('dispositivos-unidad-filter');
    dispositivosUnidadFilter = filter ? filter.value : '';
    loadDispositivos();
}

function getProyectoNombreById(proyectoId) {
    const coreProject = coreProjects.find((p) => String(p.id) === String(proyectoId));
    if (coreProject) return coreProject.name;
    const legacyProject = proyectos.find((p) => String(p.id) === String(proyectoId));
    return legacyProject ? legacyProject.nombre : (proyectoId || '-');
}

function getUnidadNombreById(unidadId) {
    const unidad = unidades.find(u => String(u.id) === String(unidadId));
    return unidad ? (unidad.name || unidad.nombre) : (unidadId || '-');
}

async function syncCoreByLegacyProjectId(legacyProjectId) {
    if (!legacyProjectId) return;
    try {
        await fetch(`${API_BASE}/proyectos/${legacyProjectId}/sync-core`, { method: 'POST' });
    } catch (error) {
        console.warn('No se pudo sincronizar core schema:', error);
    }
}

async function editProyecto(id) {
    try {
        const response = await fetch(`${API_BASE}/proyectos/${id}`);
        const proyecto = await response.json();
        currentEditId = id;
        openModal('proyecto', proyecto);
    } catch (error) {
        console.error('Error obteniendo proyecto:', error);
        showError('Error al obtener el proyecto');
    }
}

async function deleteProyecto(id) {
    if (!confirm('¿Estás seguro de eliminar este proyecto?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/proyectos/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showSuccess('Proyecto eliminado exitosamente');
            loadProyectos();
        } else {
            showError('Error al eliminar el proyecto');
        }
    } catch (error) {
        console.error('Error eliminando proyecto:', error);
        showError('Error al eliminar el proyecto');
    }
}

// Unidades
async function loadUnidades() {
    try {
        await loadCoreProjects();
        populateUnidadesProyectoFilter();
        
        const params = new URLSearchParams();
        if (unidadesProyectoFilter) {
            params.append('project_id', unidadesProyectoFilter);
        }
        params.append('active', 'true');
        const suffix = params.toString() ? `?${params.toString()}` : '';
        const response = await fetch(`${API_BASE}/core/sectors${suffix}`);
        unidades = await response.json();
        
        const tbody = document.getElementById('unidades-list-tbody');
        if (unidades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No hay sectores</td></tr>';
            return;
        }
        
        tbody.innerHTML = unidades.map(u => `
            <tr>
                <td>${u.name}</td>
                <td>${u.project_name || getProyectoNombreById(u.project_id)}</td>
                <td>${u.code || '-'}</td>
                <td><span class="badge badge-${u.is_active ? 'success' : 'secondary'}">${u.is_active ? 'Activo' : 'Inactivo'}</span></td>
                <td class="actions-cell">
                    ${
                        u.legacy_unit_id
                            ? `<button class="btn btn-sm btn-primary" onclick="editUnidad('${u.legacy_unit_id}')">Editar</button>
                               <button class="btn btn-sm btn-danger" onclick="deleteUnidad('${u.legacy_unit_id}', '${u.legacy_project_id || ''}')">Eliminar</button>`
                            : '<span class="badge badge-secondary">Solo core</span>'
                    }
                    <button class="btn btn-sm btn-secondary" onclick="openTopologyCanvas('${u.project_id}')">Canvas</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando sectores:', error);
        showError('Error al cargar sectores');
    }
}

async function editUnidad(id) {
    if (!id) {
        showError('Este sector no tiene vínculo legacy para edición.');
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/unidades/${id}`);
        const unidad = await response.json();
        currentEditId = id;
        openModal('unidad', unidad);
    } catch (error) {
        console.error('Error obteniendo unidad:', error);
        showError('Error al obtener la unidad');
    }
}

async function deleteUnidad(id, legacyProjectId = '') {
    if (!id) {
        showError('Este sector no tiene vínculo legacy para eliminación.');
        return;
    }
    if (!confirm('¿Estás seguro de eliminar este sector?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/unidades/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showSuccess('Sector eliminado exitosamente');
            if (legacyProjectId) {
                await syncCoreByLegacyProjectId(legacyProjectId);
            }
            await loadUnidades();
            await loadDispositivos();
        } else {
            showError('Error al eliminar el sector');
        }
    } catch (error) {
        console.error('Error eliminando sector:', error);
        showError('Error al eliminar el sector');
    }
}

// Dispositivos
async function loadDispositivos() {
    try {
        await loadCoreProjects();
        await loadUnidadesList();
        populateDispositivosUnidadFilter();
        
        const params = new URLSearchParams();
        if (dispositivosUnidadFilter) {
            params.append('sector_id', dispositivosUnidadFilter);
        }
        params.append('active', 'true');
        const suffix = params.toString() ? `?${params.toString()}` : '';
        const response = await fetch(`${API_BASE}/core/assets${suffix}`);
        const dispositivos = await response.json();
        
        const tbody = document.getElementById('dispositivos-list-tbody');
        if (dispositivos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No hay assets</td></tr>';
            return;
        }
        
        tbody.innerHTML = dispositivos.map(d => `
            <tr>
                <td>${d.name}</td>
                <td>${d.project_name || getProyectoNombreById(d.project_id)}</td>
                <td>${d.sector_name || getUnidadNombreById(d.sector_id)}</td>
                <td>${d.asset_type}</td>
                <td><span class="badge badge-${getEstadoBadgeClass(d.status)}">${getEstadoLabel(d.status)}</span></td>
                <td class="actions-cell">
                    ${
                        d.legacy_dispositivo_proyecto_id
                            ? `<button class="btn btn-sm btn-primary" onclick="editDispositivo('${d.legacy_dispositivo_proyecto_id}')">Editar</button>
                               <button class="btn btn-sm btn-danger" onclick="deleteDispositivo('${d.legacy_dispositivo_proyecto_id}', '${d.legacy_project_id || ''}')">Eliminar</button>`
                            : '<span class="badge badge-secondary">Solo core</span>'
                    }
                    <button class="btn btn-sm btn-secondary" onclick="openTopologyCanvas('${d.project_id}')">Canvas</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando assets:', error);
        showError('Error al cargar assets');
    }
}

async function editDispositivo(id) {
    if (!id) {
        showError('Este asset no tiene vínculo legacy para edición.');
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/dispositivos/${id}`);
        const dispositivo = await response.json();
        currentEditId = id;
        openModal('dispositivo', dispositivo);
    } catch (error) {
        console.error('Error obteniendo dispositivo:', error);
        showError('Error al obtener el dispositivo');
    }
}

async function deleteDispositivo(id, legacyProjectId = '') {
    if (!id) {
        showError('Este asset no tiene vínculo legacy para eliminación.');
        return;
    }
    if (!confirm('¿Estás seguro de eliminar este asset?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/dispositivos/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showSuccess('Asset eliminado exitosamente');
            if (legacyProjectId) {
                await syncCoreByLegacyProjectId(legacyProjectId);
            }
            await loadDispositivos();
        } else {
            showError('Error al eliminar el asset');
        }
    } catch (error) {
        console.error('Error eliminando asset:', error);
        showError('Error al eliminar el asset');
    }
}

// Usuarios
async function loadUsuarios() {
    try {
        const response = await fetch(`${API_BASE}/usuarios/`);
        const usuarios = await response.json();
        
        const tbody = document.getElementById('usuarios-list-tbody');
        if (usuarios.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No hay usuarios</td></tr>';
            return;
        }
        
        tbody.innerHTML = usuarios.map(u => `
            <tr>
                <td>${u.email}</td>
                <td>${u.nombre} ${u.apellido || ''}</td>
                <td><span class="badge badge-info">${u.rol}</span></td>
                <td><span class="badge badge-${u.activo ? 'success' : 'danger'}">${u.activo ? 'Activo' : 'Inactivo'}</span></td>
                <td>${u.ultimo_login || '-'}</td>
                <td class="actions-cell">
                    <button class="btn btn-sm btn-primary" onclick="editUsuario('${u.id}')">Editar</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteUsuario('${u.id}')">Eliminar</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando usuarios:', error);
        showError('Error al cargar usuarios');
    }
}

async function editUsuario(id) {
    try {
        const response = await fetch(`${API_BASE}/usuarios/${id}`);
        const usuario = await response.json();
        currentEditId = id;
        openModal('usuario', usuario);
    } catch (error) {
        console.error('Error obteniendo usuario:', error);
        showError('Error al obtener el usuario');
    }
}

async function deleteUsuario(id) {
    if (!confirm('¿Estás seguro de eliminar este usuario?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/usuarios/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showSuccess('Usuario eliminado exitosamente');
            loadUsuarios();
        } else {
            showError('Error al eliminar el usuario');
        }
    } catch (error) {
        console.error('Error eliminando usuario:', error);
        showError('Error al eliminar el usuario');
    }
}

// Modal
async function openModal(type, data = null) {
    currentEditId = data ? data.id : null;
    const modal = document.getElementById('modal');
    const title = document.getElementById('modal-title');
    const formContent = document.getElementById('modal-form-content');
    
    title.textContent = data ? `Editar ${getTypeName(type)}` : `Nuevo ${getTypeName(type)}`;
    
    if (type === 'unidad' && proyectos.length === 0) {
        await loadProyectosList();
    }
    if (type === 'dispositivo') {
        if (proyectos.length === 0) {
            await loadProyectosList();
        }
        if (unidadesLegacy.length === 0) {
            await loadUnidadesLegacyList();
        }
    }
    formContent.innerHTML = getFormHTML(type, data);
    if (type === 'dispositivo') {
        bindDispositivoSelects();
    }
    
    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
    currentEditId = null;
}

function getTypeName(type) {
    const names = {
        'proyecto': 'Proyecto',
        'unidad': 'Sector',
        'dispositivo': 'Asset',
        'usuario': 'Usuario'
    };
    return names[type] || type;
}

function getFormHTML(type, data) {
    const forms = {
        'proyecto': `
            <div class="form-group">
                <label>Cliente ID</label>
                <input type="text" name="cliente_id" value="${data?.cliente_id || ''}" required>
            </div>
            <div class="form-group">
                <label>Nombre</label>
                <input type="text" name="nombre" value="${data?.nombre || ''}" required>
            </div>
            <div class="form-group">
                <label>Descripción</label>
                <textarea name="descripcion">${data?.descripcion || ''}</textarea>
            </div>
            <div class="form-group">
                <label>Estado</label>
                <select name="estado" required>
                    <option value="planificado" ${data?.estado === 'planificado' ? 'selected' : ''}>Planificado</option>
                    <option value="activo" ${data?.estado === 'activo' ? 'selected' : ''}>Activo</option>
                    <option value="pausado" ${data?.estado === 'pausado' ? 'selected' : ''}>Pausado</option>
                    <option value="cerrado" ${data?.estado === 'cerrado' ? 'selected' : ''}>Cerrado</option>
                </select>
            </div>
            <div class="form-group">
                <label>Fecha Inicio</label>
                <input type="date" name="fecha_inicio" value="${data?.fecha_inicio || ''}">
            </div>
            <div class="form-group">
                <label>Fecha Fin</label>
                <input type="date" name="fecha_fin" value="${data?.fecha_fin || ''}">
            </div>
            <div class="form-group">
                <label>Presupuesto</label>
                <input type="number" step="0.01" name="presupuesto" value="${data?.presupuesto || ''}">
            </div>
        `,
        'unidad': `
            <div class="form-group">
                <label>Proyecto ID</label>
                <select name="proyecto_id" required>
                    <option value="">Selecciona un proyecto</option>
                    ${proyectos.map(p => `
                        <option value="${p.id}" ${data?.proyecto_id === p.id ? 'selected' : ''}>
                            ${p.nombre}
                        </option>
                    `).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Nombre</label>
                <input type="text" name="nombre" value="${data?.nombre || ''}" required>
            </div>
            <div class="form-group">
                <label>Descripción</label>
                <textarea name="descripcion">${data?.descripcion || ''}</textarea>
            </div>
            <div class="form-group">
                <label>Ubicación</label>
                <input type="text" name="ubicacion" value="${data?.ubicacion || ''}">
            </div>
            <div class="form-group">
                <label>Responsable</label>
                <input type="text" name="responsable" value="${data?.responsable || ''}">
            </div>
            <div class="form-group">
                <label>Email Responsable</label>
                <input type="email" name="responsable_email" value="${data?.responsable_email || ''}">
            </div>
        `,
        'dispositivo': `
            <div class="form-group">
                <label>Proyecto ID</label>
                <select name="proyecto_id" id="dispositivo-proyecto-select" required>
                    <option value="">Selecciona un proyecto</option>
                    ${proyectos.map(p => `
                        <option value="${p.id}" ${data?.proyecto_id === p.id ? 'selected' : ''}>
                            ${p.nombre}
                        </option>
                    `).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Dispositivo ID</label>
                <input type="text" name="dispositivo_id" value="${data?.dispositivo_id || ''}" required>
            </div>
            <div class="form-group">
                <label>Unidad ID</label>
                <select name="unidad_id" id="dispositivo-unidad-select">
                    <option value="">Selecciona una unidad</option>
                    ${unidadesLegacy
                        .filter(u => !data?.proyecto_id || String(u.proyecto_id) === String(data?.proyecto_id))
                        .map(u => `
                            <option value="${u.id}" ${data?.unidad_id === u.id ? 'selected' : ''}>
                                ${u.nombre}
                            </option>
                        `).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Nombre Personalizado</label>
                <input type="text" name="nombre_personalizado" value="${data?.nombre_personalizado || ''}">
            </div>
            <div class="form-group">
                <label>Fecha Instalación</label>
                <input type="date" name="fecha_instalacion" value="${data?.fecha_instalacion || ''}" required>
            </div>
        `,
        'usuario': `
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" value="${data?.email || ''}" required>
            </div>
            <div class="form-group">
                <label>Nombre</label>
                <input type="text" name="nombre" value="${data?.nombre || ''}" required>
            </div>
            <div class="form-group">
                <label>Apellido</label>
                <input type="text" name="apellido" value="${data?.apellido || ''}">
            </div>
            <div class="form-group">
                <label>Contraseña</label>
                <input type="password" name="password" ${!data ? 'required' : ''}>
            </div>
            <div class="form-group">
                <label>Rol</label>
                <select name="rol" required>
                    <option value="lectura" ${data?.rol === 'lectura' ? 'selected' : ''}>Lectura</option>
                    <option value="cliente" ${data?.rol === 'cliente' ? 'selected' : ''}>Cliente</option>
                    <option value="tecnico" ${data?.rol === 'tecnico' ? 'selected' : ''}>Técnico</option>
                    <option value="supervisor" ${data?.rol === 'supervisor' ? 'selected' : ''}>Supervisor</option>
                    <option value="admin" ${data?.rol === 'admin' ? 'selected' : ''}>Admin</option>
                </select>
            </div>
        `
    };
    return forms[type] || '';
}

function bindDispositivoSelects() {
    const proyectoSelect = document.getElementById('dispositivo-proyecto-select');
    const unidadSelect = document.getElementById('dispositivo-unidad-select');
    if (!proyectoSelect || !unidadSelect) return;
    
    const selectedProyectoId = proyectoSelect.value;
    const selectedUnidadId = unidadSelect.value;
    
    const options = [
        `<option value="">Selecciona una unidad</option>`,
        ...unidadesLegacy
            .filter(u => !selectedProyectoId || String(u.proyecto_id) === String(selectedProyectoId))
            .map(u => `
                <option value="${u.id}" ${selectedUnidadId === u.id ? 'selected' : ''}>
                    ${u.nombre}
                </option>
            `)
    ];
    
    unidadSelect.innerHTML = options.join('');
    
    proyectoSelect.addEventListener('change', () => {
        const newProyectoId = proyectoSelect.value;
        const newOptions = [
            `<option value="">Selecciona una unidad</option>`,
            ...unidadesLegacy
                .filter(u => !newProyectoId || String(u.proyecto_id) === String(newProyectoId))
                .map(u => `<option value="${u.id}">${u.nombre}</option>`)
        ];
        unidadSelect.innerHTML = newOptions.join('');
    });
}

async function handleSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Eliminar campos vacíos para evitar errores de validación (ej: fechas vacías)
    Object.keys(data).forEach((key) => {
        if (data[key] === "") {
            delete data[key];
        }
    });
    
    // Normalizar campos numéricos si vienen como string
    if (data.presupuesto !== undefined) {
        data.presupuesto = parseFloat(data.presupuesto);
        if (Number.isNaN(data.presupuesto)) {
            delete data.presupuesto;
        }
    }
    if (data.prioridad !== undefined) {
        data.prioridad = parseInt(data.prioridad, 10);
        if (Number.isNaN(data.prioridad)) {
            delete data.prioridad;
        }
    }
    
    // Determinar tipo y endpoint
    const type = currentSection.slice(0, -1); // Remove 's' from end
    const endpoint = `${API_BASE}/${currentSection}/`;
    const method = currentEditId ? 'PUT' : 'POST';
    const url = currentEditId ? `${endpoint}${currentEditId}` : endpoint;
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        let payload = {};
        try {
            payload = await response.json();
        } catch (jsonError) {
            payload = {};
        }
        
        if (response.ok) {
            const affectedLegacyProjectId = (
                payload?.proyecto_id
                || data?.proyecto_id
                || (currentSection === 'proyectos' ? currentEditId : null)
            );
            if (currentSection === 'unidades' || currentSection === 'dispositivos') {
                await syncCoreByLegacyProjectId(affectedLegacyProjectId);
            }
            showSuccess(`${getTypeName(type)} ${currentEditId ? 'actualizado' : 'creado'} exitosamente`);
            closeModal();
            // Recargar lista
            switch(currentSection) {
                case 'proyectos': loadProyectos(); break;
                case 'unidades': loadUnidades(); break;
                case 'dispositivos': loadDispositivos(); break;
                case 'usuarios': loadUsuarios(); break;
            }
        } else {
            showError(payload?.detail || 'Error al guardar');
        }
    } catch (error) {
        console.error('Error guardando:', error);
        showError('Error al guardar');
    }
}

// Utilidades UI
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    document.querySelector('.main-content').insertBefore(errorDiv, document.querySelector('.content-section.active'));
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    document.querySelector('.main-content').insertBefore(successDiv, document.querySelector('.content-section.active'));
    setTimeout(() => successDiv.remove(), 5000);
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});
