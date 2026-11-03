import { useEffect, useRef, useState } from "react";
import type { LocalizationImage } from "../types";

// Per-image summary charts shown above a run's image table: match quality and position as a
// function of image number. Plain SVG, since the dashboard has no charting dependency. The four
// charts share one hover index so the crosshair lines up the same image across all of them.

const SERIES_BLUE = "#3987e5";
const SERIES_ORANGE = "#d95926";
const GRID = "#262932";
const AXIS_TEXT = "#8a909c";
const SURFACE = "#14161a";

const HEIGHT = 190;
const MARGIN = { top: 10, bottom: 26, left: 52, right: 16 };
const RIGHT_AXIS_MARGIN = 52;
// Below this many images every point gets a dot; above it the line alone reads better.
const DOT_ALL_MAX = 60;

interface Series {
  label: string;
  colour: string;
  values: (number | null)[];
  format: (value: number) => string;
  axis: "left" | "right";
  axisTitle?: string;
}

export function RunCharts({ images }: { images: LocalizationImage[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const indices = images.map((img) => img.index);

  const ok = (img: LocalizationImage) => img.status === "ok" && img.position;
  const position = (axis: "x" | "y" | "z") => images.map((img) => (ok(img) ? img.position![axis] : null));
  const metres = (value: number) => `${value.toFixed(3)} m`;

  const charts: { title: string; series: Series[] }[] = [
    {
      title: "Inlier ratio and reprojection error",
      series: [
        {
          label: "Ratio",
          colour: SERIES_BLUE,
          values: images.map((img) => (img.metrics ? img.metrics.inlier_ratio * 100 : null)),
          format: (value) => `${value.toFixed(1)}%`,
          axis: "left",
          axisTitle: "Ratio (%)",
        },
        {
          label: "Reproj error",
          colour: SERIES_ORANGE,
          values: images.map((img) => (img.metrics ? img.metrics.reprojection_error_median : null)),
          format: (value) => `${value.toFixed(2)} px`,
          axis: "right",
          axisTitle: "Reproj (px)",
        },
      ],
    },
    { title: "X", series: [{ label: "X", colour: SERIES_BLUE, values: position("x"), format: metres, axis: "left" }] },
    { title: "Y", series: [{ label: "Y", colour: SERIES_BLUE, values: position("y"), format: metres, axis: "left" }] },
    { title: "Z", series: [{ label: "Z", colour: SERIES_BLUE, values: position("z"), format: metres, axis: "left" }] },
  ];

  return (
    <div className="run-charts">
      {charts.map((chart) => (
        <SeriesChart
          key={chart.title}
          title={chart.title}
          series={chart.series}
          indices={indices}
          failed={images.map((img) => img.status !== "ok")}
          hover={hover}
          onHover={setHover}
        />
      ))}
    </div>
  );
}

function SeriesChart({
  title,
  series,
  indices,
  failed,
  hover,
  onHover,
}: {
  title: string;
  series: Series[];
  indices: number[];
  failed: boolean[];
  hover: number | null;
  onHover: (slot: number | null) => void;
}) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;
    const observer = new ResizeObserver(() => setWidth(wrapper.clientWidth));
    observer.observe(wrapper);
    setWidth(wrapper.clientWidth);
    return () => observer.disconnect();
  }, []);

  const hasRight = series.some((s) => s.axis === "right");
  const left = MARGIN.left;
  const right = width - (hasRight ? RIGHT_AXIS_MARGIN : MARGIN.right);
  const top = MARGIN.top;
  const bottom = HEIGHT - MARGIN.bottom;

  const xMin = indices.length ? indices[0] : 0;
  const xMax = indices.length ? indices[indices.length - 1] : 1;
  const xOf = (index: number) => (xMax === xMin ? (left + right) / 2 : left + ((index - xMin) / (xMax - xMin)) * (right - left));

  const scales = {
    left: axisScale(series.filter((s) => s.axis === "left"), top, bottom),
    right: axisScale(series.filter((s) => s.axis === "right"), top, bottom),
  };

  function onMove(event: React.MouseEvent<SVGRectElement>) {
    const box = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - box.left + left;
    let nearest = 0;
    for (let slot = 1; slot < indices.length; slot++) {
      if (Math.abs(xOf(indices[slot]) - x) < Math.abs(xOf(indices[nearest]) - x)) nearest = slot;
    }
    onHover(indices.length ? nearest : null);
  }

  const xTicks = niceTicks(xMin, xMax, Math.max(2, Math.floor((right - left) / 70))).filter(
    (tick) => Number.isInteger(tick) && tick >= xMin && tick <= xMax,
  );
  const leftSeries = series.find((s) => s.axis === "left");
  const rightSeries = series.find((s) => s.axis === "right");
  const tooltipLeft = hover !== null ? xOf(indices[hover]) : 0;

  return (
    <div className="run-chart">
      <div className="run-chart-header">
        <span className="run-chart-title">{title}</span>
        {series.length > 1 && (
          <span className="run-chart-legend">
            {series.map((s) => (
              <span key={s.label} className="run-chart-legend-item">
                <span className="run-chart-key" style={{ background: s.colour }} />
                {s.label} ({s.axis} axis)
              </span>
            ))}
          </span>
        )}
      </div>
      <div ref={wrapperRef} className="run-chart-plot" style={{ height: HEIGHT }}>
        {width > 0 && (
          <svg width={width} height={HEIGHT} role="img" aria-label={`${title} by image number`}>
            {scales.left.ticks.map((tick) => (
              <g key={`l${tick}`}>
                <line x1={left} x2={right} y1={scales.left.y(tick)} y2={scales.left.y(tick)} stroke={GRID} />
                <text x={left - 6} y={scales.left.y(tick)} dy="0.32em" textAnchor="end" className="run-chart-tick">
                  {formatTick(tick)}
                </text>
              </g>
            ))}
            {hasRight &&
              scales.right.ticks.map((tick) => (
                <text key={`r${tick}`} x={right + 6} y={scales.right.y(tick)} dy="0.32em" className="run-chart-tick">
                  {formatTick(tick)}
                </text>
              ))}
            {leftSeries?.axisTitle && (
              <text transform={`translate(12 ${(top + bottom) / 2}) rotate(-90)`} textAnchor="middle" className="run-chart-tick">
                {leftSeries.axisTitle}
              </text>
            )}
            {rightSeries?.axisTitle && (
              <text transform={`translate(${width - 10} ${(top + bottom) / 2}) rotate(90)`} textAnchor="middle" className="run-chart-tick">
                {rightSeries.axisTitle}
              </text>
            )}
            {xTicks.map((tick) => (
              <text key={`x${tick}`} x={xOf(tick)} y={bottom + 16} textAnchor="middle" className="run-chart-tick">
                {tick}
              </text>
            ))}
            <line x1={left} x2={right} y1={bottom} y2={bottom} stroke={GRID} />

            {series.map((s) => {
              const y = scales[s.axis].y;
              const runs = splitRuns(s.values);
              return (
                <g key={s.label}>
                  {runs.map((run) =>
                    run.length > 1 ? (
                      <polyline
                        key={run[0]}
                        points={run.map((slot) => `${xOf(indices[slot])},${y(s.values[slot]!)}`).join(" ")}
                        fill="none"
                        stroke={s.colour}
                        strokeWidth={2}
                        strokeLinejoin="round"
                        strokeLinecap="round"
                      />
                    ) : null,
                  )}
                  {runs
                    .filter((run) => run.length === 1 || indices.length <= DOT_ALL_MAX)
                    .flat()
                    .map((slot) => (
                      <circle
                        key={slot}
                        cx={xOf(indices[slot])}
                        cy={y(s.values[slot]!)}
                        r={4}
                        fill={s.colour}
                        stroke={SURFACE}
                        strokeWidth={2}
                      />
                    ))}
                </g>
              );
            })}

            {hover !== null && (
              <g pointerEvents="none">
                <line x1={tooltipLeft} x2={tooltipLeft} y1={top} y2={bottom} stroke={AXIS_TEXT} strokeWidth={1} />
                {series.map((s) =>
                  s.values[hover] !== null ? (
                    <circle
                      key={s.label}
                      cx={tooltipLeft}
                      cy={scales[s.axis].y(s.values[hover]!)}
                      r={5}
                      fill={s.colour}
                      stroke={SURFACE}
                      strokeWidth={2}
                    />
                  ) : null,
                )}
              </g>
            )}
            <rect
              x={left}
              y={top}
              width={Math.max(0, right - left)}
              height={bottom - top}
              fill="transparent"
              onMouseMove={onMove}
              onMouseLeave={() => onHover(null)}
            />
          </svg>
        )}
        {hover !== null && width > 0 && (
          <div
            className="run-chart-tooltip"
            style={tooltipLeft > width / 2 ? { right: width - tooltipLeft + 10 } : { left: tooltipLeft + 10 }}
          >
            <div className="run-chart-tooltip-title">Image {indices[hover]}</div>
            {series.map((s) => (
              <div key={s.label} className="run-chart-tooltip-row">
                <span className="run-chart-key" style={{ background: s.colour }} />
                {s.label}
                <span className="run-chart-tooltip-value">
                  {s.values[hover] !== null ? s.format(s.values[hover]!) : failed[hover] ? "failed" : "—"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Slots of consecutive non-null values, so a failed image breaks the line instead of being
// bridged over.
function splitRuns(values: (number | null)[]): number[][] {
  const runs: number[][] = [];
  let current: number[] = [];
  values.forEach((value, slot) => {
    if (value === null) {
      if (current.length) runs.push(current);
      current = [];
    } else {
      current.push(slot);
    }
  });
  if (current.length) runs.push(current);
  return runs;
}

function axisScale(series: Series[], top: number, bottom: number) {
  const values = series.flatMap((s) => s.values.filter((v): v is number => v !== null));
  if (!values.length) return { ticks: [] as number[], y: (_: number) => bottom };
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const ticks = niceTicks(min, max, 4);
  const lo = Math.min(ticks[0], min);
  const hi = Math.max(ticks[ticks.length - 1], max);
  return { ticks, y: (value: number) => bottom - ((value - lo) / (hi - lo)) * (bottom - top) };
}

// Round-number ticks covering [min, max]: steps of 1, 2 or 5 times a power of ten.
function niceTicks(min: number, max: number, count: number): number[] {
  const span = max - min || 1;
  const raw = span / count;
  const power = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 5, 10].map((m) => m * power).find((s) => s >= raw) ?? 10 * power;
  const ticks: number[] = [];
  for (let tick = Math.floor(min / step) * step; tick <= max + step * 1e-9; tick += step) {
    ticks.push(Number(tick.toFixed(10)));
  }
  if (ticks[ticks.length - 1] < max) ticks.push(Number((ticks[ticks.length - 1] + step).toFixed(10)));
  return ticks;
}

function formatTick(value: number): string {
  return Math.abs(value) >= 100 || Number.isInteger(value) ? value.toFixed(0) : String(Number(value.toPrecision(3)));
}
