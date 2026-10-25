import { QUICK_REFINEMENTS } from '../hooks/useItinerary';
import { Banner, Button, PaperCard } from './ui';

export function RefineBar({ onRefine, disabled }) {
  return (
    <div className="refine-bar" role="group" aria-label="Quick changes">
      <span className="refine-bar__label">Tweak it:</span>
      {QUICK_REFINEMENTS.map((r) => (
        <Button key={r.key} variant="chip" size="sm" disabled={disabled} onClick={() => onRefine(r.message)}>
          {r.label}
        </Button>
      ))}
    </div>
  );
}

export function ConfirmPanel({ version, isConfirmed, hasNewerDraft, canDownload, loading, downloading, onConfirm, onDownload }) {
  return (
    <PaperCard className="confirm-panel" tape={false} aria-label="Confirm and download">
      {hasNewerDraft && (
        <Banner tone="info">
          You’ve changed the plan since you confirmed it. The PDF still has the confirmed version until you confirm
          this one.
        </Banner>
      )}
      {isConfirmed ? (
        <p className="confirm-panel__done">✓ Version {version} confirmed. Your PDF is ready.</p>
      ) : (
        <p>Happy with this plan? Confirm it to lock it in for the PDF.</p>
      )}
      <div className="confirm-panel__actions">
        {!isConfirmed && (
          <Button onClick={onConfirm} disabled={loading || !version}>
            Confirm itinerary
          </Button>
        )}
        {canDownload && (
          <Button variant={isConfirmed ? 'primary' : 'secondary'} onClick={onDownload} disabled={downloading}>
            {downloading ? 'Preparing PDF…' : 'Download PDF'}
          </Button>
        )}
      </div>
    </PaperCard>
  );
}
