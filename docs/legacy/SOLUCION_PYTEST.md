# 🔧 Solución al Error de pytest-postgresql

## ❌ Error Encontrado

```
ImportError: no pq wrapper available.
- couldn't import psycopg 'c' implementation: No module named 'psycopg_c'
- couldn't import psycopg 'binary' implementation: No module named 'psycopg_binary'
```

## 🔍 Causa

El paquete `pytest-postgresql` requiere `psycopg-binary` (versión 3), pero solo está instalado `psycopg2-binary` (versión 2). Son paquetes diferentes y ambos pueden coexistir.

## ✅ Solución

Ejecuta este comando en tu terminal:

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar psycopg-binary
pip install psycopg-binary

# Verificar que pytest funciona
pytest --version
```

O usa el script automático:

```bash
./fix_pytest.sh
```

## 📝 Nota

- `psycopg2-binary` se usa en el proyecto principal
- `psycopg-binary` se necesita solo para `pytest-postgresql`
- Ambos pueden coexistir sin problemas

## ✅ Verificación

Después de instalar, deberías ver:

```bash
$ pytest --version
pytest 8.2.2
```

Sin errores de importación.

---

**¡Ejecuta el comando en tu terminal!** 🚀
