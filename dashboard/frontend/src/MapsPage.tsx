import { useCallback, useEffect, useState } from "react";
import { listMaps, unpublishMap } from "./api";
import { errorText } from "./storage";
import type { LocalizationMap } from "./types";

// What the capture tool's picker labels a map with: the capture's name, not the map's own (see
// AppUI.SelectValidationTargetDialog). Showing the same string is the point of this page -- a name
// here that the device doesn't show would make the mirror misleading.
function deviceLabel(map: LocalizationMap): string {
  return map.device_label ?? map.name ?? `Unnamed [${map.id.slice(0, 8)}]`;
}

function placement(map: LocalizationMap): string {
  if (map.is_identity_placement) return "identity";
  const { x, y, z } = map.position;
  return `${x.toFixed(1)}, ${y.toFixed(1)}, ${z.toFixed(1)}`;
}

export function MapsPage() {
  const [maps, setMaps] = useState<LocalizationMap[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  // One withdrawal at a time, by map id, so a row's button can't be pressed twice while in flight.
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(() => {
    listMaps()
      .then(setMaps)
      .catch((e: unknown) => setError(errorText(e)));
  }, []);

  useEffect(refresh, [refresh]);

  async function withdraw(map: LocalizationMap): Promise<void> {
    setBusy(map.id);
    setError(null);
    try {
      await unpublishMap(map.id);
      refresh();
    } catch (e: unknown) {
      setError(errorText(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Maps</h2>
        <span className="node-count">{maps ? `${maps.length} published` : "loading…"}</span>
      </div>
      <div className="banner banner-info">
        These are the maps a device can localize against — the same rows the capture tool&apos;s map picker
        draws from. A reconstruction that has succeeded is <strong>not</strong> here until it is published,
        which is what the Publish action on a reconstruction does.
      </div>
      {error ? <div className="banner banner-error">{error}</div> : null}
      <table className="data-table">
        <thead>
          <tr>
            <th>Shown on device as</th>
            <th>Reconstruction</th>
            <th>Placement</th>
            <th>Published</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {maps && maps.length === 0 ? (
            <tr>
              <td className="empty" colSpan={5}>
                Nothing published yet. Publish a succeeded reconstruction from the Captures tab.
              </td>
            </tr>
          ) : null}
          {(maps ?? []).map((map) => (
            <tr key={map.id}>
              <td>{deviceLabel(map)}</td>
              <td className="mono">{map.reconstruction_id.slice(0, 8)}</td>
              <td className="mono" title="Where this map's frame sits in the world frame a device localizes into">
                {placement(map)}
              </td>
              <td className="mono">{map.created_at ? map.created_at.slice(0, 10) : "—"}</td>
              <td>
                <div className="actions">
                  <button
                    disabled={busy === map.id}
                    title="Withdraw from devices; the reconstruction and its stored map data are untouched"
                    onClick={() => void withdraw(map)}
                  >
                    {busy === map.id ? "Unpublishing…" : "Unpublish"}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
