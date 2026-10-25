import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ChatBubble } from '../src/components/ChatPanel';
import { ChipSelect } from '../src/components/ChipSelect';
import { ConfirmPanel } from '../src/components/ItineraryActions';
import { ItineraryView } from '../src/components/ItineraryView';
import { QuestionCard } from '../src/components/QuestionCard';
import { SafeLink } from '../src/components/ui';
import { itinerary } from './fixtures';

describe('ChipSelect', () => {
  it('supports multiple selections', async () => {
    const onChange = vi.fn();
    const { rerender } = render(<ChipSelect multi options={['Hiking', 'Lakes']} value={[]} onChange={onChange} />);
    await userEvent.click(screen.getByRole('button', { name: 'Hiking' }));
    expect(onChange).toHaveBeenLastCalledWith(['Hiking']);
    rerender(<ChipSelect multi options={['Hiking', 'Lakes']} value={['Hiking']} onChange={onChange} />);
    expect(screen.getByRole('button', { name: 'Hiking' })).toHaveAttribute('aria-pressed', 'true');
    await userEvent.click(screen.getByRole('button', { name: 'Lakes' }));
    expect(onChange).toHaveBeenLastCalledWith(['Hiking', 'Lakes']);
  });
});

describe('QuestionCard', () => {
  const question = { key: 'interests', text: 'What do you love?', options: ['Hiking', 'Lakes', 'Food'], multi_select: true, optional: true };

  it('submits several picks at once and allows skipping', async () => {
    const onAnswer = vi.fn();
    const onSkip = vi.fn();
    render(<QuestionCard question={question} onAnswer={onAnswer} onSkip={onSkip} />);
    await userEvent.click(screen.getByRole('button', { name: 'Hiking' }));
    await userEvent.click(screen.getByRole('button', { name: 'Food' }));
    await userEvent.click(screen.getByRole('button', { name: /use these \(2\)/i }));
    expect(onAnswer).toHaveBeenCalledWith(['Hiking', 'Food']);
    await userEvent.click(screen.getByRole('button', { name: /skip this/i }));
    expect(onSkip).toHaveBeenCalledWith('interests');
  });

  it('hides skip for required questions', () => {
    render(<QuestionCard question={{ ...question, multi_select: false, optional: false }} onAnswer={vi.fn()} onSkip={vi.fn()} />);
    expect(screen.queryByRole('button', { name: /skip/i })).toBeNull();
  });
});

describe('XSS safety', () => {
  it('renders chat HTML as text', () => {
    const { container } = render(<ChatBubble role="assistant" content={'<img src=x onerror="alert(1)"><script>alert(2)</script>'} />);
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('script')).toBeNull();
    expect(screen.getByText(/<img src=x/)).toBeInTheDocument();
  });

  it('renders itinerary fields as text and drops unsafe links', () => {
    const it2 = itinerary('<b>Bold</b> trip', {
      booking_links: [
        { label: 'Evil', url: 'javascript:alert(1)' },
        { label: 'Good', url: 'https://example.com/' },
      ],
    });
    const { container } = render(<ItineraryView itinerary={it2} version={1} statusLabel="Draft" />);
    expect(container.querySelector('b')).toBeNull();
    expect(screen.getByText('<b>Bold</b> trip')).toBeInTheDocument();
    expect(screen.getByText('Evil ↗').closest('a')).toBeNull();
    const good = screen.getByText('Good ↗').closest('a');
    expect(good).toHaveAttribute('href', 'https://example.com/');
    expect(good).toHaveAttribute('rel', 'noopener noreferrer');
    expect(good).toHaveAttribute('target', '_blank');
  });

  it('SafeLink never emits a javascript: href', () => {
    const { container } = render(<SafeLink href="javascript:alert(1)">x</SafeLink>);
    expect(container.querySelector('a')).toBeNull();
  });
});

describe('ItineraryView', () => {
  it('shows days, estimates and caveats', () => {
    render(<ItineraryView itinerary={itinerary()} version={2} statusLabel="Draft" />);
    expect(screen.getByRole('article', { name: 'Day 1' })).toBeInTheDocument();
    expect(screen.getByRole('article', { name: 'Day 2' })).toBeInTheDocument();
    expect(screen.getByText(/\$180\/night \(estimate\)/)).toBeInTheDocument();
    expect(screen.getByText(/Nothing has been booked/)).toBeInTheDocument();
  });
});

describe('ConfirmPanel', () => {
  const base = { version: 2, loading: false, downloading: false, onConfirm: vi.fn(), onDownload: vi.fn() };

  it('only offers download after confirmation', () => {
    const { rerender } = render(<ConfirmPanel {...base} isConfirmed={false} hasNewerDraft={false} canDownload={false} />);
    expect(screen.getByRole('button', { name: /confirm itinerary/i })).toBeEnabled();
    expect(screen.queryByRole('button', { name: /download pdf/i })).toBeNull();
    rerender(<ConfirmPanel {...base} isConfirmed hasNewerDraft={false} canDownload />);
    expect(screen.queryByRole('button', { name: /confirm itinerary/i })).toBeNull();
    expect(screen.getByRole('button', { name: /download pdf/i })).toBeEnabled();
  });

  it('warns when the plan changed after confirming', () => {
    render(<ConfirmPanel {...base} isConfirmed={false} hasNewerDraft canDownload />);
    expect(screen.getByText(/still has the confirmed version/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /confirm itinerary/i })).toBeInTheDocument();
  });
});
