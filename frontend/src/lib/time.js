/** "5 min ago", "3 h ago", "2 d ago" from an ISO timestamp. */
export function timeAgo(iso) {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return 'just now';
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}

/** How to show a live headline's time: date-only feeds show the date; feeds with no date show when Raven first saw it. */
export function itemTime(item) {
  if (item.date_only) {
    const day = new Date(item.published_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', timeZone: 'Asia/Kolkata' });
    return { text: day, title: 'The feed gives a date but no time' };
  }
  if (item.time_estimated) return { text: `seen ${timeAgo(item.published_at)}`, title: 'The feed gives no time; this is when Raven first saw it' };
  return { text: timeAgo(item.published_at), title: item.published_at };
}
