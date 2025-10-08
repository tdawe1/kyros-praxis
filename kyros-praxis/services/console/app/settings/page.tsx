'use client';

import { useQuery } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { Button, Heading } from "@carbon/react";

export default function SettingsPage() {
  const { data: session } = useSession();
  const token = (session as any)?.accessToken; // Use type assertion for NextAuth extended session

  const { data, isLoading, error } = useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const res = await fetch("http://localhost:8000/settings", {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });
      if (!res.ok) throw new Error("Failed to fetch settings");
      return res.json();
    },
    enabled: !!token, // Only run query when we have a token
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
