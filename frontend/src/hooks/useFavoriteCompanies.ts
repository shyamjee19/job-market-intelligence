import { useCallback, useEffect, useState } from "react";
import { favoriteCompany, fetchFavoriteCompanies, unfavoriteCompany } from "../api/userClient";
import { useAuth } from "../context/AuthContext";

export function useFavoriteCompanies() {
  const { user } = useAuth();
  const [names, setNames] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!user) {
      setNames(new Set());
      return;
    }
    fetchFavoriteCompanies()
      .then((favs) => setNames(new Set(favs.map((f) => f.company_name))))
      .catch(() => {});
  }, [user]);

  const toggle = useCallback(
    async (companyName: string) => {
      const wasFav = names.has(companyName);
      setNames((prev) => {
        const next = new Set(prev);
        if (wasFav) next.delete(companyName);
        else next.add(companyName);
        return next;
      });
      try {
        if (wasFav) await unfavoriteCompany(companyName);
        else await favoriteCompany(companyName);
      } catch {
        setNames((prev) => {
          const next = new Set(prev);
          if (wasFav) next.add(companyName);
          else next.delete(companyName);
          return next;
        });
      }
    },
    [names],
  );

  return { isFavorite: (name: string) => names.has(name), toggle, isAuthed: !!user };
}
