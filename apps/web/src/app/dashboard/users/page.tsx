"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  UserResponse,
  UserRole,
  createUser,
  deleteUser,
  listUsers,
  updateUser,
} from "@/lib/api";
import { getAccessToken, getSiteId } from "@/lib/auth-storage";

const ROLE_LABELS: Record<UserRole | string, string> = {
  admin: "Admin",
  manager: "Yönetici",
  accountant: "Muhasebeci",
  resident: "Sakin",
};

export default function UsersPage() {
  const router = useRouter();
  const token = getAccessToken();
  const siteId = getSiteId();

  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [createEmail, setCreateEmail] = useState("");
  const [createFullName, setCreateFullName] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [createRole, setCreateRole] = useState<UserRole>("manager");
  const [createError, setCreateError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // Edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editFullName, setEditFullName] = useState("");
  const [editRole, setEditRole] = useState<UserRole>("manager");
  const [editActive, setEditActive] = useState(true);
  const [editError, setEditError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!token || !siteId) {
      router.replace("/login");
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function load() {
    setLoading(true);
    try {
      const data = await listUsers(token!, siteId!);
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kullanıcılar yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token || !siteId) return;
    setCreating(true);
    setCreateError(null);
    try {
      const created = await createUser(token, siteId, {
        email: createEmail,
        full_name: createFullName,
        password: createPassword,
        role: createRole,
      });
      setUsers((prev) => [...prev, created]);
      setCreateEmail("");
      setCreateFullName("");
      setCreatePassword("");
      setCreateRole("manager");
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Kullanıcı oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  }

  function startEdit(user: UserResponse) {
    setEditingId(user.id);
    setEditFullName(user.full_name);
    setEditRole(user.role as UserRole);
    setEditActive(user.is_active);
    setEditError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditError(null);
  }

  async function handleSave(userId: string) {
    if (!token || !siteId) return;
    setSaving(true);
    setEditError(null);
    try {
      const updated = await updateUser(token, siteId, userId, {
        full_name: editFullName,
        role: editRole,
        is_active: editActive,
      });
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      setEditingId(null);
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Güncellenemedi.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(userId: string) {
    if (!confirm("Bu kullanıcıyı silmek istediğinizden emin misiniz?")) return;
    if (!token || !siteId) return;
    try {
      await deleteUser(token, siteId, userId);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Silinemedi.");
    }
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-10">
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        {/* Header */}
        <header className="flex items-center justify-between rounded-2xl bg-indigo-600 p-6 text-white shadow-sm">
          <div>
            <h1 className="text-2xl font-semibold">Kullanıcı Yönetimi</h1>
            <p className="mt-1 text-sm text-indigo-100">Site kullanıcılarını yönetin.</p>
          </div>
          <Link
            href="/dashboard"
            className="rounded-lg bg-white/20 px-4 py-2 text-sm font-medium text-white hover:bg-white/30"
          >
            ← Dashboard
          </Link>
        </header>

        {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-600">{error}</p>}

        {/* Create Form */}
        <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-base font-semibold text-zinc-800">Yeni Kullanıcı Ekle</h2>
          <form onSubmit={handleCreate} className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-zinc-600">Ad Soyad</label>
              <input
                type="text"
                required
                value={createFullName}
                onChange={(e) => setCreateFullName(e.target.value)}
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-zinc-600">E-posta</label>
              <input
                type="email"
                required
                value={createEmail}
                onChange={(e) => setCreateEmail(e.target.value)}
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-zinc-600">Şifre</label>
              <input
                type="password"
                required
                minLength={8}
                value={createPassword}
                onChange={(e) => setCreatePassword(e.target.value)}
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-zinc-600">Rol</label>
              <select
                value={createRole}
                onChange={(e) => setCreateRole(e.target.value as UserRole)}
                className="rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="manager">Yönetici</option>
                <option value="accountant">Muhasebeci</option>
                <option value="resident">Sakin</option>
              </select>
            </div>
            {createError && (
              <p className="col-span-full text-sm text-rose-600">{createError}</p>
            )}
            <div className="col-span-full">
              <button
                type="submit"
                disabled={creating}
                className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white disabled:opacity-60"
              >
                {creating ? "Ekleniyor…" : "Kullanıcı Ekle"}
              </button>
            </div>
          </form>
        </section>

        {/* User List */}
        <section className="rounded-xl border border-zinc-200 bg-white shadow-sm">
          <h2 className="border-b border-zinc-100 px-6 py-4 text-base font-semibold text-zinc-800">
            Kullanıcılar
          </h2>
          {loading ? (
            <p className="px-6 py-8 text-sm text-zinc-500">Yükleniyor…</p>
          ) : users.length === 0 ? (
            <p className="px-6 py-8 text-sm text-zinc-500">Henüz kullanıcı yok.</p>
          ) : (
            <ul className="divide-y divide-zinc-100">
              {users.map((user) =>
                editingId === user.id ? (
                  /* Edit Row */
                  <li key={user.id} className="flex flex-col gap-3 px-6 py-4 bg-indigo-50">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="flex flex-col gap-1">
                        <label className="text-xs font-medium text-zinc-600">Ad Soyad</label>
                        <input
                          type="text"
                          value={editFullName}
                          onChange={(e) => setEditFullName(e.target.value)}
                          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-xs font-medium text-zinc-600">Rol</label>
                        <select
                          value={editRole}
                          onChange={(e) => setEditRole(e.target.value as UserRole)}
                          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                          <option value="manager">Yönetici</option>
                          <option value="accountant">Muhasebeci</option>
                          <option value="resident">Sakin</option>
                        </select>
                      </div>
                      <div className="flex items-end gap-2">
                        <label className="flex items-center gap-2 text-sm text-zinc-700">
                          <input
                            type="checkbox"
                            checked={editActive}
                            onChange={(e) => setEditActive(e.target.checked)}
                            className="h-4 w-4 rounded border-zinc-300 accent-indigo-600"
                          />
                          Aktif
                        </label>
                      </div>
                    </div>
                    {editError && <p className="text-sm text-rose-600">{editError}</p>}
                    <div className="flex gap-2">
                      <button
                        onClick={() => void handleSave(user.id)}
                        disabled={saving}
                        className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-60"
                      >
                        {saving ? "Kaydediliyor…" : "Kaydet"}
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="rounded-lg border border-zinc-300 bg-white px-4 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
                      >
                        İptal
                      </button>
                    </div>
                  </li>
                ) : (
                  /* Display Row */
                  <li key={user.id} className="flex items-center justify-between gap-4 px-6 py-4">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-zinc-900">{user.full_name}</p>
                      <p className="truncate text-sm text-zinc-500">{user.email}</p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          user.is_active
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-zinc-100 text-zinc-500"
                        }`}
                      >
                        {user.is_active ? "Aktif" : "Pasif"}
                      </span>
                      <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
                        {ROLE_LABELS[user.role] ?? user.role}
                      </span>
                      <button
                        onClick={() => startEdit(user)}
                        className="rounded-lg border border-zinc-300 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
                      >
                        Düzenle
                      </button>
                      <button
                        onClick={() => void handleDelete(user.id)}
                        className="rounded-lg border border-rose-200 px-3 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50"
                      >
                        Sil
                      </button>
                    </div>
                  </li>
                ),
              )}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
