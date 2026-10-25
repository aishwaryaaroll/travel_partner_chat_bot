import { useEffect, useState } from 'react';

export const BUILD_TAGLINES = [
  'Plotting your route…',
  'Finding scenic stops…',
  'Packing your days…',
  'Checking drive times…',
  'Sticking in the postcards…',
];

export const REFINE_TAGLINES = [
  'Reworking your plan…',
  'Shuffling the stops…',
  'Re-checking the route…',
  'Smoothing out the days…',
];

export const TAGLINE_INTERVAL_MS = 3000;

function prefersReducedMotion() {
  try {
    return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  } catch {
    return false;
  }
}

/** A small plane flying along a dashed route, with a rotating tagline. */
export function FlightLoader({ refining = false, destination }) {
  const taglines = refining ? REFINE_TAGLINES : BUILD_TAGLINES;
  const [index, setIndex] = useState(0);
  const [still] = useState(prefersReducedMotion);

  useEffect(() => {
    if (still) return undefined;
    const id = setInterval(() => setIndex((i) => (i + 1) % taglines.length), TAGLINE_INTERVAL_MS);
    return () => clearInterval(id);
  }, [still, taglines.length]);

  const title = refining ? 'Updating your itinerary' : 'Building your itinerary';

  return (
    <div className={`flight-loader paper paper-shadow ${refining ? 'flight-loader--overlay' : ''}`}>
      <span className="tape" aria-hidden="true" />
      <div className={`flight-loader__sky ${still ? 'flight-loader__sky--still' : ''}`} aria-hidden="true">
        <svg className="flight-loader__route" viewBox="0 0 300 90" preserveAspectRatio="none">
          <path d="M10 70 C 80 10, 150 10, 200 45 S 280 70, 290 20" />
        </svg>
        <span className="flight-loader__pin flight-loader__pin--from">●</span>
        <span className="flight-loader__pin flight-loader__pin--to">📍</span>
        <span className="flight-loader__plane">✈</span>
      </div>
      <div role="status" aria-live="polite">
        <p className="flight-loader__title script">
          {title}
          {destination ? ` for ${destination}` : ''}
        </p>
        <p className="flight-loader__tagline">{taglines[index]}</p>
      </div>
    </div>
  );
}
