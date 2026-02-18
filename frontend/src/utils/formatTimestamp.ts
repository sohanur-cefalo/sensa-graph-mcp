export function formatTimestamp(timestamp: number) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return '';

  const now = new Date();
  const msPerDay = 24 * 60 * 60 * 1000;
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / msPerDay);

  if (diffDays <= 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  return diffDays === 1 ? 'yesterday' : `${diffDays} days ago`;
}
