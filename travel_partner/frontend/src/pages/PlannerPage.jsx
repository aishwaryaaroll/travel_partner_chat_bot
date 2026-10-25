import { Navigate, useNavigate } from 'react-router-dom';
import { ChatInput, ChatLog } from '../components/ChatPanel';
import { FlightLoader } from '../components/FlightLoader';
import { RefineBar } from '../components/ItineraryActions';
import { ItineraryView } from '../components/ItineraryView';
import { QuestionCard } from '../components/QuestionCard';
import { TripSummary } from '../components/TripSummary';
import { Banner, Button, PaperCard } from '../components/ui';
import { useTrip } from '../context/TripContext';
import { useChat } from '../hooks/useChat';
import { useItinerary } from '../hooks/useItinerary';

export function PlannerPage() {
  const navigate = useNavigate();
  const { state } = useTrip();
  const chat = useChat();
  const plan = useItinerary();

  if (!state.sessionId) return <Navigate to="/" replace />;

  const loadingLabel = plan.building ? 'Building your itinerary… (see the plan panel)' : 'Thinking about your trip…';
  const statusLabel = plan.isConfirmed ? 'Confirmed' : 'Draft';

  return (
    <div className="planner">
      <section className="planner__chat" aria-label="Conversation">
        <PaperCard className="chat-card" tape={false}>
          <ChatLog messages={chat.messages} loading={chat.loading} loadingLabel={loadingLabel} />
          {chat.notice && <Banner tone="info" onDismiss={chat.clearError}>{chat.notice}</Banner>}
          {chat.error && <Banner onDismiss={chat.clearError}>{chat.error}</Banner>}
          {!chat.loading && (
            <QuestionCard
              key={chat.question?.key + chat.messages.length}
              question={chat.question}
              onAnswer={chat.answer}
              onSkip={chat.skip}
              disabled={chat.loading}
            />
          )}
          <ChatInput
            value={chat.draft}
            onChange={chat.setDraft}
            onSubmit={() => chat.submit()}
            disabled={chat.loading}
            placeholder={plan.itinerary ? 'Ask for changes, e.g. "swap day 2 for a beach day"' : 'Type your answer or tell me anything about the trip…'}
          />
          {chat.messagesRemaining !== null && chat.messagesRemaining <= 5 && (
            <p className="hint">{chat.messagesRemaining} messages left in this conversation.</p>
          )}
        </PaperCard>
        <TripSummary preferences={state.preferences} />
      </section>

      <section className="planner__plan" aria-label="Itinerary">
        {plan.itinerary ? (
          <>
            {plan.refining && <FlightLoader refining destination={plan.itinerary.destination} />}
            <RefineBar onRefine={plan.refine} disabled={plan.loading} />
            <div className={plan.refining ? 'itinerary--dimmed' : undefined} aria-busy={plan.refining}>
              <ItineraryView itinerary={plan.itinerary} version={plan.version} statusLabel={statusLabel} />
            </div>
            <div className="planner__review">
              <Button size="lg" onClick={() => navigate('/review')} disabled={plan.loading}>
                Review & confirm →
              </Button>
            </div>
          </>
        ) : plan.building ? (
          <FlightLoader destination={state.preferences?.destination} />
        ) : (
          <PaperCard className="empty-plan" tiltDeg="1deg">
            <h2 className="script">Your itinerary will appear here</h2>
            <p>Answer the six quick questions (skip any you like) and I’ll sketch the plan.</p>
            {state.openCoreQuestions !== null && state.openCoreQuestions > 0 && (
              <p className="hint">
                {6 - state.openCoreQuestions} of 6 answered
              </p>
            )}
          </PaperCard>
        )}
      </section>
    </div>
  );
}
