import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../src/App';
import { itinerary, mockClient, serverState } from './fixtures';

function setup() {
  const client = mockClient();
  render(
    <MemoryRouter>
      <App client={client} />
    </MemoryRouter>,
  );
  return client;
}

beforeEach(() => {
  globalThis.URL.createObjectURL = vi.fn(() => 'blob:test');
  globalThis.URL.revokeObjectURL = vi.fn();
  // jsdom cannot follow a download link; the click itself is what we check.
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
});

describe('planning flow', () => {
  it('starts, answers, gets an itinerary, confirms and downloads the PDF', async () => {
    const user = userEvent.setup();
    const client = setup();

    await user.click(screen.getByRole('button', { name: /start planning/i }));
    expect(await screen.findByText(/I'm your Travel Partner/)).toBeInTheDocument();
    expect(screen.getByText('Where would you like to go?')).toBeInTheDocument();

    // Free-text answer containing several details at once.
    client.sendMessage.mockResolvedValueOnce(
      serverState({
        reply: 'Here is a first draft!',
        stage: 'drafting',
        preferences: { destination: 'Utah', duration_days: 2, interests: ['hiking'] },
        itinerary: { itinerary: itinerary(), version: 1, confirmed_version: null },
      }),
    );
    await user.type(screen.getByLabelText('Message'), '2 days in Utah, we love hiking{Enter}');
    expect(client.sendMessage).toHaveBeenCalledWith('test-session-token-abcdefghijklmnop', '2 days in Utah, we love hiking', {
      skipQuestion: null,
      answering: 'destination',
    });
    expect(await screen.findByText('Here is a first draft!')).toBeInTheDocument();
    expect(screen.getByText('Utah Canyon Escape')).toBeInTheDocument();
    expect(screen.getByText('Hiking')).toBeInTheDocument(); // passport summary

    // Quick refinement chip.
    client.sendMessage.mockResolvedValueOnce(
      serverState({ stage: 'drafting', itinerary: { itinerary: itinerary('Relaxed Utah'), version: 2, confirmed_version: null } }),
    );
    await user.click(screen.getByRole('button', { name: 'More relaxed' }));
    expect(client.sendMessage).toHaveBeenLastCalledWith(expect.any(String), 'Please make the schedule more relaxed.', {
      skipQuestion: null,
      answering: null,
    });
    expect(await screen.findByText('Relaxed Utah')).toBeInTheDocument();

    // Review → confirm the latest version → download.
    await user.click(screen.getByRole('button', { name: /review & confirm/i }));
    client.confirmItinerary.mockResolvedValueOnce(
      serverState({ reply: null, stage: 'confirmed', itinerary: { itinerary: itinerary('Relaxed Utah'), version: 2, confirmed_version: 2 } }),
    );
    await user.click(screen.getByRole('button', { name: /confirm itinerary/i }));
    expect(client.confirmItinerary).toHaveBeenCalledWith(expect.any(String), 2);
    await user.click(await screen.findByRole('button', { name: /download pdf/i }));
    await waitFor(() => expect(client.downloadPdf).toHaveBeenCalledTimes(1));
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  it('sends the question key when skipping', async () => {
    const user = userEvent.setup();
    const client = setup();
    await user.click(screen.getByRole('button', { name: /start planning/i }));
    client.sendMessage.mockResolvedValueOnce(
      serverState({ question: { key: 'budget', text: 'Budget?', options: ['Mid-range'], multi_select: false, optional: true } }),
    );
    await user.type(await screen.findByLabelText('Message'), 'Iceland for a week{Enter}');
    await user.click(await screen.findByRole('button', { name: /skip this/i }));
    expect(client.sendMessage).toHaveBeenLastCalledWith(expect.any(String), expect.stringMatching(/skip/i), {
      skipQuestion: 'budget',
      answering: null,
    });
  });

  it('shows backend errors and a privacy notice safely', async () => {
    const user = userEvent.setup();
    const client = setup();
    await user.click(screen.getByRole('button', { name: /start planning/i }));
    client.sendMessage.mockResolvedValueOnce(serverState({ notice: 'I removed something that looked like sensitive information.' }));
    await user.type(await screen.findByLabelText('Message'), 'my card is 4111111111111111{Enter}');
    expect(await screen.findByText(/looked like sensitive information/)).toBeInTheDocument();

    client.sendMessage.mockRejectedValueOnce(Object.assign(new Error('That took too long.'), { code: 'agent_timeout' }));
    await user.type(screen.getByLabelText('Message'), 'hello{Enter}');
    expect(await screen.findByRole('alert')).toHaveTextContent('That took too long.');
  });

  it('blocks over-long messages', async () => {
    const user = userEvent.setup();
    const client = setup();
    await user.click(screen.getByRole('button', { name: /start planning/i }));
    const box = await screen.findByLabelText('Message');
    await user.click(box);
    await user.paste('x'.repeat(2001));
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled();
    expect(client.sendMessage).not.toHaveBeenCalled();
  });
});
