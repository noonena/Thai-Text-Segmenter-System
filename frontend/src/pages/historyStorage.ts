export type HistoryItem = {
  id: string;
  filename: string;
  createdAt: string;
  segments: number;
  output: string;
};

const STORAGE_KEY = "thai-text-history";

export const getHistory = (): HistoryItem[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

export const saveToHistory = (item: Omit<HistoryItem, "id" | "createdAt">) => {
  const history = getHistory();
  const newItem: HistoryItem = {
    ...item,
    id: Date.now().toString(),
    createdAt: new Date().toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).replace(/,/g, ""),
  };

  history.unshift(newItem);
  if (history.length > 50) history.pop();

  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  return newItem;
};

export const removeFromHistory = (id: string) => {
  const history = getHistory();
  const filtered = history.filter((item) => item.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
};
