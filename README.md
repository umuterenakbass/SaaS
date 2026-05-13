# 🏢 SiteYönet — Multi-Tenant Site Yönetim SaaS'ı

> **Site yöneticileri ve sakinler için uçtan uca aidat, borç ve ödeme yönetim platformu.**  
> FastAPI · Next.js 16 · PostgreSQL · SQLAlchemy · Alembic · Tailwind CSS

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![Tests](https://img.shields.io/badge/tests-68%20passed-brightgreen)](#testing)

---

## 📋 İçindekiler

- [Proje Hakkında](#proje-hakkında)
- [Mimari](#mimari)
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Çalıştırma](#çalıştırma)
- [API Endpointleri](#api-endpointleri)
- [Veritabanı Şeması](#veritabanı-şeması)
- [Testing](#testing)
- [Sprint Geçmişi](#sprint-geçmişi)
- [Klasör Yapısı](#klasör-yapısı)

---

## Proje Hakkında

**SiteYönet**, apartman ve site yöneticilerinin aidat tahsilatı, borç takibi, sakin yönetimi ve finansal raporlamayı tek platformdan yapabildiği çok kiracılı (multi-tenant) bir SaaS uygulamasıdır.

Her site tamamen izole çalışır — farklı siteler birbirinin verilerine erişemez (row-level tenant isolation).

---

## Mimari

```
SaaS/
├── apps/
│   ├── api/          # FastAPI backend (Python 3.13)
│   └── web/          # Next.js 16 frontend (TypeScript)
├── infra/            # Docker, nginx konfigürasyonları
├── data/             # Veri & analitik klasörü (Sprint 14+)
├── docs/             # Dokümantasyon
├── docker-compose.yml
└── start.sh          # Tek komutla başlat
```

**Tech Stack:**

| Katman | Teknoloji |
|---|---|
| Backend API | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Database | PostgreSQL 16 |
| Frontend | Next.js 16 App Router + TypeScript |
| Styling | Tailwind CSS |
| Auth | JWT (python-jose) + bcrypt |
| Testing | pytest + FastAPI TestClient (SQLite in-memory) |
| Proxy | Next.js rewrites → FastAPI (CORS-free) |

---

## Özellikler

### 🔐 Kimlik Doğrulama & Yetkilendirme
- Site kaydı + admin kullanıcı oluşturma (tek endpoint)
- JWT tabanlı oturum yönetimi
- Rol tabanlı erişim kontrolü: `admin` · `manager` · `accountant` · `resident`
- Multi-tenant row-level izolasyon (`X-Site-Id` header)

### 🏘️ Site & Bina Yönetimi
- Blok (bina) CRUD
- Daire (flat) CRUD — aktif/pasif durum, kat bilgisi
- Sakin-daire ilişkisi (birden fazla sakin, tarih aralıklı geçmiş)
- Sakin portalı (resident self-service)

### 💰 Finansal Modül
- **Aidat/Borç yönetimi** (charges): tip, dönem, tutar, vade
- **Ödeme planları** (charge plans): otomatik periyodik borç üretimi
- **Zamanlanmış borç oluşturma** (scheduled charges): kural motoru
- **Ödeme kaydı** (payments): çoklu borcu kapsayan ödeme
- **Ödeme dağıtımı** (payment allocations): bir ödemeyi birden fazla borca bölme
- **Taksit planı** (installment plans): büyük borçları aylık taksite yayma
- **Muhasebe defteri** (ledger): her daire için debit/credit hareketleri

### 📊 Analytics & Raporlama
- Dashboard KPI'ları: toplam tahsilat, bekleyen borç, tahsilat oranı
- Aylık trend grafiği
- Daire doluluk istatistikleri
- **Vadesi geçmiş borçlar** (kaç gün geciktiğiyle birlikte)
- **En borçlu daireler** (top debtors)
- Gelir/gider raporları

### 🔔 Bildirimler
- Sakinlere borç/ödeme bildirimleri
- Otomatik vadesi geçmiş borç tetikleyici

### 📥 Taksit Planı
- Büyük borcu N taksite böl (ilk vade + aylık artış)
- Taksit başına ödeme işaretleme
- Kuruş hassasiyetiyle kalan taksit hesaplama

---

## Kurulum

### Gereksinimler

- Python 3.13+
- Node.js 20+
- PostgreSQL 16+

### 1. Repo'yu klonla

```bash
git clone https://github.com/umuterenakbass/SaaS.git
cd SaaS
```

### 2. Python ortamını kur

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

### 3. Veritabanını oluştur

```bash
psql -U postgres -c "CREATE USER saas_user WITH PASSWORD 'change_me';"
psql -U postgres -c "CREATE DATABASE saas_db OWNER saas_user;"
```

### 4. Environment dosyasını ayarla

```bash
cp .env.example .env
# Aşağıdaki değerleri düzenle:
# DATABASE_URL=postgresql+psycopg://saas_user:change_me@localhost:5432/saas_db
# SECRET_KEY=supersecret-change-in-production
```

### 5. Migrasyonları çalıştır

```bash
cd apps/api
alembic upgrade head
```

### 6. Frontend bağımlılıklarını yükle

```bash
cd apps/web
npm install
```

---

## Çalıştırma

### Tek komutla (önerilen)

```bash
./start.sh
```

| Servis | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### Manuel başlatma

```bash
# Backend
cd apps/api
PYTHONPATH=$(pwd) uvicorn app.main:app --reload --port 8000

# Frontend (yeni terminal)
cd apps/web
npm run dev
```

> **Not:** Frontend `/api/*` isteklerini Next.js proxy üzerinden backend'e yönlendirir. Ayrıca CORS ayarı gerekmez.

---

## API Endpointleri

| Grup | Prefix | Açıklama |
|---|---|---|
| Auth | `/api/v1/auth` | Kayıt, giriş, token |
| Tenant | `/api/v1/tenant` | Site bilgileri |
| Blocks | `/api/v1/blocks` | Blok CRUD |
| Flats | `/api/v1/flats` | Daire CRUD |
| Charges | `/api/v1/charges` | Aidat/borç CRUD |
| Charge Plans | `/api/v1/charge-plans` | Periyodik plan CRUD |
| Scheduled Charges | `/api/v1/scheduled-charges` | Zamanlanmış borç kuralları |
| Payments | `/api/v1/payments` | Ödeme kayıtları |
| Payment Allocations | `/api/v1/payment-allocations` | Ödeme dağıtımı |
| Installments | `/api/v1/installments` | Taksit planı CRUD |
| Ledger | `/api/v1/ledger` | Muhasebe defteri |
| Notifications | `/api/v1/notifications` | Bildirimler |
| Analytics | `/api/v1/analytics` | KPI, trend, overdue, top-debtors |
| Reports | `/api/v1/reports` | Gelir/gider raporları |
| Resident Portal | `/api/v1/resident-portal` | Sakin self-service |
| Resident Relations | `/api/v1/resident-relations` | Sakin-daire ilişkileri |
| User Management | `/api/v1/users` | Kullanıcı CRUD |

Tüm endpoint'lerin interaktif dokümantasyonu: **http://localhost:8000/docs**

---

## Veritabanı Şeması

```
sites ──┬── users
        ├── blocks ── flats ──┬── charges ──── payment_allocations
        │                     │                       │
        │                     ├── payments ────────────┘
        │                     ├── ledger_entries
        │                     ├── installment_plans ── installment_items
        │                     ├── resident_flat_relations
        │                     └── notifications
        ├── charge_plans
        └── scheduled_charges
```

**Migrasyon geçmişi:**

| # | Tarih | İçerik |
|---|---|---|
| 0001 | 2026-05-04 | Auth & Tenant (sites, users) |
| 0002 | 2026-05-06 | Domain: blocks, flats, relations |
| 0003 | 2026-05-06 | Flat unique constraint (active only) |
| 0004 | 2026-05-07 | Billing core: charges, payments, ledger |
| 0005 | 2026-05-08 | Plans & payment allocations |
| 0006 | 2026-05-12 | Notifications |
| 0007 | 2026-05-12 | Scheduled charges |
| 0008 | 2026-05-13 | Installment plans & items |

---

## Testing

Testler **SQLite in-memory** veritabanı kullanır — PostgreSQL kurulumu gerekmez.

```bash
cd apps/api
pytest -v
```

```
68 passed ✅  (9.66s)
```

**Test kapsamı:**

| Dosya | Test Sayısı | Kapsam |
|---|---|---|
| test_auth.py | 4 | Kayıt, giriş, token, tenant izolasyon |
| test_blocks.py | 3 | CRUD, tenant guard |
| test_flats.py | 4 | CRUD, unique constraint |
| test_charges.py | 3 | CRUD, filtre, tenant guard |
| test_charge_plans.py | 3 | Plan CRUD, tenant guard |
| test_payments.py | 4 | Ödeme, fazla ödeme, tenant guard |
| test_payment_allocations.py | 3 | Dağıtım, bakiye kontrolü |
| test_installments.py | 5 | Plan oluştur, öde, sil, tenant izolasyon |
| test_ledger.py | 3 | Debit/credit, bakiye hesabı |
| test_notifications.py | 3 | Bildirim, okundu işareti |
| test_analytics.py | 5 | KPI, trend, occupancy, tenant guard |
| test_reports.py | 2 | Gelir/gider raporu |
| test_resident_portal.py | 3 | Sakin portal erişimi |
| test_resident_relations.py | 3 | İlişki CRUD |
| test_user_mgmt.py | 3 | Kullanıcı CRUD, yetki |
| test_bulk.py | 2 | Toplu borç oluşturma |
| test_scheduled_charges.py | 2 | Kural motoru |
| test_health.py | 1 | Health check |

---

## Sprint Geçmişi

| Sprint | Tarih | Özellikler |
|---|---|---|
| **1** | 2026-05-04 | Monorepo iskelet, Docker Compose, FastAPI/Next.js kurulumu, GitHub Actions CI |
| **2** | 2026-05-05 | Auth: site kaydı, JWT login, multi-tenant izolasyon |
| **3** | 2026-05-06 | Bloklar ve daireler CRUD |
| **4** | 2026-05-07 | Sakin-daire ilişkileri, resident portal |
| **5** | 2026-05-07 | Billing core: charges (aidat/borç), payments |
| **6** | 2026-05-08 | Ledger (muhasebe defteri), bakiye hesabı |
| **7** | 2026-05-08 | Ödeme planları (charge plans), periyodik borç üretimi |
| **8** | 2026-05-09 | Payment allocations (ödeme dağıtımı) |
| **9** | 2026-05-10 | Analytics dashboard (KPI kartları, aylık trend, doluluk) |
| **10** | 2026-05-12 | Bildirim sistemi, otomatik vadesi geçmiş tetikleyici |
| **11** | 2026-05-12 | Zamanlanmış borç kuralları, toplu borç oluşturma |
| **12** | 2026-05-12 | Raporlama (gelir/gider), kullanıcı yönetimi, frontend dashboard |
| **13** | 2026-05-13 | Taksit planı (CRUD + ödeme), dashboard overdue/top-debtors kartları |

---

## Klasör Yapısı

```
apps/api/
├── app/
│   ├── api/v1/
│   │   └── endpoints/      # Her domain için ayrı router (20 endpoint dosyası)
│   ├── core/               # Config, JWT, dependency injection
│   ├── db/                 # Session yönetimi, base model
│   ├── models/             # SQLAlchemy ORM modelleri (14 model)
│   └── schemas/            # Pydantic request/response şemaları
├── alembic/
│   └── versions/           # 8 migrasyon dosyası
├── tests/                  # 68 pytest testi
└── requirements.txt

apps/web/
├── src/
│   ├── app/
│   │   └── dashboard/      # 15 sayfa (her özellik için ayrı)
│   │       ├── page.tsx         # Ana dashboard (KPI + overdue + top-debtors)
│   │       ├── charges/         # Borç yönetimi
│   │       ├── payments/        # Ödeme kayıtları
│   │       ├── installments/    # Taksit planları
│   │       ├── analytics/       # Grafikler
│   │       ├── reports/         # Raporlar
│   │       └── ...
│   └── lib/
│       └── api.ts          # Tüm API çağrıları (typed interfaces)
└── next.config.ts          # Proxy: /api/* → localhost:8000
```

---

## Lisans

MIT © 2026
