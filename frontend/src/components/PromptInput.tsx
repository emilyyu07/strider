import { useState } from 'react'

interface PromptInputProps {
  onSubmit: (prompt: string) => void
  loading: boolean
  disabled: boolean
}

const SAMPLE_PROMPTS = [
  '5km loop, quiet streets, some elevation',
  'Easy 3km recovery run, shaded routes',
  '8km steady run on calm roads',
]

export default function PromptInput({ onSubmit, loading, disabled }: PromptInputProps) {
  const [prompt, setPrompt] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim() && !disabled) {
      onSubmit(prompt.trim())
    }
  }

  return (
    <div>
      <h3>Describe your run</h3>
      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
          placeholder="e.g. 5km loop, quiet streets, some elevation"
          disabled={loading}
        />
        <button type="submit" disabled={disabled || loading || !prompt.trim()}>
          {loading ? 'Generating…' : 'Generate route'}
        </button>
      </form>

      <p>Samples:</p>
      <ul>
        {SAMPLE_PROMPTS.map((sample) => (
          <li key={sample}>
            <button
              type="button"
              onClick={() => setPrompt(sample)}
              disabled={loading}
              className="sample-button"
            >
              {sample}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
