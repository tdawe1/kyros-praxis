# ARCHITECTURE

## Collab API  {#collab-api}
DocID: collab-api-v1
Spec for /collab/state, ETag If-Match updates with atomic writes, and SSE tail.

## Leases  {#leases}
DocID: leases-spec-v1
Lease schema with ttl_seconds and heartbeat_at, reclaim rules, and events.

## Events  {#events}
DocID: events-protocol-v1
Append-only JSONL events with ts and actor; human log rules.

## Jobs  {#jobs}
DocID: jobs-slice-v1
Auth → create job → stub variant → accept → export.
