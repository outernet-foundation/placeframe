import type { MeasureOverlay } from "./PointCloudScene";

// The measuring overlay drawn over the 3D canvas in an axis-on orthographic view: the segment the
// user shift-dragged, and the scale bar. Drawn as HTML/SVG rather than in the 3D scene so the line
// stays a fixed screen thickness (WebGL lines are always 1px) and the text stays crisp.

export const SEGMENT_COLOR = "#ff00aa";

// The longest bar of 1, 2 or 5 times a power of ten that fits in this many pixels, so it spans
// 120-300 px at any zoom.
const SCALE_MAX_PX = 300;
// Label every hash only when they are at least this far apart; otherwise label just the ends.
const MIN_LABEL_SPACING_PX = 30;

export function SegmentOverlay({ segment }: { segment: NonNullable<MeasureOverlay["segment"]> }) {
  const { a, b, lengthMetres } = segment;
  const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  return (
    <>
      <svg className="viewer-measure-svg">
        <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#ffffff" strokeWidth={6} strokeLinecap="round" />
        <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={SEGMENT_COLOR} strokeWidth={3} strokeLinecap="round" />
        {[a, b].map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={5} fill={SEGMENT_COLOR} stroke="#ffffff" strokeWidth={2} />
        ))}
      </svg>
      <div className="viewer-measure-label" style={{ left: mid.x, top: mid.y }}>
        {formatLength(lengthMetres)}
      </div>
    </>
  );
}

export function ScaleBar({ metresPerPixel }: { metresPerPixel: number }) {
  const { length, divisions } = niceScale(metresPerPixel * SCALE_MAX_PX);
  const width = length / metresPerPixel;
  const step = length / divisions;
  const labelEvery = width / divisions >= MIN_LABEL_SPACING_PX;
  const pad = 20; // room for the end labels, which are centred on their ticks
  return (
    <svg className="viewer-scale" width={width + pad * 2} height={34} aria-label={`Scale: ${formatLength(length)}`}>
      <g transform={`translate(${pad} 0)`}>
        <line x1={0} x2={width} y1={8} y2={8} stroke="#1a1a1a" strokeWidth={2} />
        {Array.from({ length: divisions + 1 }, (_, i) => {
          const x = (i / divisions) * width;
          const end = i === 0 || i === divisions;
          return (
            <g key={i}>
              <line x1={x} x2={x} y1={end ? 2 : 4} y2={14} stroke="#1a1a1a" strokeWidth={end ? 2 : 1.5} />
              {(labelEvery || end) && (
                <text x={x} y={28} textAnchor="middle" className="viewer-scale-text">
                  {i === divisions ? formatLength(step * i) : formatNumber(step * i, length)}
                </text>
              )}
            </g>
          );
        })}
      </g>
    </svg>
  );
}

// A round bar length near `target` metres and how many hashes split it into round steps: 50 m in
// five 10 m steps, 20 m in four 5 m steps, 10 m in five 2 m steps.
function niceScale(target: number): { length: number; divisions: number } {
  const power = Math.pow(10, Math.floor(Math.log10(target)));
  const leading = [1, 2, 5].filter((m) => m * power <= target).pop() ?? 1;
  return { length: leading * power, divisions: leading === 2 ? 4 : 5 };
}

function formatLength(metres: number): string {
  if (metres >= 1000) return `${trim(metres / 1000)} km`;
  if (metres >= 1) return `${trim(metres)} m`;
  if (metres >= 0.01) return `${trim(metres * 100)} cm`;
  return `${trim(metres * 1000)} mm`;
}

// A hash label in the same unit as the bar's total, without the unit (only the last label has it).
function formatNumber(value: number, total: number): string {
  if (total >= 1000) return trim(value / 1000);
  if (total >= 1) return trim(value);
  if (total >= 0.01) return trim(value * 100);
  return trim(value * 1000);
}

function trim(value: number): string {
  return String(Number(value.toPrecision(3)));
}
