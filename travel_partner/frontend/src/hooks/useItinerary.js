import { useCallback, useState } from 'react';
import { useTrip } from '../context/TripContext';
import { saveBlob } from '../services/api';

export const QUICK_REFINEMENTS = [
  { key: 'less_driving', label: 'Less driving', message: 'Please reduce the amount of driving.' },
  { key: 'more_nature', label: 'More nature', message: 'Please add more nature and outdoor time.' },
  { key: 'lower_budget', label: 'Lower budget', message: 'Please bring the overall cost down.' },
  { key: 'more_relaxed', label: 'More relaxed', message: 'Please make the schedule more relaxed.' },
];

/**
 * Whether the message in flight is expected to (re)build the itinerary, so the
 * flight animation can be shown. True when refining an existing plan, when all
 * six initial questions are already settled, or when the traveler is answering
 * the last open one (or picking a suggested destination).
 */
export function isItineraryTurn(state) {
  if (state.itinerary) return true;
  const wantsSuggestions = state.preferences?.wants_suggestions && !state.preferences?.destination;
  if (state.awaitingDestinationChoice) return Boolean(state.pendingAnswer);
  if (state.readyToGenerate) return true;
  return state.openCoreQuestions === 1 && Boolean(state.pendingAnswer) && !wantsSuggestions;
}

/** Itinerary-related derived state and actions (refine, confirm, download). */
export function useItinerary() {
  const { state, sendMessage, confirm, downloadPdf } = useTrip();
  const [downloading, setDownloading] = useState(false);

  const { itinerary, version, confirmedVersion, loading } = state;
  const building = loading && isItineraryTurn(state);
  const isConfirmed = Boolean(version && confirmedVersion === version);
  const hasNewerDraft = Boolean(confirmedVersion && version && confirmedVersion !== version);
  const canDownload = Boolean(confirmedVersion);

  const refine = useCallback((message) => sendMessage(message), [sendMessage]);

  const confirmLatest = useCallback(() => {
    if (version && !loading) confirm(version);
  }, [version, loading, confirm]);

  const download = useCallback(async () => {
    if (!canDownload || downloading) return;
    setDownloading(true);
    try {
      const blob = await downloadPdf();
      if (blob) saveBlob(blob, 'travel-itinerary.pdf');
    } finally {
      setDownloading(false);
    }
  }, [canDownload, downloading, downloadPdf]);

  return {
    itinerary,
    version,
    confirmedVersion,
    isConfirmed,
    hasNewerDraft,
    canDownload,
    loading,
    building,
    refining: building && Boolean(itinerary),
    downloading,
    refine,
    confirmLatest,
    download,
  };
}
