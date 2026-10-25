import { Navigate, Route, Routes } from 'react-router-dom';
import { TripProvider } from './context/TripContext';
import { ScrapbookLayout } from './layouts/ScrapbookLayout';
import { LandingPage } from './pages/LandingPage';
import { PlannerPage } from './pages/PlannerPage';
import { ReviewPage } from './pages/ReviewPage';

export default function App({ client }) {
  return (
    <TripProvider client={client}>
      <Routes>
        <Route element={<ScrapbookLayout />}>
          <Route index element={<LandingPage />} />
          <Route path="plan" element={<PlannerPage />} />
          <Route path="review" element={<ReviewPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </TripProvider>
  );
}
