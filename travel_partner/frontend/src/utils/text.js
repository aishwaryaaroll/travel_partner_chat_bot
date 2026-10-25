/**
 * Splits plain model text into paragraphs and bullet lists without any HTML parsing.
 * Returns blocks like { type: 'p', text } or { type: 'ul', items }.
 */
export function toBlocks(text) {
  if (!text) return [];
  const blocks = [];
  let list = null;
  for (const raw of String(text).split(/\r?\n/)) {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    if (bullet) {
      if (!list) {
        list = { type: 'ul', items: [] };
        blocks.push(list);
      }
      list.items.push(bullet[1].replace(/\*\*/g, ''));
      continue;
    }
    list = null;
    if (line) blocks.push({ type: 'p', text: line.replace(/\*\*/g, '') });
  }
  return blocks;
}

export const INTEREST_LABELS = {
  mountains: 'Mountains',
  lakes: 'Lakes',
  waterfalls: 'Waterfalls',
  beaches: 'Beaches',
  scenic_drives: 'Scenic drives',
  hiking: 'Hiking',
  cities: 'Cities',
  food: 'Food',
  culture: 'Culture',
  relaxation: 'Relaxation',
  photography: 'Photography',
};

/** Pastel stamp colours taken from the reference design. */
export const STAMP_COLORS = ['#f4a874', '#b5d99c', '#c9b3e6', '#f7dc7c', '#f3a9c4', '#f2a7a0', '#d9b98c'];

export function stampColor(index) {
  return STAMP_COLORS[Math.abs(index) % STAMP_COLORS.length];
}

/** Small deterministic tilt so cards look hand-placed but don't jump between renders. */
export function tilt(index, max = 1.6) {
  const pattern = [-1, 0.7, -0.4, 1, -0.8, 0.5];
  return `${(pattern[Math.abs(index) % pattern.length] * max).toFixed(2)}deg`;
}
