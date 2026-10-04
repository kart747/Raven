import { useCallback, useEffect, useState } from 'react';

const read = () => Object.fromEntries(new URLSearchParams(window.location.hash.slice(1)));

/**
 * App state kept in the URL hash (#tab=donations&donor=10) so every view can be bookmarked and shared.
 * update({ key: value }) merges; null/'' removes a key. Each change is a history entry, so Back works.
 */
export default function useHashParams() {
  const [params, setParams] = useState(read);

  useEffect(() => {
    const onChange = () => setParams(read());
    window.addEventListener('popstate', onChange);
    window.addEventListener('hashchange', onChange);
    return () => {
      window.removeEventListener('popstate', onChange);
      window.removeEventListener('hashchange', onChange);
    };
  }, []);

  const update = useCallback((patch) => {
    const next = { ...read(), ...patch };
    Object.keys(next).forEach((k) => {
      if (next[k] === null || next[k] === undefined || next[k] === '') delete next[k];
    });
    const hash = new URLSearchParams(next).toString();
    window.history.pushState(null, '', hash ? `#${hash}` : window.location.pathname + window.location.search);
    setParams(next);
  }, []);

  return [params, update];
}
