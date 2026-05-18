# Innovation, gate, Kalman, slew — ELI5 (with hand-holding)

A walkthrough of `RelocalizationFilter.ApplyMeasurement` and its helpers. Every code reference is to `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` or `Se3.cs`.

The filter's job, in one sentence: keep a running best-guess transform `T_unityFromEcef` ("the map's pose in Unity world"), update it whenever the server returns a new measurement, and never let a bad measurement yank the world.

The big-picture vocabulary:

- **Mean (`AlignmentMean`)**: the filter's current best guess for `T_unityFromEcef`.
- **Covariance (`AlignmentCovariance`)**: how unsure we are about that guess, expressed as a 6×6 matrix in "tangent space" (more on that in a minute).
- **Measurement (`measurementMean`, `sigmaMeas`)**: what the server just told us, plus how confident the server says it is.
- **Innovation**: the disagreement between mean and measurement, with a confidence assessment.
- **Gate**: a "is this disagreement too crazy to believe?" check.
- **Kalman update**: the formula that mixes mean and measurement in proportion to their respective confidences.
- **Slew**: don't snap the world — animate the visible transform smoothly toward the new mean.

We'll do these in order.

---

## Setting the stage: tangent space, because rotations don't add

A 3D pose lives in a thing called **SE(3)** — Special Euclidean group, 6 DOF (3 rotation + 3 translation). The frustrating thing about SE(3) is that you can't just add two poses or take their difference like you would with vectors. Rotating "30° about X" and then "30° about Y" is **not** the same as "30° about X plus 30° about Y" — rotations don't commute.

That's a problem for a Kalman filter, which is built on the assumption "I can subtract estimate from measurement to get a residual, and add a correction to my estimate." Subtraction and addition don't work on SE(3) directly.

The trick is to do all the math in a flat 6-dimensional vector space that locally approximates SE(3) — the **Lie algebra** `se(3)`, also called the **tangent space at the identity**. Two functions move you between the curved manifold (SE(3), `double4x4`) and the flat space (`se(3)`, `Vector<double>` of length 6):

- `Se3.Log(T)`: takes a 4×4 transform, returns a 6-vector "this much rotation, this much translation away from identity." Called `ξ` (xi) in the literature.
- `Se3.Exp(ξ)`: takes a 6-vector, returns a 4×4 transform.

The 6-vector ordering used here (`Se3.cs:8-9`): `(ω_x, ω_y, ω_z, ρ_x, ρ_y, ρ_z)` — **rotation first** (three components of a rotation-axis-times-angle vector), then translation. This ordering matches what pycolmap's PnP solver emits for its covariance matrix, so the filter can ingest `Σ_meas` byte-for-byte without reshuffling.

Why does this matter for the rest of the document? Because **the residual, the covariance, and the Kalman gain are all 6-vectors and 6×6 matrices in tangent space**, not 4×4 transforms. The mean lives on the manifold (`double4x4`); the uncertainty about the mean lives in the tangent space.

---

## Step 1 — `ApplyMeasurement` orchestration (lines 99–168)

Top of the function (lines 105–111):

```csharp
var metrics = localizationResult.Metrics;
var measurementMean = ComputeAlignmentFromResult(localizationResult, frame);
var sigmaMeas = BuildCovarianceMatrix(metrics.MeasurementCovariance);
var currentVioPosition = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;
var sigmaPredicted =
    state.AlignmentCovariance + ProcessNoise(currentVioPosition, state.LastAcceptedVioPosition);
var innovation = ComputeInnovation(state.AlignmentMean, sigmaPredicted, measurementMean, sigmaMeas);
```

Three things happen here, all setup:

1. **Compose the measurement.** `ComputeAlignmentFromResult` turns "the server thinks the camera is here in the map" plus "the device thinks the camera is here in Unity world" into a single proposed `T_unityFromEcef`. This is the same kind of object as `AlignmentMean` — a 4×4 SE(3) transform.

2. **Inflate the prior covariance.** The filter's stored `AlignmentCovariance` is the uncertainty *as of the last measurement*. Between then and now, the VIO has drifted some. We can't go back and "shrink the mean" to fix the drift — but we can *grow the covariance* to reflect "we're more uncertain than we used to be." That's `sigmaPredicted = AlignmentCovariance + ProcessNoise(...)`. The result is the **predicted** covariance — what we believe right before seeing the new measurement.

3. **Compute the innovation.** This is where the disagreement gets quantified. Covered in detail below.

