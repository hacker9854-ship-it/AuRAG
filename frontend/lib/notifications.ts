export interface PredictiveNotification {
  id: string;
  type: "predictive_warning";
  title: string;
  description: string;
  severity: "high";
  equipment: string;
  failure_event_id: string;
  similarity: number;
  status: "unread" | "read";
  detected_at: string;
  action_href: string;
}

export function mergeNotifications(
  current: PredictiveNotification[],
  incoming: PredictiveNotification[],
): PredictiveNotification[] {
  const byId = new Map(current.map((item) => [item.id, item]));
  for (const item of incoming) byId.set(item.id, item);
  return [...byId.values()]
    .sort((left, right) => right.detected_at.localeCompare(left.detected_at))
    .slice(0, 100);
}

