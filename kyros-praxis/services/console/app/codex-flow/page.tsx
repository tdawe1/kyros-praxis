import { codexFlow } from '@bear_ai/codex-flow'
import { getUsageLimits, validateUsageLimits } from '@bear_ai/codex-flow/src/config/usage-limits'

export const dynamic = 'force-dynamic'

export default async function CodexFlowDemo() {
  const limits = getUsageLimits()
  const warnings = validateUsageLimits(limits)

  let configStatus: { valid: boolean; errors: string[] } = { valid: false, errors: [] }
  try {
    // This checks whether a Codex-Flow config exists and is readable
    configStatus = await codexFlow.validateConfiguration()
  } catch (err: any) {
    configStatus = { valid: false, errors: [err?.message || 'Unknown error'] }
  }

  return (
    <main className="p-6 space-y-6">
      <section>
        <h1 className="text-2xl font-bold">Codex-Flow Integration</h1>
        <p className="text-gray-600">Minimal server-side usage wired into Next.js.</p>
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Status</h2>
        <ul className="list-disc pl-6 text-sm">
          <li>Package: <code>@bear_ai/codex-flow</code> detected</li>
          <li>Config present: {configStatus.valid ? 'yes' : 'no'}</li>
          {!configStatus.valid && configStatus.errors.length > 0 && (
            <li className="text-red-600">{configStatus.errors[0]}</li>
          )}
        </ul>
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Usage Limits</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="p-3 rounded border">
            <div className="font-medium">Model</div>
            <div className="text-gray-700">{limits.MODEL}</div>
          </div>
          <div className="p-3 rounded border">
            <div className="font-medium">Max Steps / Task</div>
            <div className="text-gray-700">{limits.MAX_STEPS_PER_TASK}</div>
          </div>
          <div className="p-3 rounded border">
            <div className="font-medium">Concurrency</div>
            <div className="text-gray-700">{limits.MAX_CONCURRENT_REQUESTS}</div>
          </div>
          <div className="p-3 rounded border">
            <div className="font-medium">Prompt Tokens</div>
            <div className="text-gray-700">{limits.MAX_PROMPT_TOKENS}</div>
          </div>
          <div className="p-3 rounded border">
            <div className="font-medium">Response Tokens</div>
            <div className="text-gray-700">{limits.MAX_RESPONSE_TOKENS}</div>
          </div>
          <div className="p-3 rounded border">
            <div className="font-medium">Daily Cap (USD)</div>
            <div className="text-gray-700">{limits.DAILY_SPENDING_CAP_USD.toFixed(2)}</div>
          </div>
        </div>
        {warnings.length > 0 && (
          <div className="mt-2 text-amber-700 text-sm">Warnings: {warnings.join('; ')}</div>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Next Steps</h2>
        <ul className="list-disc pl-6 text-sm">
          <li>
            To initialize configuration locally, run: <code>npx codex-flow init</code>
          </li>
          <li>
            To use OpenAI, set <code>OPENAI_API_KEY</code> in <code>.env.local</code> and restart dev server.
          </li>
          <li>
            For local models, configure provider <code>local</code> pointing to <code>http://localhost:11434</code> (Ollama).
          </li>
        </ul>
      </section>
    </main>
  )
}

