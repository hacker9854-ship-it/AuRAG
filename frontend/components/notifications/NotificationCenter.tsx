"use client";

import Link from "next/link";
import { BellIcon, CircleIcon, RadioIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useLiveEvents } from "@/hooks/use-live-events";

const connectionVariant = {
  connecting: "warning",
  live: "success",
  reconnecting: "warning",
  offline: "destructive",
} as const;

export default function NotificationCenter() {
  const { notifications, unreadCount, connectionStatus, markRead } = useLiveEvents();

  return (
    <Sheet>
      <SheetTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className="relative"
            aria-label={`${unreadCount} unread predictive notifications`}
          />
        }
      >
        <BellIcon />
        {unreadCount ? (
          <Badge variant="destructive" className="absolute -top-1 -right-1 min-w-5 px-1">
            {unreadCount > 9 ? "9+" : unreadCount}
          </Badge>
        ) : null}
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader className="border-b">
          <div className="flex items-center justify-between gap-3 pr-10">
            <SheetTitle>Predictive notifications</SheetTitle>
            <Badge variant={connectionVariant[connectionStatus]}>
              <RadioIcon data-icon="inline-start" />
              {connectionStatus}
            </Badge>
          </div>
          <SheetDescription>
            Durable warnings from the autonomous telemetry worker.
          </SheetDescription>
        </SheetHeader>
        <ScrollArea className="min-h-0 flex-1">
          <div className="flex flex-col gap-3 p-4">
            {notifications.length ? (
              notifications.map((item) => (
                <article key={item.id} className="rounded-lg border p-4">
                  <div className="flex items-start gap-3">
                    <CircleIcon
                      className={item.status === "unread" ? "mt-1 fill-destructive text-destructive" : "mt-1 text-muted"}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-medium">{item.title}</h3>
                        <Badge variant="destructive">{Math.round(item.similarity * 100)}% match</Badge>
                      </div>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.description}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          nativeButton={false}
                          render={<Link href={item.action_href} />}
                          onClick={() => void markRead(item.id)}
                        >
                          Open warning
                        </Button>
                        {item.status === "unread" ? (
                          <Button size="sm" variant="ghost" onClick={() => void markRead(item.id)}>
                            Mark read
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <div className="py-16 text-center">
                <BellIcon className="mx-auto text-muted-foreground" />
                <div className="mt-3 font-medium">No predictive warnings</div>
                <p className="mt-1 text-sm text-muted-foreground">
                  New autonomous alerts will appear here.
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
