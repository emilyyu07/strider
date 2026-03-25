import { useMemo } from 'react'
import './RoutePanel.css'

const PACE_LABELS = ['EASY', 'STEADY', 'TEMPO', 'PUSH']
const PACE_KM_VALUES = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0] // min/km

interface RoutePanelProps {
  prompt: string
  terrainTags: string[]
  paceIndex: number
  paceMinPerKm: number
  loading: boolean
  hasRoute: boolean
  inCoverage: boolean
  onPromptChange: (value: string) => void
  onPaceChange: (value: number) => void
  onPaceMinPerKmChange: (value: number) => void
  onGenerate: () => void
  onRegenerate: () => void
}

export default function RoutePanel({
  prompt,
  terrainTags,
  paceIndex,
  paceMinPerKm,
  loading,
  hasRoute,
  inCoverage,
  onPromptChange,
  onPaceChange,
  onPaceMinPerKmChange,
  onGenerate,
  onRegenerate,
}: RoutePanelProps) {
  const paceProgress = useMemo(() => (paceIndex / (PACE_LABELS.length - 1)) * 100, [paceIndex])
  const paceKmProgress = useMemo(() => {
    const minPace = PACE_KM_VALUES[0]
    const maxPace = PACE_KM_VALUES[PACE_KM_VALUES.length - 1]
    return ((paceMinPerKm - minPace) / (maxPace - minPace)) * 100
  }, [paceMinPerKm])
  
  const formatPaceLabel = (pace: number): string => {
    if (pace >= PACE_KM_VALUES[PACE_KM_VALUES.length - 1]) {
      return `${pace.toFixed(1)}+ MIN/KM`
    }
    return `${pace.toFixed(1)} MIN/KM`
  }
  
  const handleTerrainClick = (tag: string) => {
    const keyword = tag.toLowerCase()
    const currentPrompt = prompt.trim()
    
    // Add keyword to prompt with proper spacing
    if (currentPrompt) {
      onPromptChange(`${currentPrompt} ${keyword}`)
    } else {
      onPromptChange(keyword)
    }
  }

  return (
    <div className="left">
      <div className="route-planner-header">
        <span className="route-planner-title">ROUTE PLANNER</span>
        <div className="route-planner-dot" />
      </div>

      <div className="sec">
        <div className="sec-header">
          <span className="sec-label">ROUTE PROMPT</span>
        </div>
        <div className="input-wrap">
          <div className="ic tl" />
          <div className="ic tr" />
          <div className="ic bl" />
          <div className="ic br" />
          <textarea
            className="prompt-area"
            placeholder="describe your run (e.g., 5km quiet scenic run)..."
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
          />
        </div>
      </div>

      <div className="sec">
        <div className="sec-header">
          <span className="sec-label">QUICK ADD KEYWORDS</span>
        </div>
        <div className="tags">
          {terrainTags.map((tag) => (
            <button key={tag} className="tag" onClick={() => handleTerrainClick(tag)}>
              {tag}
            </button>
          ))}
        </div>
      </div>

      <div className="sec">
        <div className="sec-header">
          <span className="sec-label">CURRENT PACE</span>
        </div>
        <div className="slider-row range">
          <div className="slider-track">
            <div className="slider-fill" style={{ width: `${paceKmProgress}%` }} />
            <div className="slider-dot" style={{ left: `${paceKmProgress}%` }} />
            <input
              className="slider-native"
              type="range"
              min={PACE_KM_VALUES[0]}
              max={PACE_KM_VALUES[PACE_KM_VALUES.length - 1]}
              step={0.5}
              value={paceMinPerKm}
              onChange={(event) => onPaceMinPerKmChange(Number(event.target.value))}
            />
          </div>
          <span className="slider-val">{formatPaceLabel(paceMinPerKm)}</span>
        </div>
        <div className="slider-labels">
          {[PACE_KM_VALUES[0], PACE_KM_VALUES[Math.floor(PACE_KM_VALUES.length / 2)], PACE_KM_VALUES[PACE_KM_VALUES.length - 1]].map((label, idx) => (
            <span key={idx} className={`slider-label ${Math.abs(paceMinPerKm - label) < 0.3 ? 'active' : ''}`}>
              {idx === 2 ? `${label.toFixed(1)}+` : `${label.toFixed(1)}`}
            </span>
          ))}
        </div>
      </div>

      <div className="sec">
        <div className="sec-header">
          <span className="sec-label">PACE MOOD</span>
          <span className="sec-action">SET</span>
        </div>
        <div className="slider-row range">
          <div className="slider-track">
            <div className="slider-fill" style={{ width: `${paceProgress}%` }} />
            <div className="slider-dot" style={{ left: `${paceProgress}%` }} />
            <input
              className="slider-native"
              type="range"
              min={0}
              max={3}
              step={1}
              value={paceIndex}
              onChange={(event) => onPaceChange(Number(event.target.value))}
            />
          </div>
        </div>
        <div className="slider-labels">
          {PACE_LABELS.map((label, index) => (
            <span key={label} className={`slider-label ${paceIndex === index ? 'active' : ''}`}>
              {label}
            </span>
          ))}
        </div>
      </div>

      {!inCoverage && (
        <div className="coverage-warning">
          <div className="warning-icon">⚠</div>
          <div className="warning-text">
            <strong>COVERAGE UNAVAILABLE</strong>
            <p>Coverage available in Guelph/Kitchener-Waterloo region. Enter address in coverage area.</p>
          </div>
        </div>
      )}

      <button className="gen-btn" onClick={onGenerate} disabled={loading || !prompt.trim() || !inCoverage}>
        <div className="bc tl" />
        <div className="bc tr" />
        <div className="bc bl" />
        <div className="bc br" />
        {loading ? (
          <span className="calculating">
            CALCULATING...<span className="blink">_</span>
          </span>
        ) : (
          'GENERATE ROUTE'
        )}
      </button>

      {hasRoute && (
        <button className="regen-link" onClick={onRegenerate} disabled={loading}>
          REGENERATE
        </button>
      )}
    </div>
  )
}

