# Site/Apartman Yonetim SaaS + Data Platform

Bu repo, site/apartman yonetim MVP'si ile data engineering platformunu birlikte gelistirmek icin olusturuldu.

## Sprint 1 Kapsami (Tamamlandi)
- Monorepo klasor yapisi olusturuldu
- Docker Compose ile PostgreSQL + Redis + API + Web calisir hale getirildi
- FastAPI baslangic iskeleti + health endpoint + test + Alembic iskeleti eklendi
- Next.js (TypeScript + Tailwind) baslangic ekrani ve API health karti eklendi
- GitHub Actions CI eklendi (API lint/test, Web lint/build, Compose config)

## Sprint 2 Kapsami (Tamamlandi)
- Auth akisi eklendi: `register`, `login`, `me`
- RBAC temeli eklendi: `admin`, `manager`, `accountant`, `resident`
- Tenant context kontrolu eklendi (`X-Site-Id`)
- `sites` ve `users` tablolari Alembic migration ile eklendi
- API container startup adimina migration calistirma eklendi
- Web tarafinda `login`, `register`, `dashboard` sayfalari eklendi
- Auth + tenant akisi icin API testleri eklendi

## Dizin Yapisi
- `apps/api` : FastAPI backend
- `apps/web` : Next.js frontend
- `data` : Airflow + dbt iskeleti
- `infra` : altyapi dosyalari
- `docs` : ADR ve sprint notlari

## Hizli Baslangic
1. Ornek ortam dosyasini kopyala
2. Servisleri kaldir
3. Health endpointi kontrol et

```zsh
cd /Users/umuterenakbas/Desktop/SaaS
cp .env.example .env
docker compose up -d
curl -sS http://localhost:8000/api/v1/health
```

## Lokal Kontroller
### API
```zsh
cd /Users/umuterenakbas/Desktop/SaaS/apps/api
/Users/umuterenakbas/Desktop/SaaS/.venv/bin/python -m ruff check .
/Users/umuterenakbas/Desktop/SaaS/.venv/bin/python -m pytest -q
```

### Web
```zsh
cd /Users/umuterenakbas/Desktop/SaaS/apps/web
npm run lint
npm run build
```

## Sprint 2 Hızlı Doğrulama
```zsh
cd /Users/umuterenakbas/Desktop/SaaS
docker compose up -d postgres redis api web
curl -sS http://localhost:3000/login | head -n 5
curl -sS http://localhost:8000/api/v1/health
docker compose down
```
