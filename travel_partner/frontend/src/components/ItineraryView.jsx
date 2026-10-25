import { stampColor, tilt } from '../utils/text';
import { PaperCard, SafeLink, Stamp, TapeLabel } from './ui';

function Meta({ items }) {
  const shown = items.filter(Boolean);
  if (!shown.length) return null;
  return <span className="meta">{shown.join(' · ')}</span>;
}

export function DayCard({ day, index }) {
  return (
    <PaperCard as="article" className="day-card" tiltDeg={tilt(index, 0.6)} aria-label={`Day ${day.day_number}`}>
      <header className="day-card__head">
        <Stamp color={stampColor(index)} tiltDeg={tilt(index + 1, 3)} className="day-card__stamp">
          <span className="day-card__num">Day {day.day_number}</span>
        </Stamp>
        <div>
          <h3 className="day-card__title">{day.title}</h3>
          <Meta items={[day.date, day.location]} />
        </div>
      </header>

      {day.activities?.length > 0 && (
        <ul className="activities">
          {day.activities.map((a, i) => (
            <li key={i}>
              {a.time_of_day && <TapeLabel color={stampColor(index + i + 2)}>{a.time_of_day}</TapeLabel>}
              <strong>{a.name}</strong> <Meta items={[a.location, a.duration, a.est_cost]} />
              {a.description && <p>{a.description}</p>}
              {a.link && <SafeLink href={a.link.url}>{a.link.label} ↗</SafeLink>}
            </li>
          ))}
        </ul>
      )}

      {day.travel?.length > 0 && (
        <div className="day-card__section">
          <h4>🚗 Getting around</h4>
          <ul>
            {day.travel.map((t, i) => (
              <li key={i}>
                {t.origin} → {t.destination} <Meta items={[t.mode, t.est_duration, t.est_distance]} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {day.lodging && (
        <div className="day-card__section">
          <h4>🛏 Stay</h4>
          <p>
            <strong>{day.lodging.name}</strong> <Meta items={[day.lodging.location, day.lodging.est_cost]} />
          </p>
          {day.lodging.description && <p>{day.lodging.description}</p>}
          {day.lodging.url && <SafeLink href={day.lodging.url.url}>{day.lodging.url.label} ↗</SafeLink>}
        </div>
      )}

      {day.restaurants?.length > 0 && (
        <div className="day-card__section">
          <h4>🍽 Where to eat</h4>
          <ul>
            {day.restaurants.map((r, i) => (
              <li key={i}>
                {r.name} <Meta items={[r.est_cost]} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {day.notes?.length > 0 && (
        <ul className="notes">
          {day.notes.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
        </ul>
      )}
    </PaperCard>
  );
}

function ListSection({ title, items, render = (x) => x }) {
  if (!items?.length) return null;
  return (
    <div className="itinerary__section">
      <h4>{title}</h4>
      <ul>
        {items.map((item, i) => (
          <li key={i}>{render(item)}</li>
        ))}
      </ul>
    </div>
  );
}

export function BudgetCard({ budget }) {
  if (!budget) return null;
  return (
    <PaperCard className="budget-card" tiltDeg="0.5deg" aria-label="Estimated budget">
      <h3 className="script">Estimated budget</h3>
      {budget.items?.length > 0 && (
        <table className="budget-table">
          <tbody>
            {budget.items.map((item, i) => (
              <tr key={i}>
                <th scope="row">{item.category}</th>
                <td>{item.amount}</td>
              </tr>
            ))}
            {budget.total && (
              <tr className="budget-table__total">
                <th scope="row">Total (estimate)</th>
                <td>{budget.total}</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
      <ListSection title="Assumptions" items={budget.assumptions} />
    </PaperCard>
  );
}

export function ItineraryView({ itinerary, version, statusLabel }) {
  if (!itinerary) return null;
  const dates = [itinerary.start_date, itinerary.end_date].filter(Boolean).join(' – ');
  return (
    <div className="itinerary">
      <div className="boarding-pass paper-shadow">
        <div className="boarding-pass__main">
          <span className="boarding-pass__label">Boarding pass · v{version}</span>
          <h2 className="boarding-pass__title">{itinerary.title}</h2>
          <div className="boarding-pass__fields">
            <div>
              <span>Destination</span>
              <strong>{itinerary.destination}</strong>
            </div>
            <div>
              <span>Dates</span>
              <strong>{dates || 'Flexible'}</strong>
            </div>
            <div>
              <span>Duration</span>
              <strong>
                {itinerary.duration_days} day{itinerary.duration_days === 1 ? '' : 's'}
              </strong>
            </div>
          </div>
        </div>
        <div className="boarding-pass__stub">
          <span className="boarding-pass__status">{statusLabel}</span>
        </div>
      </div>

      {itinerary.summary && <p className="itinerary__summary">{itinerary.summary}</p>}

      <div className="day-list">
        {itinerary.days.map((day, i) => (
          <DayCard key={day.day_number} day={day} index={i} />
        ))}
      </div>

      <BudgetCard budget={itinerary.budget} />

      <PaperCard className="notes-card" tape={false} aria-label="Links and notes">
        <ListSection
          title="Booking & useful links"
          items={itinerary.booking_links}
          render={(l) => <SafeLink href={l.url}>{l.label} ↗</SafeLink>}
        />
        <ListSection title="Travel notes" items={itinerary.travel_notes} />
        <ListSection
          title="Caveats"
          items={[
            ...(itinerary.caveats || []),
            'Prices, hours and availability are estimates. Please check them before you go. Nothing has been booked.',
          ]}
        />
      </PaperCard>
    </div>
  );
}