Then:

```csharp
if (innovation.MahalanobisSquared > Chi2_99_6dof)
    return ...; // rejected
```

The **gate**. If the disagreement is statistically implausible given how confident we are, reject. Detail below.

Then:

```csharp
var posterior = KalmanUpdate(...);
```

The **Kalman update**. Mix prior and measurement. Detail below.

Then the snap-vs-slew branch (lines 137–161): is the new posterior so far from where the camera is currently rendering things that we should jump, or do we animate over the slew duration?

Each piece in turn.

---

## Step 2 — Process noise (lines 218–243)

The filter has two sources of uncertainty growth between measurements:

```csharp
var noise = Matrix<double>.Build.DenseOfDiagonalArray(new[] {
    BaseProcessNoiseRotationVariancePerTick,    // ω_x
    BaseProcessNoiseRotationVariancePerTick,    // ω_y
    BaseProcessNoiseRotationVariancePerTick,    // ω_z
    BaseProcessNoiseTranslationVariancePerTick, // ρ_x
    BaseProcessNoiseTranslationVariancePerTick, // ρ_y
    BaseProcessNoiseTranslationVariancePerTick, // ρ_z
});
```

This is the **baseline floor**. Even if the device hasn't moved at all, we add `1e-6 rad²` of rotation variance and `1e-4 m²` of translation variance per measurement. Why? The comment at lines 57–63 spells it out: without a noise floor, the Kalman update keeps shrinking `Σ_posterior` indefinitely. After ~30 stationary measurements the filter becomes so overconfident in its prior that any new measurement gets rejected by the gate. The base noise prevents that lockup.

Then the motion-proportional term (lines 239–242):

```csharp
var deltaTranslation = math.length(currentVioPosition - lastAcceptedVioPosition.Value);
var sigma = DriftPerMeter * deltaTranslation; // 0.01 * distance
var motionVariance = sigma * sigma;
return noise + Matrix<double>.Build.DenseDiagonal(6, 6, motionVariance);
```

The model: every meter the device walked, the VIO probably drifted by about 1 cm of translation and 0.01 rad ≈ 0.57° of rotation (`DriftPerMeter = 0.01` is the σ per meter). Squared because covariance is in units of variance. Added to all 6 diagonals — yes, including rotation, which is a simplification noted in the comment.

The end-result `sigmaPredicted` says: "given how much we've moved since the last accepted measurement, here's how unsure we now are about `T_unityFromEcef`."

---

## Step 3 — Innovation (lines 313–328)

```csharp
public static Innovation ComputeInnovation(
    double4x4 currentMean,
    Matrix<double> sigmaPredicted,
    double4x4 measurementMean,
    Matrix<double> sigmaMeas
)
{
    var residual = Se3.Log(math.mul(math.inverse(currentMean), measurementMean));
    var innovationCov = sigmaPredicted + sigmaMeas;
    return new Innovation
    {
        Residual = residual,
        Covariance = innovationCov,
        MahalanobisSquared = MahalanobisSquared(residual, innovationCov),
    };
}
```

Three pieces. ELI5 each.

### 3a. The residual

`Se3.Log(currentMean⁻¹ · measurementMean)`. Read right-to-left:

- `currentMean⁻¹ · measurementMean`: the SE(3) transform that, when composed onto the current mean, gives the measurement. "What rotation+translation moves you from where I think the map is, to where the measurement says the map is?"
- `Se3.Log(...)`: flatten that little SE(3) transform into a 6-vector in tangent space. Now you have a vector — addable, subtractable, scalable.

If the mean and measurement agree perfectly, the residual is the zero vector. If they disagree, the components tell you in what direction and by how much, in `(ω_x, ω_y, ω_z, ρ_x, ρ_y, ρ_z)` order.

This is **the Kalman "y − Hx" term**, generalized to SE(3). On a flat vector space you'd just write `measurement − estimate`. On SE(3) you have to do "estimate⁻¹ · measurement, then Log."

### 3b. The innovation covariance

`innovationCov = sigmaPredicted + sigmaMeas`.

Two sources of uncertainty, both 6×6 matrices in tangent space, added:

- `sigmaPredicted`: how unsure we are about the *prior estimate* (after process-noise inflation).
- `sigmaMeas`: how unsure the *server is about its measurement*, as reported by pycolmap's PnP covariance.

Adding them gives the total uncertainty *of the residual itself*. If the prior is fuzzy (`sigmaPredicted` big) or the measurement is noisy (`sigmaMeas` big), we expect the residual to be bigger by chance even when nothing is wrong.

