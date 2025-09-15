import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Check if the application is running
    return NextResponse.json({
      status: 'healthy',
      service: 'console',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '0.1.0'
    })
  } catch (error) {
    return NextResponse.json(
      { 
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}