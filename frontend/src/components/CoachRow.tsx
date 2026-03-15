interface CoachRowProps {
  coachMessage: string
}

export default function CoachRow({ coachMessage }: CoachRowProps) {
  return (
    <div className="coach-row">
      <div className="coach-icon-frame">
        <span className="coach-dot" />
      </div>
      <div className="coach-text">
        <span className="coach-prefix">STRIDER COACH — </span>
        <span>{coachMessage}</span>
      </div>
    </div>
  )
}

