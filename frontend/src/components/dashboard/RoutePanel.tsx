import { useMemo } from 'react'
import './RoutePanel.css'

const DISTANCE_LABELS = [1000, 3000, 5000, 10000, 15000]
const PACE_LABELS = ['EASY', 'STEADY', 'TEMPO', 'PUSH']

interface RoutePanelProps {
  prompt: string
  distanceM: number
  terrainTags: string[]
  selectedTerrain: string[]
  paceIndex: number
  loading: boolean
  hasRoute: boolean
  onPromptChange: (value: string) => void
  onDistanceChange: (value: number) => void
  onPaceChange: (value: number) => void
  onToggleTerrain: (tag: string) => void
  onClearTerrain: () => void
  onGenerate: () => void
  onRegenerate: () => void
}

export default function RoutePanel({
  prompt,
  distanceM,
  terrainTags,
  selectedTerrain,
  paceIndex,
  loading,
  hasRoute,
  onPromptChange,
  onDistanceChange,
  onPaceChange,
  onToggleTerrain,
  onClearTerrain,
  onGenerate,
  onRegenerate,
}: RoutePanelProps) {
  const distanceProgress = useMemo(() => ((distanceM - 1000) / (15000 - 1000)) * 100, [distanceM])
  const paceProgress = useMemo(() => (paceIndex / (PACE_LABELS.length - 1)) * 100, [paceIndex])

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
            placeholder="describe your run..."
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
          />
        </div>
      </div>

      <div className="sec">
        <div className="sec-header">
          <span className="sec-label">DISTANCE</span>
          <span className="sec-action">SET</span>
        </div>
        <div className="slider-row range">
          <div className="slider-track">
            <div className="slider-fill" style={{ width: `${distanceProgress}%` }} />
            <div className="slider-dot" style={{ left: `${distanceProgress}%` }} />
            <input
              className="slider-native"
              type="range"
              min={1000}
              max={15000}
              step={500}
              value={distanceM}
              onChange={(event) => onDistanceChange(Number(event.target.value))}
            />
          </div>
          <span className="slider-val">{`${Math.round(distanceM / 1000)} KM`}</span>
        </div>
        <div className="slider-labels">
          {DISTANCE_LABELS.map((label) => (
            <span key={label} className={`slider-label ${distanceM >= label ? 'active' : ''}`}>
              {label >= 15000 ? '15K+' : `${Math.round(label / 1000)}K`}
            </span>
          ))}
        </div>
      </div>

      <div className="sec">
        <div className="sec-header">
          <span className="sec-label">TERRAIN FEEL</span>
          <span className="sec-action action-btn" onClick={onClearTerrain}>
            CLEAR
          </span>
        </div>
        <div className="tags">
          {terrainTags.map((tag) => {
            const enabled = selectedTerrain.includes(tag)
            return (
              <button key={tag} className={`tag ${enabled ? 'on' : ''}`} onClick={() => onToggleTerrain(tag)}>
                {tag}
              </button>
            )
          })}
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

      <button className="gen-btn" onClick={onGenerate} disabled={loading || !prompt.trim()}>
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