This is the key insight that makes the next step work: we're not asking "is the residual big in absolute terms?" — we're asking "is the residual big *relative to how big it could plausibly be just from noise*?"

### 3c. Mahalanobis squared (lines 245–250)

```csharp
public static double MahalanobisSquared(Vector<double> residual, Matrix<double> covariance)
{
    var inv = covariance.Inverse();
    var product = inv * residual;
    return residual.DotProduct(product);
}
```

In math: `d² = rᵀ · Σ⁻¹ · r`. This is the **squared Mahalanobis distance** of the residual against its own covariance.

ELI5: it's "how many σ is this residual, in 6D, accounting for the covariance shape?" Imagine the covariance as an ellipsoid in 6D space — wide in some directions, narrow in others. The Mahalanobis distance is "if I draw a line from the origin to the residual, how many ellipsoid-radii does that line cross?" A residual of 2 m might be 1σ if the ellipsoid is huge along that axis, or 50σ if the ellipsoid is tiny along that axis.

Because `r` is 6D, `d²` follows a chi-squared distribution with 6 degrees of freedom when the model is correct. That gives us a principled threshold for "this residual is bigger than noise would explain."

---

## Step 4 — The gate (lines 113–122, 47)

```csharp
public const double Chi2_99_6dof = 16.81;
...
if (innovation.MahalanobisSquared > Chi2_99_6dof)
    return new StepResult { ..., Rejection = MeasurementRejection.InnovationGate, ... };
```

`16.81` is the **99th percentile of χ²(6)**. If everything in our model is correctly calibrated and the measurement is honest, the squared Mahalanobis distance of the residual should exceed 16.81 only **1% of the time** by random chance.

So the rule is: if `d² > 16.81`, the measurement is in the unlucky 1% tail *or* something is genuinely wrong (PnP outlier, VIO jump, mis-modeled covariance). Either way, we'd rather drop it than risk corrupting the alignment.

Why 99% and not 95% or 99.9%? Trade-off:

- Tighter gate (95% = 12.59): rejects more measurements; more conservative; recovers more slowly from a stale prior.
- Looser gate (99.9% = 22.46): accepts more measurements; vulnerable to outliers; more permissive of bad PnPs.

99% is the conventional middle ground in robotics SLAM filters. The constant is tagged to be re-tuned in Phase 3 once `σ_meas` is empirically fit (line 63 comment).

---

## Step 5 — The Kalman update (lines 330–342)

This is the heart of the filter — where prior and measurement actually combine.

```csharp
public static PosteriorUpdate KalmanUpdate(
    double4x4 currentMean,
    Matrix<double> sigmaPredicted,
    Vector<double> residual,
    Matrix<double> innovationCovariance
)
{
    var kalmanGain = sigmaPredicted * innovationCovariance.Inverse();
    var residualUpdate = kalmanGain * residual;
    var newMean = math.mul(currentMean, Se3.Exp(residualUpdate));
    var newCov = (Matrix<double>.Build.DenseIdentity(6) - kalmanGain) * sigmaPredicted;
    return new PosteriorUpdate { NewMean = newMean, NewCovariance = newCov };
}
```

Line by line.

### 5a. The Kalman gain

```csharp
var kalmanGain = sigmaPredicted * innovationCovariance.Inverse();
```

In math: `K = Σ_predicted · (Σ_predicted + Σ_meas)⁻¹`.

This is a 6×6 matrix that says, per tangent dimension, "**how much of the residual should I move my estimate by?**" Each row/column corresponds to one of the 6 tangent dimensions.

Intuition with a scalar example. Suppose `σ²_predicted = 4` (prior is sloppy) and `σ²_meas = 1` (measurement is precise). Then:

```
K = 4 / (4 + 1) = 0.8
```

You move 80% of the way toward the measurement. The precise measurement gets most of the weight.

Flip it: `σ²_predicted = 1`, `σ²_meas = 100` (measurement is garbage):

```
K = 1 / (1 + 100) ≈ 0.01
```

You barely budge. The prior is much more trustworthy.

The matrix version generalizes this per-dimension and accounts for cross-correlations between dimensions (e.g. translation-x being correlated with rotation-z). For diagonal covariances it reduces to per-component reweighting; for the full 6×6 case it can rotate the residual through coupled axes.

