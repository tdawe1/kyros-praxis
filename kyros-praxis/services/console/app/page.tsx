'use client'

import { Button, Notification } from '@carbon/react'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { api } from '../generated/api'
import { useWebSocket } from '../lib/ws'
import type { JobArray, ServiceArray } from '../generated/api'

export default function Home() {
  const { data: session, status } = useSession()

  const { data: jobsData, isLoading: jobsLoading, error: jobsError } = useQuery<JobArray>({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await api.getJobs()
      return response as JobArray
    },
  })

  const { data: servicesData, isLoading: servicesLoading, error: servicesError } = useQuery<ServiceArray>({
    queryKey: ['services'],
    queryFn: async () => {
      const response = await fetch('http://localhost:9000/services')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json() as ServiceArray
    },
  })

  const jobs: JobArray = jobsData || []
  const services: ServiceArray = servicesData || []

  if (status === 'loading' || jobsLoading || servicesLoading) {
    return <div>Loading...</div>
  }

  if (!session) {
    redirect('/auth/login')
  }

  if (jobsError || servicesError) {
    console.error('Error fetching data:', jobsError || servicesError)
  }

  const orchestratorWS = useWebSocket('ws://localhost:8000/ws')
  const registryWS = useWebSocket('ws://localhost:9000/ws')

  const sendTestMessage = () => {
    const testMessage = {
      type: 'test',
      payload: { message: 'Hello from client' }
    }
    orchestratorWS.sendMessage(testMessage)
    registryWS.sendMessage(testMessage)
  }

  return (
    <main className="p-4">
      <Notification
        kind="info"
        lowContrast
        title="Welcome to Kyros Console"
        subtitle="Dashboard for jobs, tasks, and collaboration."
      />
      <Button kind="primary">
        Create Job
      </Button>
      <div className="mb-4">
        <p>Jobs ({jobs.length}):</p>
        <ul>
          {jobs.map((job, index) => (
            <li key={index}>
              ID: {job.id}, Status: {job.status}, Created: {job.created_at}
            </li>
          ))}
        </ul>
        <p>Services ({services.length}):</p>
        <ul>
          {services.map((service, index) => (
            <li key={index}>
              ID: {service.id}, Name: {service.name}, Status: {service.status}
            </li>
          ))}
        </ul>
        <p>Orchestrator WS Connected: {orchestratorWS.isConnected.toString()}</p>
        <p>Service Registry WS Connected: {registryWS.isConnected.toString()}</p>
      </div>
    </main>
  )
}
