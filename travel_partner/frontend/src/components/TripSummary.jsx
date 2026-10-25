import { INTEREST_LABELS, stampColor } from '../utils/text';
import { TapeLabel } from './ui';

const FIELDS = [
  ['destination', 'Where'],
  ['travel_dates', 'When'],
  ['duration_days', 'Days'],
  ['travelers', 'Who'],
  ['budget', 'Budget'],
];

/** "Passport page" showing what the agent has understood so far. */
export function TripSummary({ preferences }) {
  const entries = FIELDS.filter(([key]) => preferences?.[key] != null && preferences[key] !== '');
  const interests = preferences?.interests || [];
  if (!entries.length && !interests.length && !preferences?.wants_suggestions) return null;

  return (
    <aside className="passport paper-shadow" aria-label="What I know so far">
      <h3 className="passport__title">Passport</h3>
      <dl className="passport__fields">
        {preferences.wants_suggestions && !preferences.destination && (
          <div>
            <dt>Where</dt>
            <dd>Open to suggestions</dd>
          </div>
        )}
        {entries.map(([key, label]) => (
          <div key={key}>
            <dt>{label}</dt>
            <dd>{String(preferences[key])}</dd>
          </div>
        ))}
      </dl>
      {interests.length > 0 && (
        <div className="passport__interests">
          {interests.map((i, idx) => (
            <TapeLabel key={i} color={stampColor(idx)}>
              {INTEREST_LABELS[i] || i}
            </TapeLabel>
          ))}
        </div>
      )}
    </aside>
  );
}
