
# 🌌 PixelPixies Fase II — Plataforma Turística con IA

Proyecto web desarrollado en Django con microservicios basados en FastAPI para análisis de sentimientos y recomendaciones inteligentes. Todo orquestado con Docker Compose. 🚀

---

## 🧩 Tecnologías

- 🐍 **Django** — Backend principal
- ⚡ **FastAPI** — Microservicios (sentimientos & recomendación)
- 🐳 **Docker & Docker Compose** — Contenedores
- 🧠 **GenAI + Asistente de voz** — IA generativa de imagen (FLUX-schnell) + Speech to text (Whisper) + LLM 
- 📦 **Git LFS** — Archivos grandes (.pkl, .sqlite3, imágenes)

---

## 🧪 Cómo se usa

> ⚠️ Asegúrate de tener libres los puertos **8000**, **8001** y **8002** en tu máquina.

### ✅ Opción rápida (recomendada)

Las imágenes de todos los servicios ya están disponibles en **Docker Hub**, así que con un solo comando puedes levantar todo el sistema:
Tan solo necesitarías descargar el archivo docker-compose.yaml del repositorio y realizar lo siguiente:

```bash
docker compose up
```

Eso te arrancará:

| Servicio       | URL                    | Descripción                          |
|----------------|------------------------|--------------------------------------|
| 🌐 Django Web   | http://localhost:8000  | Interfaz principal de la plataforma |
| 🧠 Sentimientos | http://localhost:8001  | Microservicio de análisis emocional |
| 🏨 Recomendación | http://localhost:8002  | Motor de sugerencias personalizadas |

---

### 👤 Usuarios de prueba

El sistema ya incluye varios usuarios listos para testear todas las funcionalidades:

| Rol         | Usuario       | Contraseña    |
|-------------|---------------|---------------|
| Admin       | `admin`       | `admin`       |
| Turista     | `turista1`    | `123456789`   |
|             | `turista3`    | `123456789`   |
| Hotelero    | `hotelero1`   | `123456789`   |
|             | `hotelero2`   | `123456789`   |
|             | `hotelero3`   | `123456789`   |
| Servicio IA | `servicio1`   | `123456789`   |

Puedes usar estos usuarios directamente al iniciar sesión en la web.

---

### 🛠️ Opción avanzada: construir las imágenes tú mismo

Si quieres construir las imágenes localmente, haz lo siguiente:

1. **Edita el `docker-compose.yaml`** y:
   - ❌ Comenta las líneas que dicen `image:`
   - ✅ Descomenta las líneas que dicen `build:`

2. Asegurate de tener creado un archivo `.env`:

Y complétalo con tus claves necesarias (por ejemplo, `REPLICATE_API_TOKEN`, utilizada porque IA generativa de imagen consume demasiada memoria RAM de GPU).

3. Luego ejecuta:

```bash
docker compose up --build
```
---

### ❓ ¿Problemas ejecutando?

Si tienes dificultades para ejecutar el sistema, puedes consultar directamente a:

📩 **pixelpixies@gmail.com**

¡Estaremos encantadas de ayudarte!

---
