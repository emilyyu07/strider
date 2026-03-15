const TERRAIN_TAGS = ['QUIET', 'SHADED', 'HILLY', 'FLAT', 'LOW TRAFFIC', 'PARK', 'WATERFRONT', 'SCENIC']
const DISTANCE_TICKS = [1000, 3000, 5000, 10000, 15000]
const PACE_TICKS = ['EASY', 'STEADY', 'TEMPO', 'PUSH']

interface LeftPanelProps {
  prompt: string
  onPromptChange: (value: string) => void
  distanceM: number
  onDistanceChange: (value: number) => void
  terrain: Set<string>
  onToggleTerrain: (tag: string) => void
  onClearTerrain: () => void
  paceMood: number
  onPaceMoodChange: (value: number) => void
  loadingRoute: boolean
  error: string | null
  onGenerate: () => void
}

export default function LeftPanel({
  prompt,
  onPromptChange,
  distanceM,
  onDistanceChange,
  terrain,
  onToggleTerrain,
  onClearTerrain,
  paceMood,
  onPaceMoodChange,
  loadingRoute,
  error,
  onGenerate,
}: LeftPanelProps) {
  const distanceProgress = ((distanceM - 1000) / (15000 - 1000)) * 100
  const paceProgress = (paceMood / (PACE_TICKS.length - 1)) * 100

  return (
    <section className="left-panel">
      <header className="panel-topbar">
        <h1 className="wordmark">STRIDER</h1>
        <span className="status-dot status-dot-active" />
      </header>

      <div className="control-section">
        <div className="section-head">
          <span className="section-label">ROUTE PROMPT</span>
        </div>
        <div className="prompt-wrap">
          <div className="corner corner-tl" />
          <div className="corner corner-tr" />
          <div className="corner corner-bl" />
          <div className="corner corner-br" />
          <textarea
            className="prompt-input"
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            placeholder="describe your run..."
          />
        </div>
      </div>

      <div className="control-section">
        <div className="section-head">
          <span className="section-label">DISTANCE</span>
          <button type="button" className="head-action">
            SET
          </button>
        </div>
        <div className="slider-wrap">
          <div className="slider-rail" />
          <div className="slider-fill" style={{ width: `${distanceProgress}%` }} />
          <input
            type="range"
            min={1000}
            max={15000}
            step={500}
            value={distanceM}
            onChange={(event) => onDistanceChange(Number(event.target.value))}
            className="slider-input"
            aria-label="Distance"
          />
          <div className="value-readout">{`${Math.round(distanceM / 1000)}K`}</div>
        </div>
        <div className="ticks">
          {DISTANCE_TICKS.map((tick) => (
            <span key={tick} className={distanceM >= tick ? 'tick active' : 'tick'}>
              {tick >= 15000 ? '15K+' : `${Math.round(tick / 1000)}K`}
            </span>
          ))}
        </div>
      </div>

      <div className="control-section">
        <div className="section-head">
          <span className="section-label">TERRAIN FEEL</span>
          <button type="button" className="head-action" onClick={onClearTerrain}>
            CLEAR
          </button>
        </div>
        <div className="chip-grid">
          {TERRAIN_TAGS.map((tag) => {
            const active = terrain.has(tag)
            return (
              <button
                key={tag}
                type="button"
                className={active ? 'chip chip-active' : 'chip'}
                onClick={() => onToggleTerrain(tag)}
              >
                {tag}
              </button>
            )
          })}
        </div>
      </div>

      <div className="control-section">
        <div className="section-head">
          <span className="section-label">PACE MOOD</span>
          <button type="button" className="head-action">
            SET
          </button>
        </div>
        <div className="slider-wrap">
          <div className="slider-rail" />
          <div className="slider-fill" style={{ width: `${paceProgress}%` }} />
          <input
            type="range"
            min={0}
            max={PACE_TICKS.length - 1}
            step={1}
            value={paceMood}
            onChange={(event) => onPaceMoodChange(Number(event.target.value))}
            className="slider-input"
            aria-label="Pace mood"
          />
        </div>
        <div className="ticks">
          {PACE_TICKS.map((tick, index) => (
            <span key={tick} className={paceMood === index ? 'tick active' : 'tick'}>
              {tick}
            </span>
          ))}
        </div>
      </div>

      <button type="button" className="generate-btn" onClick={onGenerate} disabled={loadingRoute}>
        <span className="button-corner corner-tl" />
        <span className="button-corner corner-tr" />
        <span className="button-corner corner-bl" />
        <span className="button-corner corner-br" />
        {loadingRoute ? (
          <span className="calculating-text">
            CALCULATING<span className="cursor">_</span>
          </span>
        ) : (
          'GENERATE ROUTE'
        )}
      </button>

      {error && <div className="error-row">{error.toUpperCase()}</div>}
    </section>
  )
}

