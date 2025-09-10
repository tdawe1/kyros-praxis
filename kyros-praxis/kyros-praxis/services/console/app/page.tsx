'use client'

import { Button, TextInput } from '@carbon/react'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import { useWebSocket } from '../src/lib/ws'

export default function Home() {
  const { data: session, status } = useSession()

  if (status === 'loading') {
    return <div>Loading...</div>
  }

  if (!session) {
    return <div>Please log in to continue.</div>
  }

  const orchestratorWS = useWebSocket('ws://localhost:8000/ws')
  const registryWS = useWebSocket('ws://localhost:9000/ws')

  const sendTestMessage = () => {
    const testMessage = {
      type: 'test',
      payload: { message: 'Hello from client' }
    }
    if (orchestratorWS.sendMessage) {
      orchestratorWS.sendMessage(testMessage)
    }
    if (registryWS.sendMessage) {
      registryWS.sendMessage(testMessage)
    }
  }

  return (
    <main className="p-4">
      <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h1 className="text-xl font-semibold text-blue-900">Welcome to Kyros Console</h1>
        <p className="text-blue-800">Dashboard for jobs, tasks, and collaboration.</p>
      </div>
      <div className="mb-4">
        <p>Orchestrator WS Connected: {orchestratorWS.isConnected.toString()}</p>
        <p>Service Registry WS Connected: {registryWS.isConnected.toString()}</p>
      </div>
      <Button kind="primary" onClick={sendTestMessage}>
        Send Test WS Message
      </Button>
      <Button kind="primary">
        Create Job
      </Button>
    </main>
  )
}