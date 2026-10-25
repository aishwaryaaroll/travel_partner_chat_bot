import { Link, Navigate } from 'react-router-dom';
import { ConfirmPanel } from '../components/ItineraryActions';
import { ItineraryView } from '../components/ItineraryView';
import { Banner } from '../components/ui';
import { useTrip } from '../context/TripContext';
import { useItinerary } from '../hooks/useItinerary';

export function ReviewPage() {
  const { state, clearError } = useTrip();
  const plan = useItinerary();

  if (!state.sessionId) return <Navigate to="/" replace />;
  if (!plan.itinerary) return <Navigate to="/plan" replace />;

  return (
    <div className="review">
      <div className="review__top">
        <Link to="/plan" className="link">← Back to planning</Link>
        <h1 className="script review__title">Review your trip</h1>
      </div>
      {state.error && <Banner onDismiss={clearError}>{state.error}</Banner>}
      <ConfirmPanel
        version={plan.version}
        isConfirmed={plan.isConfirmed}
        hasNewerDraft={plan.hasNewerDraft}
        canDownload={plan.canDownload}
        loading={plan.loading}
        downloading={plan.downloading}
        onConfirm={plan.confirmLatest}
        onDownload={plan.download}
      />
      <ItineraryView
        itinerary={plan.itinerary}
        version={plan.version}
        statusLabel={plan.isConfirmed ? 'Confirmed' : 'Draft'}
      />
    </div>
  );
}
