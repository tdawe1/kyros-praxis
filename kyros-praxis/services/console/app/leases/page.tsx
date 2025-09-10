'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@carbon/react';
import { Button } from '@carbon/react';

interface Lease {
  id: string;
  resource: string;
  ttl_seconds: number;
}

export default function LeasesPage() {
  const queryClient = useQueryClient();
  const [selectedLeaseId, setSelectedLeaseId] = useState<string | null>(null);
  const [leases, setLeases] = useState<Lease[]>([]);
  const [connected, setConnected] = useState(false);

  // Fetch initial leases
  const { data, isLoading, error } = useQuery({
    queryKey: ['leases'],
    queryFn: async () => {
      const response = await fetch('/api/leases');
      if (!response.ok) {
        throw new Error('Failed to fetch leases');
      }
      const fetchedLeases: Lease[] = await response.json();
      setLeases(fetchedLeases);
      return fetchedLeases;
    },
  });

  // Real-time TTL updates via EventSource (SSE)
  useEffect(() => {
    const eventSource = new EventSource('/api/leases/tail');
    eventSource.onopen = () => setConnected(true);
    eventSource.onerror = () => setConnected(false);
    eventSource.onmessage = (event) => {
      try {
        const eventData = JSON.parse(event.data);
        if (eventData.type === 'ttl_update' && eventData.id) {
          setLeases((prev) =>
            prev.map((lease) =>
              lease.id === eventData.id
                ? { ...lease, ttl_seconds: eventData.ttl_seconds }
                : lease
            )
          );
        }
      } catch (err) {
        console.error('Error parsing SSE message:', err);
      }
    };

    return () => {
      eventSource.close();
      setConnected(false);
    };
  }, []);

  // Mutation for reclaiming a lease
  const reclaimMutation = useMutation({
    mutationFn: async (leaseId: string) => {
      const response = await fetch(`/api/leases/${leaseId}/reclaim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        throw new Error('Failed to reclaim lease');
      }
      return response.json();
    },
    onSuccess: () => {
      toast.success('Lease reclaimed successfully');
      queryClient.invalidateQueries({ queryKey: ['leases'] });
      setSelectedLeaseId(null);
    },
    onError: (err: Error) => {
      toast.error(`Failed to reclaim lease: ${err.message}`);
    },
  });

  if (isLoading) return <div>Loading leases...</div>;
  if (error) return <div>Error loading leases: {error.message}</div>;

  const handleReclaim = (leaseId: string) => {
    if (confirm(`Reclaim lease ${leaseId}?`)) {
      reclaimMutation.mutate(leaseId);
    }
  };

  const getCountdown = (ttl: number) => {
    const minutes = Math.floor(ttl / 60);
    const seconds = ttl % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div>
      <h1>Leases</h1>
      <p>Connection Status: {connected ? 'Connected' : 'Disconnected'}</p>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>ID</TableHeader>
              <TableHeader>Resource</TableHeader>
              <TableHeader>TTL Countdown</TableHeader>
              <TableHeader>Actions</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {leases.map((lease) => (
              <TableRow key={lease.id}>
                <TableCell>{lease.id}</TableCell>
                <TableCell>{lease.resource}</TableCell>
                <TableCell>{getCountdown(lease.ttl_seconds)}</TableCell>
                <TableCell>
                  <Button
                    onClick={() => handleReclaim(lease.id)}
                    disabled={reclaimMutation.isPending}
                    size="sm"
                  >
                    Reclaim
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}