# ADR: stateless localizer architecture

Status: Proposed. The open questions below are unresolved. A future session
interviews the operator to close them, a session after that turns this record
into an execution plan, and a further session implements it. The interview
rulings land here as a "Resolved" section, and the execution plan lands beside
this file as a `PLAN-` document, following the pg-schema-diff precedent.

This record supersedes six design notes deleted from `design/` in the commit
before this one:

- `relocalization-redesign.md`
- `relocalization-multi-hypothesis-plan.md`
- `relocalization-filter-findings.md`
- `relocalization-filter-rewrite.md`
- `relocalization-false-lock-diagnosis.md`
- `relocalization-scale-mismatch-diagnosis.md`

Anything from those notes an implementer would otherwise rediscover the hard
way is carried in "Salvaged knowledge" below. Linear tickets that linked those
blobs should repoint here.

## Decision

All relocalization inference moves into the localizer. The localizer stays
stateless: every request carries the full context it needs, the server holds no
session state, and the request contract doubles as the native function
signature and eventually the on-device call.

Four commitments, in order:

1. **Push everything into the localizer, in Python, stateless.** Multi-cluster
   solving, multi-hypothesis adjudication over request-carried history, fusion,
   and per-device intrinsics refinement all land in the localizer behind the new
   request contract. Python is the iteration language for this phase because the
   fusion semantics are not yet validated against field data.
2. **Port the localizer internals to a native language.** C++ or Rust, decided
   when the port starts. The Python service shell (Litestar, S3, map cache)
   stays. External behavior is identical, proven by tolerance-based replay of a
   golden corpus through both implementations, not by bitwise comparison.
   RANSAC is randomized and torch kernels differ numerically across builds, so
   bitwise parity is not a real bar.
3. **Ship the same native module as a client-side module.** The client
   downloads maps and runs localization locally through the same logic the
   server runs. Maps are tiled so a client holds only the shards near it.
4. **Replace the current Unity package.** The package, including the client EKF
   filter, is deleted and rebuilt as a thin client: camera provider, VIO feed,
   map and tile cache, history store, and a renderer-side extrapolator that
   applies server or local-module fixes to the live VIO pose. The replacement
   scope is worked out in the execution plan, not here.

Calibration joins the program as a rebuild, not a retrofit. The recorded corpus
infrastructure (the `localization_evaluations` table, the held-out frame
selectors, the fit script) is the half-built foundation to complete. One corpus
serves three customers: calibration fit, native-port parity, and regression.

The client-versus-server split is a per-deployment choice, not a scale law.
Tiled maps remove map size as the deciding variable. Thin clients against a
serving localizer and thick clients running the local module both speak the
same request contract, which is what makes the choice expressible at all.

## The request contract

The contract is the load-bearing artifact of the whole program. It is designed
as a function signature first, because it will literally become one.

Request:

- **Camera intrinsics** with provenance (factory, borrowed default, or
  Placeframe-refined). The server's refinement policy keys off the provenance:
  trust factory values, refine aggressively against borrowed ones.
- **The query image.**
- **The device VIO pose for that image.** The server consumes relative motion
  only. Absolute VIO coordinates carry no information, and the contract must
  say so, because a VIO world frame is arbitrary and drift-accumulating.
- **An optional history array of prior raw fixes.** Each entry carries the
  server-returned fix for a past frame, never the client-filtered pose, plus
  the VIO pose at that frame, the timestamp, the map id, and the covariance the
  server returned. Sending filtered poses back would make the server re-count
  information it already produced.

Response:

- **Pose fixes with explicit semantics.** Every response states whether it is a
  raw per-frame measurement or an already-fused posterior. A client that feeds
  a fused posterior into its own filter double-counts silently, so this is a
  contract field, not an implementation detail.
- **Measurement covariance**, as today.
- **Optionally multiple pose candidates** for the multi-hypothesis consumer.
- **Optionally a refined intrinsics estimate** with a quality signal, which the
  device persists and echoes back as its provenance-carried intrinsics on
  later requests.

