'use client'

import { Button, TextInput } from '@carbon/react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useWebSocket } from '@/lib/ws'

export default function Home() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const { status: wsStatus } = useWebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws')

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/login')
    }
  }, [status, router])

  if (status === 'loading') {
    return <div>Loading...</div>
  }

  if (!session) {
    return null
  }

  return (
    <main className="p-4">
      <h1 className="text-2xl font-bold mb-4">Welcome to Kyros Console</h1>
      <p className="mb-4">Dashboard for jobs and tasks.</p>
      <p>Session: {session.user?.email}</p>
      <p>WS Connected: {wsStatus.connected.toString()}</p>
      <button onClick={() => router.push('/jobs')}>Go to Jobs</button>
    </main>
  )
}