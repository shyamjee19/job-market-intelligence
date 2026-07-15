import { AlertTriangle, Bell, FileUp, Plus, Trash2, User as UserIcon } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { fetchCurrentUserProfile } from "../api/authClient";
import { createAlert, deleteAlert, fetchAlerts, toggleAlert, updateProfile, uploadResume } from "../api/userClient";
import { PageTransition } from "../components/PageTransition";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";
import { formatDate } from "../lib/format";
import type { JobAlert, JobAlertCreate, Profile } from "../types";

const inputStyle = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  color: "var(--text-primary)",
};

function ProfileForm() {
  const [profile, setProfile] = useState<Profile>({
    headline: "",
    bio: "",
    location: "",
    skills: [],
    experience_years: null,
    resume_filename: null,
    resume_uploaded_at: null,
  });
  const [skillsInput, setSkillsInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchCurrentUserProfile()
      .then((p) => {
        setProfile(p);
        setSkillsInput(p.skills.join(", "));
      })
      .catch(() => {});
  }, []);

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    setSaved(false);
    try {
      const updated = await updateProfile({
        headline: profile.headline || null,
        bio: profile.bio || null,
        location: profile.location || null,
        skills: skillsInput
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        experience_years: profile.experience_years,
      });
      setProfile(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  async function handleResumeChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const result = await uploadResume(file);
      setProfile((p) => ({ ...p, resume_filename: result.resume_filename, resume_uploaded_at: result.resume_uploaded_at }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload resume");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <Card className="p-6">
      <h2 className="flex items-center gap-2 text-sm font-semibold mb-4" style={{ color: "var(--text-secondary)" }}>
        <UserIcon size={15} />
        Profile
      </h2>

      <form onSubmit={handleSave} className="flex flex-col gap-3">
        <input
          placeholder="Headline (e.g. Senior Backend Engineer)"
          value={profile.headline ?? ""}
          onChange={(e) => setProfile((p) => ({ ...p, headline: e.target.value }))}
          className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
          style={inputStyle}
        />
        <textarea
          placeholder="Short bio"
          value={profile.bio ?? ""}
          onChange={(e) => setProfile((p) => ({ ...p, bio: e.target.value }))}
          rows={3}
          className="rounded-lg px-3.5 py-2.5 text-sm outline-none resize-none"
          style={inputStyle}
        />
        <div className="flex gap-3">
          <input
            placeholder="Location"
            value={profile.location ?? ""}
            onChange={(e) => setProfile((p) => ({ ...p, location: e.target.value }))}
            className="flex-1 rounded-lg px-3.5 py-2.5 text-sm outline-none"
            style={inputStyle}
          />
          <input
            type="number"
            min={0}
            placeholder="Years experience"
            value={profile.experience_years ?? ""}
            onChange={(e) =>
              setProfile((p) => ({ ...p, experience_years: e.target.value ? Number(e.target.value) : null }))
            }
            className="w-40 rounded-lg px-3.5 py-2.5 text-sm outline-none"
            style={inputStyle}
          />
        </div>
        <input
          placeholder="Skills, comma separated (e.g. Python, React, AWS)"
          value={skillsInput}
          onChange={(e) => setSkillsInput(e.target.value)}
          className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
          style={inputStyle}
        />

        {error && (
          <div className="flex items-center gap-2 text-sm" style={{ color: "var(--status-critical)" }}>
            <AlertTriangle size={14} />
            {error}
          </div>
        )}

        <div className="flex items-center gap-3 mt-1">
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? "Saving…" : "Save profile"}
          </Button>
          {saved && (
            <span className="text-xs" style={{ color: "var(--status-good)" }}>
              Saved
            </span>
          )}
        </div>
      </form>

      <div className="mt-5 pt-5 flex items-center justify-between" style={{ borderTop: "1px solid var(--border)" }}>
        <div>
          <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
            Resume
          </div>
          <div className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
            {profile.resume_filename
              ? `${profile.resume_filename} · uploaded ${formatDate(profile.resume_uploaded_at)}`
              : "No resume uploaded yet. PDF, DOC or DOCX."}
          </div>
        </div>
        <label>
          <input ref={fileRef} type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={handleResumeChange} />
          <Button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
          >
            <FileUp size={14} />
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </label>
      </div>
    </Card>
  );
}

function AlertsPanel() {
  const [alerts, setAlerts] = useState<JobAlert[] | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<JobAlertCreate>({ name: "", frequency: "daily" });

  useEffect(() => {
    fetchAlerts()
      .then(setAlerts)
      .catch((err) => setError(err.message ?? "Failed to load alerts"));
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await createAlert(form);
      setAlerts((prev) => [created, ...(prev ?? [])]);
      setForm({ name: "", frequency: "daily" });
      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create alert");
    }
  }

  async function handleToggle(alert: JobAlert) {
    setAlerts((prev) => prev?.map((a) => (a.alert_id === alert.alert_id ? { ...a, is_active: !a.is_active } : a)) ?? null);
    await toggleAlert(alert.alert_id, !alert.is_active).catch(() => {});
  }

  async function handleDelete(alertId: number) {
    setAlerts((prev) => prev?.filter((a) => a.alert_id !== alertId) ?? null);
    await deleteAlert(alertId).catch(() => {});
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
          <Bell size={15} />
          Job alerts
        </h2>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus size={14} />
          New alert
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm mb-3" style={{ color: "var(--status-critical)" }}>
          <AlertTriangle size={14} />
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleCreate} className="flex flex-col gap-2 mb-4 p-3 rounded-lg" style={{ background: "var(--surface-2)" }}>
          <input
            required
            placeholder="Alert name"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            className="rounded-lg px-3 py-2 text-sm outline-none"
            style={inputStyle}
          />
          <div className="flex gap-2 flex-wrap">
            <input
              placeholder="Keywords"
              value={form.keywords ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, keywords: e.target.value }))}
              className="flex-1 min-w-[140px] rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
            <input
              placeholder="Location"
              value={form.location ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
              className="flex-1 min-w-[120px] rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
            <select
              value={form.frequency}
              onChange={(e) => setForm((f) => ({ ...f, frequency: e.target.value as JobAlertCreate["frequency"] }))}
              className="rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            >
              <option value="instant">Instant</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>
          <div>
            <Button type="submit" size="sm" variant="primary">
              Create alert
            </Button>
          </div>
        </form>
      )}

      {alerts === null ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Loading…
        </p>
      ) : alerts.length === 0 ? (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No alerts yet. Create one to get notified about new matching jobs.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {alerts.map((a) => (
            <div
              key={a.alert_id}
              className="flex items-center justify-between gap-3 p-3 rounded-lg"
              style={{ background: "var(--surface-2)" }}
            >
              <div className="min-w-0">
                <div className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                  {a.name}
                </div>
                <div className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
                  {[a.keywords, a.location, a.tag, a.frequency].filter(Boolean).join(" · ")}
                  {a.last_checked_at && ` · last checked ${formatDate(a.last_checked_at)}`}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleToggle(a)}
                  className="text-xs font-medium rounded-full px-2.5 py-1"
                  style={{
                    background: a.is_active
                      ? "color-mix(in srgb, var(--status-good) 14%, var(--surface-1))"
                      : "var(--surface-1)",
                    color: a.is_active ? "var(--status-good)" : "var(--text-muted)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {a.is_active ? "Active" : "Paused"}
                </button>
                <button
                  onClick={() => handleDelete(a.alert_id)}
                  className="p-1.5 rounded-md hover:bg-black/5 dark:hover:bg-white/10"
                  style={{ color: "var(--status-critical)" }}
                  aria-label="Delete alert"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export function ProfilePage() {
  const { user } = useAuth();

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          {user?.full_name || user?.email}
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          {user?.email}
        </p>

        <div className="flex flex-col gap-6">
          <ProfileForm />
          <AlertsPanel />
        </div>
      </div>
    </PageTransition>
  );
}
