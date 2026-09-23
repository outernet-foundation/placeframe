// Remembered form values (last-used folders, focal length, tree expansion). localStorage can throw
// (private browsing, quota, disabled site data) or come back empty — either way fall back to the
// default rather than breaking the page; remembering is a convenience, never required.
export function readStored(key: string, fallback = ""): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

export function store(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

export const STORAGE_KEYS = {
  expanded: "placeframe-dashboard.tree.expanded",
  localizeImageDir: "placeframe-dashboard.localize.imageDir",
  importTar: "placeframe-dashboard.localize.importTar",
  focalLength: "placeframe-dashboard.reconstruct.poselessFocalLength",
  exportZipDir: "placeframe-dashboard.visualize.exportZipOutputDir",
  exportPosesDir: "placeframe-dashboard.tools.exportPosesOutputDir",
} as const;

// Server-side join: the dashboard always runs on the machine the CLI does, with Linux paths.
export function joinPath(dir: string, filename: string): string {
  return `${dir.replace(/\/+$/, "")}/${filename}`;
}

export function parentDir(path: string): string | undefined {
  const i = path.lastIndexOf("/");
  return i > 0 ? path.slice(0, i) : undefined;
}

export function errorText(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}