This is the **classic Kalman gain identity**. In standard textbook notation `K = P · Hᵀ · (H · P · Hᵀ + R)⁻¹`, and because our measurement is a direct observation of the state (`H = I` in tangent space — see the box at the end), it collapses to `K = Σ_predicted · (Σ_predicted + Σ_meas)⁻¹`.

### 5b. The residual update

```csharp
var residualUpdate = kalmanGain * residual;
```

A 6-vector. "Here is the correction, in tangent space, that I'm going to apply to my mean."

If `K` is close to identity, `residualUpdate ≈ residual` (snap fully to measurement).
If `K` is close to zero, `residualUpdate ≈ 0` (ignore measurement).

### 5c. Lifting the correction back to SE(3)

```csharp
var newMean = math.mul(currentMean, Se3.Exp(residualUpdate));
```

The correction is in tangent space (6-vector). The mean lives on SE(3) (4×4 matrix). To apply the correction, we Exp it back to a 4×4 transform and **right-multiply** the current mean by it.

Right-multiply, not left-multiply. Why? Because the residual was computed in the **frame of the current mean** (`currentMean⁻¹ · measurementMean` — read as "expressed relative to currentMean"). Applying a small correction in the local frame means composing it on the right: `newMean = currentMean · Exp(correction)`. This is the SE(3) generalization of "add the correction to the mean" on flat vector spaces.

If the gain were exactly identity, the algebra works out to `newMean = measurementMean` exactly. Snap to measurement. If the gain were exactly zero, `Exp(0) = identity`, so `newMean = currentMean`. Ignore measurement. In between, you blend.

### 5d. The new covariance

```csharp
var newCov = (Matrix<double>.Build.DenseIdentity(6) - kalmanGain) * sigmaPredicted;
```

In math: `Σ_new = (I − K) · Σ_predicted`.

ELI5: every time we accept a measurement, we get *more certain* — covariance can only shrink (or stay the same) on an accepted update. The factor `(I − K)` is "how much uncertainty survives." If `K` is big (we trusted the measurement a lot), `(I − K)` is small (lots of uncertainty got crushed). If `K` is tiny (we barely listened), `(I − K) ≈ I` (uncertainty almost unchanged).

This is the **Joseph form's simpler cousin**, and is numerically less robust than the full `(I − K)·Σ·(I − K)ᵀ + K·R·Kᵀ` form. In single-precision it can lose symmetry over time. For double precision and 6×6 matrices with reasonable conditioning it's fine — the codebase has it as the v1 simple form.

This is **the part that prevents lockup**, paired with the process noise. Without process noise, `Σ_new` shrinks monotonically and eventually nothing fits the gate. With process noise added every step, `Σ_predicted = Σ_new + ProcessNoise` re-inflates, keeping the filter responsive.

---

## Step 6 — Snap vs slew (lines 137–161)

The Kalman update produced a new posterior mean. But the **rendered transform** (`AlignmentCurrent`) doesn't immediately jump — that would teleport the user's world. Instead, we usually animate from `AlignmentCurrent` toward the new posterior over half a second.

```csharp
var shouldSnap = !state.HasAcceptedMeasurement;
if (!shouldSnap)
{
    var shiftMagSquared = ShiftMagnitudeSquared(
        state.AlignmentCurrent,
        posterior.NewMean,
        posterior.NewCovariance
    );
    shouldSnap = shiftMagSquared > SnapThresholdSigmasSquared;
}
```

Two reasons to snap instead of slew:

1. **First-ever measurement** (`!HasAcceptedMeasurement`). The bootstrap covariance is enormous (`σ = π` for rotation, `100 m` for translation — lines 67–68); the snap-vs-slew distance metric below would be ill-conditioned against a near-singular `Σ_new` on the first update. So just snap and move on.

2. **The new posterior is more than `√36 = 6σ` away from where we're rendering.** That uses `ShiftMagnitudeSquared` (lines 344–348), which is *another* Mahalanobis distance — this time of "log(AlignmentCurrent⁻¹ · NewMean)" against `Σ_new`. If the shift is huge (6σ is wildly significant statistically), animating over half a second would be a slow visible drift. Better to snap and let the user mentally re-anchor.

If neither condition fires, slew:

```csharp
newState.SlewStart = state.AlignmentCurrent;
newState.SlewProgress = 0f;
```

The actual animation happens in `TickSlew` (lines 171–185), called once per frame from `VisualPositioningSystem`:

