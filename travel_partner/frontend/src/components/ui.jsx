// Small, reusable scrapbook primitives. Presentation only, with no data fetching.
import { safeUrl } from '../utils/safeUrl';
import { toBlocks } from '../utils/text';

export function Button({ variant = 'primary', size = 'md', className = '', ...props }) {
  return <button type="button" className={`btn btn--${variant} btn--${size} ${className}`} {...props} />;
}

/** Postage stamp with perforated edges. */
export function Stamp({ color = '#f4a874', tiltDeg = '0deg', large = false, className = '', children, ...rest }) {
  return (
    <div
      className={`stamp paper-shadow ${large ? 'stamp--lg' : ''} ${className}`}
      style={{ '--stamp': color, '--tilt': tiltDeg }}
      {...rest}
    >
      <div className="stamp__inner">{children}</div>
    </div>
  );
}

/** Paper card with an optional strip of washi tape. */
export function PaperCard({ as: Tag = 'section', tape = true, tiltDeg, className = '', children, ...rest }) {
  return (
    <Tag className={`paper paper-shadow ${className}`} style={tiltDeg ? { '--tilt': tiltDeg } : undefined} {...rest}>
      {tape && <span className="tape" aria-hidden="true" />}
      {children}
    </Tag>
  );
}

export function TapeLabel({ children, color }) {
  return (
    <span className="tape-label" style={color ? { '--tape': color } : undefined}>
      {children}
    </span>
  );
}

/** External link that only renders when the URL is http(s). Otherwise plain text. */
export function SafeLink({ href, children, className = '' }) {
  const url = safeUrl(href);
  if (!url) return <span className={className}>{children}</span>;
  return (
    <a className={`link ${className}`} href={url} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

/** Renders model text as paragraphs and bullets: React text only, never HTML. */
export function RichText({ text }) {
  return toBlocks(text).map((block, i) =>
    block.type === 'ul' ? (
      <ul key={i} className="rich-list">
        {block.items.map((item, j) => (
          <li key={j}>{item}</li>
        ))}
      </ul>
    ) : (
      <p key={i}>{block.text}</p>
    ),
  );
}

export function Banner({ tone = 'error', children, onDismiss }) {
  return (
    <div className={`banner banner--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <span>{children}</span>
      {onDismiss && (
        <button type="button" className="banner__close" onClick={onDismiss} aria-label="Dismiss">
          ×
        </button>
      )}
    </div>
  );
}

export function Spinner({ label }) {
  return (
    <div className="spinner" role="status" aria-live="polite">
      <span className="spinner__plane" aria-hidden="true">✈</span>
      <span>{label}</span>
    </div>
  );
}
