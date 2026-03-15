import './CoachPanel.css'

interface CoachPanelProps {
  message: string
}

export default function CoachPanel({ message }: CoachPanelProps) {
  return (
    <div className="coach-panel">
      <div className="coach-icon">
        <div className="coach-dot" />
      </div>
      <div className="coach-text">
        <em>STRIDER COACH —</em> {message}
      </div>
    </div>
  )
}