The stateless shape is what makes the module portable. When the client runs the
localizer locally, the request becomes an in-process call with local state
passed as data, and the history array is just the client's own record. No
session plumbing exists anywhere.

The same contract closes the intrinsics gap on devices where the platform
exposes nothing, which is the current Android XR situation. The refinement
logic lives in the localizer, runs server-side first, runs on-device later,
and the device persists the estimate. A camera provider ships a borrowed
default and converges from there. Single-frame focal recovery is weakly
observed, the dolly ambiguity, so the solve aggregates across the history
rather than trusting one frame. Known-baseline multi-view constraints from
VIO make the solve well conditioned within a single request. The principal
point stays unrefined, matching both the map-builder precedent
(`ba_refine_focal_length=True`, `ba_refine_principal_point=False`) and the
rectified-stream reality of the delivered images.

## Salvaged knowledge

Empirical facts, failure catalogs, and design rulings carried forward from the
superseded notes. Field numbers come from demo-site runs at walking pace
against a 228-image courtyard map, unless stated otherwise.

### Field-measured facts

- **Perceptual aliasing produces 22-25 m teleports with high confidence.** The
  two largest observed snaps carried `confidence_tight` of 0.58 and 0.90.
  Confidence is a monotonic function of inlier count under the deployed
  artifact, `sigmoid(1.2 * log1p(num_inliers) - 5.5)`, so it measures texture
  density, not correctness. Observed range 0.255-0.950, mean 0.719.
- **ARFoundation outdoor monocular VIO underreports motion by about 7%.** The
  scale ratio is 0.93 median, flat across the whole map, with near-zero spatial
  correlation. That offset signature, plus a map baseline confirmed at
  119.97 mm against a 120 mm factory spec, rules out map warp and global map
  scale error. The bias is the device. Stereo-tracker devices are expected to
  sit near 1.0.
- **VIO drift at walking pace (1.4 m/s):** 14-28 cm of translation drift and
  0.02-0.17 degrees of rotation over 10 s. 0.8-1.7 m and 0.1-1 degrees over
  60 s. 4-8 m and 0.5-5 degrees over 5 minutes. Alignment must update
  continuously or content peels off the world.
- **Retrieval is spatially incoherent on hard queries.** Spans of 12-24 m on
  nearly every query, with retrieved image sets flip-flopping between disjoint
  regions at roughly 1 s cadence while the device stood still. Each individual
  PnP solve is internally clean (0.95-0.99 confidence, thousands of inliers),
  which is why per-solve confidence never flags it.
- **Snapping behaves badly without cooldown.** Observed snap magnitudes were
  mostly 0.66-2.33 m with two above 22 m, and snap ping-pong at 5 s intervals
  after rejection cascades. A distance-base VIO anomaly threshold of 0.5 m sits
  inside the legitimate noise band: accepted residuals reach 0.58 m and the
  anomaly bottom quartile starts at 0.50 m.
- **All Pixel 9 camera configs run 30 fps.** Maximum resolution costs no frame
  rate, so resolution-over-fps selection is not a scale-bias mechanism on that
  hardware. The camera-config probe that established this stays in the build
  as a tripwire for devices that do expose an fps split.
- **Sun angle moves inlier counts 30-50% over a two-hour shift.** Map recapture
  at deployment lighting is the source-level fix for aliasing-prone viewpoints.
  No filter fully replaces it.

### The aliasing mechanism fork

Two mechanisms produce confident-wrong poses, and they have different fixes:

- **Mechanism A, multi-modal retrieval.** Retrieval straddles two look-alike
  regions, both contribute correspondences, RANSAC commits to the wrong one.
  The retrieval span is large. Visible within a single frame, so per-cluster
  solving and span rejection fix it server-side.
- **Mechanism B, clean retrieval of the wrong region.** The query descriptor is
  simply closest to the wrong look-alike. The retrieval span is small. No
  single-frame analysis can catch it. Motion across frames is the only
  discriminator: a wrong fix predicts future fixes badly as the user moves.

