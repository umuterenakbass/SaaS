# Site/Apartman Yonetim SaaS + Data Platform

Bu repo, site/apartman yonetim MVP'si ile data engineering platformunu birlikte gelistirmek icin olusturuldu.

## Sprint 1 Kapsami (Tamamlandi)
- Monorepo klasor yapisi olusturuldu
- Docker Compose ile PostgreSQL + Redis + API + Web calisir hale getirildi
- FastAPI baslangic iskeleti + health endpoint + test + Alembic iskeleti eklendi
- Next.js (TypeScript + Tailwind) baslangic ekrani ve API health karti eklendi
- GitHub Actions CI eklendi (API lint/test, Web lint/build, Compose config)

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
