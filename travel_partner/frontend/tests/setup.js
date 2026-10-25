import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => cleanup());

// jsdom does not implement scrolling; ScrapbookLayout scrolls to the top on every route change.
window.scrollTo = () => {};
