# 🌌 PixelPixies Fase II — Plataforma Turística con IA

Proyecto web desarrollado en Django con microservicios basados en FastAPI para análisis de sentimientos y recomendaciones inteligentes. Todo orquestado con Docker Compose. 🚀

---

## 🧩 Tecnologías

- 🐍 **Django** — Backend principal
- ⚡ **FastAPI** — Microservicios (sentimiento & recomendación)
- 🐳 **Docker & Docker Compose** — Contenedores
- 🧠 **Scikit-learn + modelos propios** — IA personalizada
- 💾 **SQLite** — Base de datos ligera
- 📦 **Git LFS** — Archivos grandes (.pkl, .sqlite3, imágenes)

---

## 🛠️ Estructura del proyecto

```bash
pixelpixies-faseII/
│
├── GreenLakeWeb/            # Proyecto Django
│   ├── turismo/             # App principal
│   ├── static/              # Archivos estáticos (CSS, JS, imágenes)
│   └── templates/           # HTML
│
├── app-ir-srv2/             # Microservicio de recomendación
├── app-snt-kwv1/            # Microservicio de análisis de sentimientos
├── docker-compose.yaml      # Orquestación de contenedores
├── .env.example             # Variables de entorno (sin secretos)
└── .gitattributes/.gitignore
