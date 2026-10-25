import { useLayoutEffect, useRef } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

export function ScrapbookLayout() {
  // Only the landing page is locked to one viewport; the other pages scroll normally.
  const { pathname } = useLocation();
  const fit = pathname === '/';
  const mainRef = useRef(null);

  // BrowserRouter keeps the old scroll position, so open every page at the top.
  useLayoutEffect(() => {
    window.scrollTo?.(0, 0);
    mainRef.current?.scrollTo?.(0, 0); // the landing page scrolls .site-main, not the window
  }, [pathname]);

  return (
    <div className={fit ? 'page page--fit' : 'page'}>
      <header className="site-header">
        <Link to="/" className="brand">
          <span className="brand__stamp" aria-hidden="true">✈</span>
          <span className="brand__name">Travel Partner</span>
        </Link>
        <span className="site-header__tag">your AI travel journal</span>
      </header>
      <main className="site-main" ref={mainRef}>
        <Outlet />
      </main>
      <footer className="site-footer">
        <p>Collecting moments one mile at a time.</p>
        <p className="site-footer__small">
          Plans are AI-generated suggestions. Prices and hours are estimates; nothing is booked for you.
        </p>
      </footer>
    </div>
  );
}
