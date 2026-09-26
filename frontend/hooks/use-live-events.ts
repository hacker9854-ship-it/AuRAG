"use client";

import { useEffect, useMemo, useState } from "react";

import {
  getNotifications,
  markNotificationRead as persistRead,
  predictiveEventsUrl,
} from "@/lib/api";
import {
  mergeNotifications,
  type PredictiveNotification,
} from "@/lib/notifications";

export type LiveConnectionStatus = "connecting" | "live" | "reconnecting" | "offline";

export function useLiveEvents() {
  const [notifications, setNotifications] = useState<PredictiveNotification[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<LiveConnectionStatus>("connecting");

  useEffect(() => {
    let active = true;
    let source: EventSource | null = null;

    getNotifications()
      .then((items) => {
        if (active) setNotifications((current) => mergeNotifications(current, items));
      })
      .catch(() => {
        if (active) setConnectionStatus("offline");
      });

    if (typeof EventSource !== "undefined") {
      source = new EventSource(predictiveEventsUrl());
      source.onopen = () => {
        if (active) setConnectionStatus("live");
      };
      source.addEventListener("predictive_warning", (event) => {
        try {
          const item = JSON.parse((event as MessageEvent).data) as PredictiveNotification;
          if (active) setNotifications((current) => mergeNotifications(current, [item]));
        } catch {
          // Ignore malformed event payloads; the next durable history fetch repairs state.
        }
      });
      source.addEventListener("stream_error", () => {
        if (active) setConnectionStatus("offline");
      });
      source.onerror = () => {
        if (active) setConnectionStatus("reconnecting");
      };
    } else {
      queueMicrotask(() => {
        if (active) setConnectionStatus("offline");
      });
    }

    return () => {
      active = false;
      source?.close();
    };
  }, []);

  const unreadCount = useMemo(
    () => notifications.filter((item) => item.status === "unread").length,
    [notifications],
  );

  async function markRead(eventId: string) {
    await persistRead(eventId);
    setNotifications((current) =>
      current.map((item) => (item.id === eventId ? { ...item, status: "read" } : item)),
    );
  }

  return { notifications, unreadCount, connectionStatus, markRead };
}
