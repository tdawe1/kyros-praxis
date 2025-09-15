'use client';

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth";
import { Button, Heading } from "@carbon/react";

export default function SettingsPage() {
  const { token } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const res = await fetch("http://localhost:8000/settings", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error("Failed to fetch settings");
      return res.json();
    },
  });

  if (isLoading) return <div data-testid="loading">Loading settings...</div>;
  if (error) return <div data-testid="error">Error: {error.message}</div>;

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
