'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { Button } from '@carbon/react';
import { NotificationFilled } from '@carbon/icons-react';

interface Event {
  id: string;
  message: string;
  timestamp: string;
}

const fetchEvents = async (): Promise<Event[]> => {
  const response = await fetch('/api/events');
  if (!response.ok) {
    throw new Error('Failed to fetch events');
  }
  return response.json();
};

const postHumanLog = async (data: { message: string }) => {
  const response = await fetch('/api/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to post human log');
  }
  return response.json();
};

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['events'],
    queryFn: fetchEvents,
  });

  const mutation = useMutation({
    mutationFn: postHumanLog,
    onSuccess: () => {
      toast.success('Human log entry added successfully');
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
    onError: (err) => {
      toast.error(`Failed to add human log: ${err.message}`);
    },
  });

  useEffect(() => {
    if (data) {
      setEvents(data);
    }
  }, [data]);

  useEffect(() => {
    const eventSource = new EventSource('/api/events/tail');
    eventSource.onmessage = (event) => {
      try {
        const newEvent: Event = JSON.parse(event.data);
        setEvents((prev) => [newEvent, ...prev]);
      } catch (err) {
        console.error('Failed to parse event message:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const handleGenerateLog = () => {
    mutation.mutate({ message: 'Human log entry' });
  };

  if (isLoading) return <div>Loading events...</div>;
  if (error) return <div>Error loading events: {error.message}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Events</h1>
      <p>SSE Connection Active</p>
      <Button
        onClick={handleGenerateLog}
        disabled={mutation.isPending}
        renderIcon={NotificationFilled}
      >
        Generate Human Log
      </Button>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            <strong>{event.timestamp}</strong>: {event.message}
          </li>
        ))}
      </ul>
    </div>
  );
}