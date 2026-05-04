# Sprint 02 - Auth, RBAC, Tenant

## Hedef
Kullanici kimlik dogrulama, rol bazli yetkilendirme ve tenant/site baglami kontrolunu MVP seviyesinde calisir hale getirmek.

## Tamamlanan Isler
- [x] Auth endpointleri eklendi: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- [x] Tenant endpointleri eklendi: `GET /api/v1/tenant/context`, `GET /api/v1/tenant/admin-area`
- [x] `Site` ve `User` modelleri eklendi
- [x] `UserRole` enum (`admin`, `manager`, `accountant`, `resident`) eklendi
- [x] JWT token uretim/dogrulama akisi eklendi
- [x] Sifre hashleme/verify akisi eklendi
- [x] Alembic migration eklendi (`sites`, `users`, `user_role`)
- [x] API Docker startup adimina `alembic upgrade head` eklendi
- [x] Web sayfalari eklendi: `/login`, `/register`, `/dashboard`
- [x] API auth/tenant testleri eklendi

## Dogrulama Sonuclari
- API lint: PASS
- API tests: PASS (3 test)
- Web lint/build: PASS
- Docker smoke test: PASS (`/login` ve auth+tenant akisi)

## Notlar
- RBAC ilk fazda backend guard seviyesiyle uygulanmistir.
- Frontend route guard su an basit token kontrolu + dashboard icinde me/context fetch yaklasimi ile calisir.
- Sprint 3'te domain CRUD tablolarina gecilirken tenant zorunlulugu API seviyesinde standardize edilecektir.
