import { vi } from 'vitest';

export const itinerary = (title = 'Utah Canyon Escape', extra = {}) => ({
  title,
  destination: 'Southern Utah',
  start_date: '2026-05-10',
  end_date: '2026-05-11',
  duration_days: 2,
  summary: 'Red rock canyons.',
  days: [
    {
      day_number: 1,
      title: 'Arrive in Springdale',
      location: 'Springdale',
      activities: [{ time_of_day: 'Morning', name: 'Riverside Walk', link: { label: 'NPS', url: 'https://www.nps.gov/zion/' } }],
      travel: [{ origin: 'Las Vegas', destination: 'Springdale', est_duration: '2h45m' }],
      lodging: { name: 'Canyon cabin', est_cost: '~$180/night (estimate)' },
      restaurants: [],
      notes: [],
    },
    { day_number: 2, title: 'Angels Landing views', activities: [], travel: [], restaurants: [], notes: [] },
  ],
  budget: { items: [{ category: 'Lodging', amount: '~$360' }], total: '~$900', assumptions: ['2 travelers'] },
  booking_links: [],
  travel_notes: [],
  caveats: ['Check flash flood warnings.'],
  ...extra,
});

export const serverState = (overrides = {}) => ({
  session_id: null,
  reply: 'Sounds great!',
  notice: null,
  question: null,
  preferences: {},
  stage: 'gathering',
  itinerary: { itinerary: null, version: null, confirmed_version: null },
  messages_remaining: 30,
  open_core_questions: 6,
  ready_to_generate: false,
  awaiting_destination_choice: false,
  ...overrides,
});

export function mockClient() {
  return {
    createSession: vi.fn().mockResolvedValue(
      serverState({
        session_id: 'test-session-token-abcdefghijklmnop',
        reply: "Hi! I'm your Travel Partner.",
        question: {
          key: 'destination',
          text: 'Where would you like to go?',
          options: ['Suggest destinations for me'],
          multi_select: false,
          optional: false,
        },
      }),
    ),
    getSession: vi.fn(),
    deleteSession: vi.fn().mockResolvedValue(null),
    sendMessage: vi.fn().mockResolvedValue(serverState()),
    confirmItinerary: vi.fn(),
    downloadPdf: vi.fn().mockResolvedValue(new Blob(['%PDF'], { type: 'application/pdf' })),
  };
}
