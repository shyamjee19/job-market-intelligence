import { useCallback, useEffect, useState } from "react";
import { fetchSavedJobs, saveJob, unsaveJob } from "../api/userClient";
import { useAuth } from "../context/AuthContext";

export function useSavedJobs() {
  const { user } = useAuth();
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!user) {
      setSavedIds(new Set());
      return;
    }
    fetchSavedJobs()
      .then((jobs) => setSavedIds(new Set(jobs.map((j) => j.id))))
      .catch(() => {});
  }, [user]);

  const toggle = useCallback(
    async (jobId: number) => {
      const wasSaved = savedIds.has(jobId);
      setSavedIds((prev) => {
        const next = new Set(prev);
        if (wasSaved) next.delete(jobId);
        else next.add(jobId);
        return next;
      });
      try {
        if (wasSaved) await unsaveJob(jobId);
        else await saveJob(jobId);
      } catch {
        setSavedIds((prev) => {
          const next = new Set(prev);
          if (wasSaved) next.add(jobId);
          else next.delete(jobId);
          return next;
        });
      }
    },
    [savedIds],
  );

  return { isSaved: (id: number) => savedIds.has(id), toggle, isAuthed: !!user };
}
