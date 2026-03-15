import './CoachPanel.css'

interface CoachPanelProps {
  message: string
}

export default function CoachPanel({ message }: CoachPanelProps) {
  return (
    <div className="cp-root">
      <div className="cp-icon">
        <div className="cp-dot" />
      </div>
      <div className="cp-text">
        <em>STRIDER COACH —</em> {message}
      </div>
    </div>
  )
}

