'use client'

import { Button, TextInput } from '@carbon/react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useWebSocket } from '@/lib/ws'
import { useAuditLogging } from './hooks/useAuditLogging'
import { AuditWrapper } from './lib/components/AuditWrapper'

export default function Home() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
  const { status: wsStatus } = useWebSocket(wsUrl, (session as any)?.accessToken)
  
  // Add audit logging
  const { logAction, logDataOperation } = useAuditLogging({
    component: 'home-page',
    trackPageViews: true,
    trackButtonClicks: true,
  })

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/login')
    }
  }, [status, router])

  // Log navigation actions
  const handleNavigateToAgents = async () => {
    await logAction('navigate_to_agents', { destination: '/agents' })
    router.push('/agents')
  }

  const handleNavigateToTasks = async () => {
    await logAction('navigate_to_tasks', { destination: '/tasks' })  
    router.push('/tasks')
  }

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
      
      {/* Audit-wrapped navigation buttons */}
      <div className="space-y-2 mt-4">
        <AuditWrapper component="home-navigation">
          <button 
            onClick={() => router.push('/jobs')}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-2"
          >
            Go to Jobs
          </button>
        </AuditWrapper>
        
        <AuditWrapper component="home-navigation">
          <button 
            onClick={handleNavigateToAgents}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mr-2"
          >
            Go to Agents
          </button>
        </AuditWrapper>
        
        <AuditWrapper component="home-navigation">
          <button 
            onClick={handleNavigateToTasks}
            className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
          >
            Go to Tasks
          </button>
        </AuditWrapper>
      </div>
    </main>
  )
}
