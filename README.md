
# 🌌 PixelPixies Fase II — Plataforma Turística con IA

Proyecto web desarrollado en Django con microservicios basados en FastAPI para análisis de sentimientos y recomendaciones inteligentes. Todo orquestado con Docker Compose. 🚀

---

## 🧩 Tecnologías

- 🐍 **Django** — Backend principal
- ⚡ **FastAPI** — Microservicios (sentimientos & recomendación)
- 🐳 **Docker & Docker Compose** — Contenedores
- 🧠 **GenAI + Asistente de voz** — IA generativa de imagen (FLUX-schnell) + Speech to text model (Whisper) + LLM 
- 📦 **Git LFS** — Archivos grandes (.pkl, .sqlite3, imágenes)

---

---

## 🧪 Cómo se usa

> ⚠️ Asegúrate de tener libres los puertos **8000**, **8001** y **8002** en tu máquina.

### ✅ Opción rápida (recomendada)

Las imágenes de todos los servicios ya están disponibles en **Docker Hub**, así que con un solo comando podés levantar todo el sistema:

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

Podés usar estos usuarios directamente al iniciar sesión en la web.

---

### 🛠️ Opción avanzada: construir las imágenes tú mismo

Si querés construir las imágenes localmente, hacé lo siguiente:

1. **Editá el `docker-compose.yaml`** y:
   - ❌ Comentá las líneas que dicen `image:`
   - ✅ Descomentá las líneas que dicen `build:`

2. Asegurate de tener creado un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Y completalo con tus claves necesarias (por ejemplo, `REPLICATE_API_TOKEN`, utilizada porque IA generativa de imagen consume demasiada memoria RAM de GPU).

3. Luego ejecutá:

```bash
docker compose up --build
```
---

### ❓ ¿Problemas ejecutando?

Si tenés dificultades para ejecutar el sistema, podés consultar directamente a:

📩 **pixelpixies@gmail.com**

¡Estaremos encantados de ayudarte!

---
