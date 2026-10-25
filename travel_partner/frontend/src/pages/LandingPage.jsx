import { useNavigate } from 'react-router-dom';
import { Button, PaperCard, Stamp } from '../components/ui';
import { useTrip } from '../context/TripContext';
import { stampColor, tilt } from '../utils/text';

const POSTCARDS = [
  { emoji: '🏔', place: 'Mountains', note: 'alpine lakes & ridgelines' },
  { emoji: '🌊', place: 'Coastlines', note: 'beaches & sunsets' },
  { emoji: '🏙', place: 'Cities', note: 'food, culture & late nights' },
  { emoji: '🚗', place: 'Road trips', note: 'scenic drives & detours' },
];

const STEPS = [
  ['Tell me about your trip', 'A few quick questions: where, when, who and what you love. Skip anything.'],
  ['Get a day-by-day plan', 'Activities, drive times, places to stay and estimated costs.'],
  ['Tweak, confirm, download', 'Ask for less driving or a slower pace, then save it as a PDF.'],
];

export function LandingPage() {
  const navigate = useNavigate();
  const { state, startTrip } = useTrip();

  const start = async () => {
    await startTrip();
    navigate('/plan');
  };

  return (
    <div className="landing">
      <section className="hero">
        <div className="hero__copy">
          <p className="script hero__kicker">Postcards from your next adventure</p>
          <h1 className="hero__title">Plan a trip with a travel partner who listens.</h1>
          <p className="hero__lead">
            Chat with an AI travel agent that asks just enough, then sketches a personalised day-by-day itinerary
            you can refine, confirm and keep.
          </p>
          <div className="hero__cta">
            <Button size="lg" onClick={start} disabled={state.loading}>
              {state.loading ? 'Opening your journal…' : 'Start planning'}
            </Button>
            {state.sessionId && (
              <Button variant="ghost" onClick={() => navigate('/plan')}>
                Continue my trip
              </Button>
            )}
          </div>
          {state.error && <p className="error-text" role="alert">{state.error}</p>}
        </div>
        <div className="hero__collage" aria-hidden="true">
          {POSTCARDS.map((p, i) => (
            <Stamp key={p.place} large color={stampColor(i)} tiltDeg={tilt(i, 4)} className="hero__stamp">
              <span className="hero__emoji">{p.emoji}</span>
              <span className="hero__place">{p.place}</span>
              <span className="hero__note">{p.note}</span>
            </Stamp>
          ))}
        </div>
      </section>

      <section className="steps">
        {STEPS.map(([title, text], i) => (
          <PaperCard key={title} tiltDeg={tilt(i, 1)} className="step">
            <span className="step__num">{i + 1}</span>
            <h2 className="script">{title}</h2>
            <p>{text}</p>
          </PaperCard>
        ))}
      </section>

      <blockquote className="quote">“Not all those who wander are lost.” <cite>J.R.R. Tolkien</cite></blockquote>

      <p className="privacy-note">
        🔒 No account needed. I only ask for travel details, never passport numbers, IDs or payment details. Your
        trip is kept in memory for this visit only.
      </p>
    </div>
  );
}
