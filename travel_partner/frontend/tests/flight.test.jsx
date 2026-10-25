import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '../src/App';
import { BUILD_TAGLINES, FlightLoader, REFINE_TAGLINES, TAGLINE_INTERVAL_MS } from '../src/components/FlightLoader';
import { initialState } from '../src/context/TripContext';
import { isItineraryTurn } from '../src/hooks/useItinerary';
import { itinerary, mockClient, serverState } from './fixtures';

afterEach(() => vi.useRealTimers());

describe('FlightLoader', () => {
  it('shows a plane and rotates the tagline', () => {
    vi.useFakeTimers();
    const { container } = render(<FlightLoader destination="Utah" />);
    expect(container.querySelector('.flight-loader__plane')).toHaveTextContent('✈');
    expect(screen.getByRole('status')).toHaveTextContent('Building your itinerary for Utah');
    expect(screen.getByText(BUILD_TAGLINES[0])).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(TAGLINE_INTERVAL_MS));
    expect(screen.getByText(BUILD_TAGLINES[1])).toBeInTheDocument();
  });

  it('uses refine wording when refining', () => {
    render(<FlightLoader refining />);
    expect(screen.getByRole('status')).toHaveTextContent('Updating your itinerary');
    expect(screen.getByText(REFINE_TAGLINES[0])).toBeInTheDocument();
  });

  it('stays still when the user prefers reduced motion', () => {
    vi.useFakeTimers();
    const original = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue({ matches: true });
    const { container } = render(<FlightLoader />);
    expect(container.querySelector('.flight-loader__sky--still')).not.toBeNull();
    act(() => vi.advanceTimersByTime(TAGLINE_INTERVAL_MS * 2));
    expect(screen.getByText(BUILD_TAGLINES[0])).toBeInTheDocument();
    window.matchMedia = original;
  });

  it('renders the destination as text, not HTML', () => {
    const { container } = render(<FlightLoader destination="<img src=x onerror=alert(1)>" />);
    expect(container.querySelector('img')).toBeNull();
  });
});

describe('isItineraryTurn', () => {
  const base = { ...initialState, loading: true };
  it.each([
    ['refining an existing plan', { itinerary: itinerary() }, true],
    ['all six settled', { readyToGenerate: true, openCoreQuestions: 0 }, true],
    ['answering the last open question', { openCoreQuestions: 1, pendingAnswer: 'interests' }, true],
    ['still several questions open', { openCoreQuestions: 3, pendingAnswer: 'budget' }, false],
    ['free text with one question left', { openCoreQuestions: 1, pendingAnswer: null }, false],
    [
      'last answer but suggestions come next',
      { openCoreQuestions: 1, pendingAnswer: 'interests', preferences: { wants_suggestions: true } },
      false,
    ],
    [
      'picking a suggested destination',
      { readyToGenerate: true, awaitingDestinationChoice: true, pendingAnswer: 'destination' },
      true,
    ],
    ['suggestions pending, no choice yet', { readyToGenerate: true, awaitingDestinationChoice: true }, false],
  ])('%s', (_, overrides, expected) => {
    expect(isItineraryTurn({ ...base, ...overrides })).toBe(expected);
  });
});

describe('planner integration', () => {
  function setup(client) {
    render(
      <MemoryRouter>
        <App client={client} />
      </MemoryRouter>,
    );
  }

  it('has no "plan it now" shortcut and shows the plane while the last answer builds the itinerary', async () => {
    const user = userEvent.setup();
    const client = mockClient();
    setup(client);
    await user.click(screen.getByRole('button', { name: /start planning/i }));
    expect(screen.queryByRole('button', { name: /plan it now/i })).toBeNull();

    // Five answered; the interests card is the last one.
    let resolveTurn;
    client.sendMessage
      .mockResolvedValueOnce(
        serverState({
          open_core_questions: 1,
          preferences: { destination: 'Utah' },
          question: { key: 'interests', text: 'What do you love?', options: ['Hiking', 'Lakes'], multi_select: true },
        }),
      )
      .mockImplementationOnce(() => new Promise((resolve) => (resolveTurn = resolve)));

    await user.type(await screen.findByLabelText('Message'), 'Utah, May, 2 days, couple, mid-range{Enter}');
    expect(await screen.findByText('5 of 6 answered')).toBeInTheDocument();

    await user.click(await screen.findByRole('button', { name: 'Hiking' }));
    await user.click(screen.getByRole('button', { name: /use these/i }));
    expect(client.sendMessage).toHaveBeenLastCalledWith(expect.any(String), 'Hiking', {
      skipQuestion: null,
      answering: 'interests',
    });
    expect(await screen.findByText(/Building your itinerary for Utah/)).toBeInTheDocument();

    await act(async () =>
      resolveTurn(
        serverState({
          stage: 'drafting',
          ready_to_generate: true,
          open_core_questions: 0,
          itinerary: { itinerary: itinerary(), version: 1, confirmed_version: null },
        }),
      ),
    );
    expect(await screen.findByText('Utah Canyon Escape')).toBeInTheDocument();
    expect(screen.queryByText(/Building your itinerary/)).toBeNull();
  });

  it('shows the refine overlay over an existing itinerary', async () => {
    const user = userEvent.setup();
    const client = mockClient();
    setup(client);
    await user.click(screen.getByRole('button', { name: /start planning/i }));
    client.sendMessage
      .mockResolvedValueOnce(
        serverState({
          stage: 'drafting',
          ready_to_generate: true,
          open_core_questions: 0,
          itinerary: { itinerary: itinerary(), version: 1, confirmed_version: null },
        }),
      )
      .mockImplementationOnce(() => new Promise(() => {}));
    await user.type(await screen.findByLabelText('Message'), 'everything at once{Enter}');
    await screen.findByText('Utah Canyon Escape');
    await user.click(screen.getByRole('button', { name: 'Less driving' }));
    expect(await screen.findByText(/Updating your itinerary/)).toBeInTheDocument();
    expect(screen.getByText('Utah Canyon Escape')).toBeInTheDocument(); // old plan stays visible underneath
  });
});
