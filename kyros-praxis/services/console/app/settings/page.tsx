"use client";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth";
import { Button, Heading } from "@carbon/react";

export default function SettingsPage() {
  const { token } = useAuth();

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  const { data, isLoading, error } = useQuery<any, Error>({
    queryKey: ["settings", token],
    enabled: !!token,
    queryFn: async () => {
      const res = await fetch(`${apiBase}/settings`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Failed to fetch settings (${res.status})`);
      return res.json();
    },
  });

  if (isLoading) return <div data-testid="loading">Loading settings...</div>;
  if (error) return (
    <div data-testid="error">Error: {error instanceof Error ? error.message : String(error)}</div>
  );

  return (
    <div data-testid="settings-page">
      <Heading>Settings</Heading>
      <div
        data-testid="settings-card"
        style={{ padding: "1rem", border: "1px solid #ccc" }}
      >
        <p data-testid="settings-content">
          Settings content: {JSON.stringify(data || {})}
        </p>
        <Button data-testid="save-settings">Save Settings</Button>
      </div>
    </div>
  );
}