```csharp
newState.SlewProgress = math.min(1f, state.SlewProgress + deltaSeconds / SlewDurationSeconds);
var t = SmoothStep(newState.SlewProgress);
newState.AlignmentCurrent = Double4x4.Interpolate(state.SlewStart, state.AlignmentMean, t);
```

`SmoothStep(t) = t² · (3 − 2t)` (line 252) is the classic Hermite ease-in-ease-out curve. It has zero derivative at `t=0` and `t=1`, so the animation starts and ends smoothly rather than with a velocity discontinuity. Without smooth-step, half a second of constant-velocity interpolation would look like the world abruptly starts and stops sliding.

`Double4x4.Interpolate` does the right SE(3)-ish thing — slerp on rotation, lerp on translation (defined elsewhere in `Double4x4.cs`).

---

## Putting it together

A timeline of one accepted measurement:

1. **Server returns a measurement.** `MapLocalization` arrives with a `CameraFromMapTransform` and a 6×6 PnP covariance.
2. **Compose into our alignment vocabulary.** `ComputeAlignmentFromResult` produces a 4×4 `measurementMean = T_unityFromEcef` candidate.
3. **Inflate the prior.** `sigmaPredicted = AlignmentCovariance + ProcessNoise(currentVio, lastVio)`. The previous-step's certainty erodes by however much the user has walked.
4. **Compute the disagreement.** `residual = Log(currentMean⁻¹ · measurementMean)` — 6-vector. `Σ_innovation = sigmaPredicted + sigmaMeas`. `d² = rᵀ · Σ⁻¹ · r`.
5. **Gate.** If `d² > 16.81`, drop the measurement and return unchanged. Filter remembers the rejection in `StepResult` for telemetry.
6. **Compute the gain.** `K = sigmaPredicted · Σ_innovation⁻¹`. Per-dimension blending weight.
7. **Update the mean on the manifold.** `newMean = currentMean · Exp(K · residual)`.
8. **Shrink the covariance.** `Σ_new = (I − K) · sigmaPredicted`.
9. **Snap or slew?** First measurement always snaps. Otherwise, snap if `Mahalanobis(currentRendered → newMean) > √36`. Otherwise, start a 0.5 s smooth-step interpolation from currently-rendered toward new mean.
10. **Record state.** `HasAcceptedMeasurement = true`, `LastAcceptedVioPosition = currentVio`.

A timeline of a rejected measurement: steps 1–4, then return early at step 5. The filter state is unchanged except a log entry — the alignment doesn't move, the slew doesn't restart, no covariance change.

---

## Why this whole apparatus exists

If you only ever had one measurement, you'd just use it. The Kalman machinery is for the case where:

- Measurements arrive at ~1 Hz over a long session.
- Each measurement is independently noisy.
- You want each new measurement to *refine* your estimate without being whipped around by outliers.
- You want a principled way to know "how confident am I right now?" so downstream code (the snap-vs-slew branch, the UI, the gate itself) can make decisions.

The single most important number is the **Kalman gain** `K`. Everything else is plumbing to compute it correctly: `Σ_predicted` so the gain knows how much to trust the prior; `sigmaMeas` so it knows how much to trust the measurement; `Σ_innovation` because the denominator needs both; the residual because the gain has to multiply *something* to produce a correction. The gain is the answer to "how strongly does this measurement get to vote?"

And the gate is just the gain's bouncer: "before I let you vote, prove your residual isn't statistical garbage."

---

## Box: the `H = I` simplification

Standard Kalman: `K = P · Hᵀ · (H · P · Hᵀ + R)⁻¹` where `H` is the measurement model — how a state would project into measurement space.

Here, **the measurement is the state**. The server reports `T_unityFromEcef` directly (after `ComputeAlignmentFromResult`'s composition), in the same parameterization as `AlignmentMean`. So `H = I` (well, more precisely: the *Jacobian* of the measurement map evaluated at the current mean, in tangent coordinates, is the identity). That collapses the gain formula to `K = P · (P + R)⁻¹`, which is what the code computes.

This is why nothing in `KalmanUpdate` looks like an `H` matrix — it would just be `I` everywhere and cancel out. The simplification is load-bearing: if the server ever started reporting only *part* of the alignment (e.g. just translation), `H` would re-appear and the gain shape would change.

This same property also explains why the residual is just `Log(currentMean⁻¹ · measurementMean)` — there's no "project state into measurement space, subtract" step. Mean and measurement live in the same space and `Log(currentMean⁻¹ · measurementMean)` *is* the SE(3) generalization of `measurement − state`.