The field data that would say which mechanism dominates was never collected,
because the retrieval set was not logged and the frames were not persisted.
The retrieval-span logging that fixes this was added but never redeployed. The
fork stays open and gates how much per-cluster solving matters.

This decision changes one thing about the fork. The old claim was that only a
client-side filter could catch Mechanism B, because the server saw one frame at
a time. With history in the request, the server runs motion-consistency checks
too. The claim was an artifact of the old contract, not a law.

### Failure catalogs the new machinery must not repeat

The four structural bugs of the old single-Gaussian EKF:

1. Rejection-inflate recovery. After gate rejections the covariance diagonal
   grew until the gate re-admitted anything, matrix-incoherent and not
   guaranteed PSD. The correct shape is N consecutive rejections triggering an
   explicit reset.
2. Posterior-based snap test, backwards. The posterior shrinks after each
   update, so refinements read as surprising and snap. The test belongs on the
   prior, "is this shift surprising given what we knew before."
3. Dimensionally wrong VIO drift model. Translation drift is distance
   proportional, rotation drift is time proportional (standing still still
   accumulates yaw), and process noise is per-second, not per-tick, so
   localization cadence changes do not silently rescale decay.
4. Fixed-duration slew. A 1 cm correction and a 30 cm correction took the same
   0.5 s, so small corrections crept and large ones flew, and at 2 Hz
   localization the display was permanently mid-slew.

The multi-hypothesis prototype failure modes:

- **Leader stickiness.** Decay applied only to non-matched hypotheses makes the
  leader's score a monotonic lifetime accumulator. Whoever wins the early
  high-motion phase is permanently ahead, and absolute-margin promotion can
  never fire. Score must mean current belief strength, a leaky integrator over
  a roughly ten-measurement window, or a recent-support-rate.
- **Capacity eviction churn.** A capped pool that evicts at seed score in the
  same batch that spawned a hypothesis guarantees a fresh correct pose dies
  before its second supporting measurement. Recent spawns need protection.
- **Duplicate-cluster flooding.** Clustering retrieved images by camera-center
  proximity misfires on center-facing captures, where keyframes ring a space
  but all observe the same central structure. Spatially dispersed clusters
  solve to the same pose within 0.2 m. The coherence signal is solved-pose
  agreement, and clusters that solve to the same pose should dedupe before
  reaching any consumer.
- **The innovation gate ate good fixes when covariance floors were wrong.** A
  single beta of 1e-3 floored rotation at 1.8 degrees and translation at 3.2
  cm, far below the real fix-to-fix scatter, and the client rejected most good
  measurements. Separate rotation and translation floors set from measured
  scatter (0.3 degrees and 20 cm, against observed 0.17 degrees and 16 cm per
  axis) fixed it. Calibration values must come from measured error
  distributions, and the deployed artifact's values are exactly that, a
  hand-tuned empirical stopgap with the fit pipeline never having run.

### Design rulings that carry forward

- **Loose coupling.** Localization output never feeds back into VIO. The client
  publishes a corrective transform on top of a read-only VIO stream. Tight
  coupling would tie tracking continuity to network cadence and give a bad
  cluster a path into catastrophic drift.
- **No freeze-on-convergence.** Two independent reasons. Aliased environments
  confirm their own wrong lock, so freezing amplifies the failure. And VIO
  drift at walking pace guarantees a frozen alignment peels off within
  seconds. Stability means smooth tracking of drift while rejecting per-shot
  noise, which is a timescale separation: smoothing well under the
  drift-visible horizon of roughly 10 s and well over the measurement period
  of roughly 0.5 s.
- **Per-hypothesis process noise is mandatory.** A shared pool lets a dormant
  correct hypothesis stay artificially tight, so the future correct
  measurements that should evict the incumbent get rejected instead. The
  anti-aliasing mechanism defeats itself.
- **Score by motion diversity, not count.** Weight each supporting measurement
  by distance traveled since the hypothesis was last supported. Ten
  confirmations standing still earn almost nothing, three across a 5 m walk
  earn strong credit. This is the correct use of the motion information, and
  under the new contract the server has it too.
- **Swap on evidence, with hysteresis.** Promotion requires a margin held over
  a dwell. The principled form is a Bayes factor of 100 (log K of 4.6,
  Jeffreys' decisive threshold) plus a precision floor on the challenger
  (translation sigma under 30 cm, rotation under 1 degree) so a broadly
  agreeing but uncertain cluster cannot win. No time-based forced publish. A
  watchdog resets state on evidence drought during motion instead of
  publishing without grounds.
- **Publish deadband keyed to perception, not uncertainty.** VIO yaw drift
  accumulates without bound over a session, so an uncertainty-shaped deadband
  either widens monotonically and stops firing or fires on every refinement. A
  perceptual-mean deadband stays well-defined for the session lifetime.
- **Tracking-discontinuity signals exist and must be consumed.** Magic Leap 2
  has first-class events (tracking-origin reset after 15 s of loss,
  localization-map callbacks). ARFoundation has none, so the signal is
  synthesized from tracking-state transitions plus a pose-delta heuristic
  (inter-frame motion beyond a physically plausible bound). The heuristic is
  the only way to tell continuous drift in Limited state from a hard reset on
  recovery.
- **Operator override carries forward permanently.** A human rescue path for a
  bad lock survives every architectural generation.
- **Calibration must precede covariance-heavy machinery.** A filter that
  weights by inverse variance weights by numbers the solver invented times a
  guess, and it launders bad covariance into confident wrong answers. This is
  the one forced ordering in the whole program: garbage covariance makes
  multi-hypothesis machinery more dangerous than the heuristic it replaces.
- **Two-reconstruction calibration recipe.** Reconstruct all frames as truth,
  reconstruct 80% as the map, localize the held-out 20%, fit covariance to
  those residuals. This is not circular: it measures how well the localizer
  lands queries in the map's own coordinate system, which is exactly what a
  user experiences. Raw VIO poses are never truth. ZED capture VIO drifts
  double-digit meters across a city block before loop closure.
- **Truth attribution is per-frame BA-refined poses.** A pairwise
  VIO-versus-VPS comparison produces scalar errors per pair, absorbs
  session-shared bias into the implicit alignment, and cannot drive a per-query
  SE(3) covariance fit. When phone sessions fail the reconstruction quality
  gate too often, the answer is better capture, not a second truth path.
- **Layered tuning, never joint.** Measurement covariance is a property of the
  localizer's output distribution and is fit by maximum likelihood against
  truth residuals. Filter thresholds are a property of how the consumer should
  react to that distribution and are picked by corpus replay. Reconstruction
  options shape the input distribution. Treating one layer's outputs as
  another layer's knobs produces values chosen to flatter the replay score.
- **Feature-conditional covariance floor.** The floor expands to
  `beta0 + sum(w_i * feature_i)` over five per-query features (log inliers,
  inlier ratio, normalized reprojection error, inlier coverage, log matches),
  fit by L1-regularized maximum likelihood with cross-validated lambda. L1
  because three of the five features derive from the same two integers and an
  unregularized fit produces nonsense weights that still score fine. Per-map
  features are excluded, they describe the map and not the measurement, which
  is a category error in a per-measurement noise model.
- **Per-map character is handled by mechanism, not tuning.** Long-corridor
  maps spawn more hypotheses, aliasing-prone maps require more evidence to
  swap, sparse maps get wider covariance through the feature-conditional fit.
  Per-map data is a diagnostic that says "rebuild this map with better
  options," never a per-map filter configuration.
- **The bootstrap corpus is explicitly throwaway.** Held-out ZED frames
  characterize rig imagery against rig-built maps with rig-grade VIO, a
  different distribution on every axis from deployment. When field data
  arrives the calibration is replaced wholesale, never warm-started from the
  bootstrap fit.
- **VPS queries run at 0.5-2 s cadence.** The renderer always needs high-rate
  local fusion, so a server-side or module-side authoritative estimate still
  lands on a client that extrapolates from fix timestamps through live VIO.
  The client is never fully dumb, latency alone forbids it.
- **Map-agnostic measurement intake.** Fix consumers work in ECEF-frame terms
  regardless of source map, so multi-map and tiled operation later needs no
  re-architecture of the estimator, only a handoff rule.
- **Axis convention is a tag, not a dispatch.** The math boundary works in
  OpenCV convention. Engine glue converts at the boundary.
- **Test conventions by failure class.** Lie-algebra primitives get
  convention-targeted tests where each test fails for a specific error class:
  row-major versus column-major, handedness, quaternion component order,
  product order, adjoint identity, small-angle series behavior. Primitive
  tests red means a math bug, primitives green with behavioral tests red means
  an architecture bug. No bit-parity against any previous implementation.

### Instrumentation gaps that stay open

- VIO and tracking-state transitions were never logged client-side, so "did
  tracking drop during the divergence" is unanswerable from existing data.
- Camera world position per measurement was never logged, so "drifted away"
  was never measurable in ground meters.
- The query frames are not persisted server-side and the retrieval set was
  discarded mid-pipeline, so the A-versus-B fork cannot be resolved
  retroactively. The corpus infrastructure this program builds closes all
  three gaps by construction if it records requests and responses.

## Superseded alternatives

- **The portable C# filter library.** A `Placeframe.Filter` DLL shared by
  Unity and a .NET replay harness, with one implementation of the filter math
  and a Python port foreclosed. The native module serves the
  single-implementation goal better: one codebase, two hosts. The replay
  harness idea survives as the Python corpus replay that the parity and
  calibration work already need.
- **The client-side multi-hypothesis bank as the destination.** Prototyped
  off-mainline and not merging. Its purpose moves server-side under the
  history-carrying contract, and its failure modes are cataloged above so the
  server-side machinery does not repeat them.
- **A backend-stateful session.** The server remembering per-device history.
  Foreclosed. It would force the anonymous-identity header to become
  load-bearing in anonymous deployments, add a database on the request hot
  path, and break under localizer replicas and restarts. History rides the
  request.
- **Server-side confidence gating.** The rejection gate on
  `confidence_loose` / `confidence_tight` is removed rather than completed. The
  hypothesis machinery subsumes "is this measurement useful" with strictly more
  context. Confidence stays a pure diagnostic.

## Open questions

A question is listed only if the architecturally correct answer is genuinely
ambiguous or the question is about intended behavior. Everything else is
engineering with a derivable answer.

**Response semantics**

1. Does the server return an authoritative fused posterior, making the client
   a pure VIO extrapolator between fixes, or a refined per-frame measurement
   that a client-side filter consumes? Both are coherent. They imply different
   client rewrites, and the contract must pick one and say so on every
   response.

2. What is the multi-hypothesis response shape? A candidates array per map, or
   one adjudicated winner with the alternatives as diagnostics? How does the
   transition-era client, still running the old EKF, consume it?

3. Is the A-versus-B field-data collection still required before investing in
   per-cluster solving, or does history-based motion adjudication make the
   fork moot by defending both mechanisms?

**The history contract**

4. Window size and entry fields. How many entries, and does each carry the
   returned covariance and confidence or just the pose pair? Is the window
   time-boxed, count-boxed, or distance-boxed?

5. Multi-map behavior. Does one history span map switches, with entries
   carrying map ids, or is history per-map and reset on switch?

6. VIO scale handling. The server receives VIO deltas that are 7% short on
   monocular phones and presumably metric on stereo trackers. Does the server
   estimate scale jointly with alignment, the server-side analog of the
   per-session EMA compensation that was prototyped, or does the contract
   carry a per-platform scale-trust declaration? What happens to the estimate
   when a monocular phone and a stereo headset share one device identity?

**Intrinsics**

7. Refinement policy. When does the server refine, how does it aggregate
   across requests and maps, and what quality bar must an estimate clear
   before the response carries it? Is the refined value per-device only, or
   also per-map?

8. Provenance vocabulary. What are the enum values and their exact server-side
   behaviors? Does the contract distinguish a borrowed default from a
   Placeframe-refined value from factory calibration, and does a refined value
   carry its sample count and confidence?

**Calibration rebuild**

9. Is the current hand-tuned artifact the behavioral baseline the rebuild must
   not regress, or is its gating behavior itself up for redesign?

10. What quality signals does the rebuilt calibration produce for the new
    response fields, per-candidate confidence and intrinsics estimates, which
    have no calibration story today?

11. Does the pipeline-version pinning discipline, dormant today under the
    placeholder sentinel, get rebuilt as designed, keyed to the localizer
    image hash, or redesigned around the corpus that now also serves parity?

**Native port**

12. C++ or Rust? The deciding input is the ratio of new logic to glue. The
    kernel ecosystem, libtorch, FAISS, COLMAP, is C++ and calls directly from
    C++, while Rust buys memory safety at the cost of FFI bridges. Client-side
    delivery through Unity P/Invoke works with either. Decided at port start,
    not before.

13. When does the port start? The correct trigger is behavioral validation of
    the Python pipeline against field data, not a date. Porting before the
    fusion semantics survive the field means porting twice.

**Client replacement and tiles**

14. What survives the Unity package replacement? The auth handlers have a
    documented twin in lbe-toolkit that must stay mirrored until lbe-toolkit
    depends on this package instead. The `ICameraProvider` shape, the camera
    config observable, the frame contract, all have successors in the thin
    client. Which exact surfaces carry over, which get redesigned, and what is
    the migration story for the two existing consumers?

15. Tile-selection bootstrap. The headset has no GNSS. Candidates: a coarse
    hierarchical retrieval pass against a city-level index, WiFi or IP
    geolocation, user venue selection, or last-known position. Which is the
    intended path, and is a GPS-free bootstrap a requirement or a nice-to-have?

16. Tile handoff. Crossing a tile seam needs a re-anchoring rule and overlap
    policy. What is the intended continuity behavior, and how much tile
    overlap does it require?

17. Artifact versioning. Old clients with old tiles and old calibration
    constants. What compatibility does the map distribution contract promise,
    and does the calibration artifact travel with the map or the module?

**Sequencing**

18. Does the Aura camera provider land before the API change, running against
    the current endpoint with a borrowed intrinsics profile, or does
    everything wait for the new contract? The provider work is independent,
    the intrinsics convergence is not.

19. Is bootstrap aliasing, wrong lock at first fix, a real observed failure
    mode that needs a refuse-to-commit rule before evidence accumulates, or
    is it covered by the same machinery as mid-session aliasing?

## Consequences

- The localizer's build context, the `LOCALIZER_SHA` calibration coupling,
  is dormant in production today and the calibration refit cost of pipeline
  churn is currently zero. It becomes a real cost again the moment the rebuilt
  calibration ships, and the rebuild should treat that discipline as a design
  input, not a standing constraint.
- `workloads/localizer/AGENTS.md` describes the deployed calibration artifact
  as the pre-stopgap placeholder, which is factually two levels stale. Doc
  reconciliation is part of the implementation, and the execution plan should
  carry it explicitly.
- The deployed hand-tuned gates, the loose gate near 38 inliers and the
  separate rotation and translation covariance floors, are load-bearing
  production behavior that exists to stop a real failure mode. The rewrite
  measures itself against that behavior rather than silently modernizing it.
- The walking-pace pedestrian (1.4 m/s) remains the primary design point.
  Vehicle-mounted and room-scale are not design points.
- Map recapture at deployment lighting remains the source-level fix for
  aliasing-prone viewpoints, and no amount of filter or contract work
  replaces it.
