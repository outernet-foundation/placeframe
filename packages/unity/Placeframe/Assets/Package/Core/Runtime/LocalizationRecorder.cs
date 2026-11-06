using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using ICSharpCode.SharpZipLib.Tar;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using PlaceframeApiClient.Model;
using R3;
using Unity.Mathematics;
using UnityEngine;

namespace Placeframe.Core
{
    // Records a localization run for studying VIO/VPS fusion offline: query images, the tracker's pose
    // for every camera frame, and what the live VPS did, all on the camera clock. Written as a folder
    // and, once stopped, a tar of it beside the folder:
    //
    //   manifest.json   type "localization_recording", camera intrinsics (full resolution), device, maps
    //   video/<t>.jpg   every camera frame (~30 fps) at 1/video_downscale resolution, for replaying the
    //                   run frame by frame; <t> its camera timestamp in ns
    //   video.csv       each video frame's timestamp and the tracker's pose when it was taken
    //   stills/<t>.jpg  a full-resolution frame every still_interval_seconds, for localizing offline:
    //                   VPS matches at a 1024 px shorter side, so a video frame would only be upscaled
    //   stills.csv      as video.csv, for the stills
    //   tracking.csv    the tracker's pose and state for every camera frame (~30 Hz)
    //   vps.jsonl       each live localization: its image's timestamp, request/response times, the
    //                   server's result and the filter's verdict
    //   vps/<t>.jpg     the image each live localization sent
    //
    // Poses are unanchored Unity world (camera from world inverse, Unity axes), as the fusion filter
    // sees them; timestamps are camera ns, with the wall clock (unix ms) alongside for the VPS log.
    public static class LocalizationRecorder
    {
        public const string ManifestType = "localization_recording";
        public const int ManifestVersion = 2;

        private static ICameraProvider _cameraProvider;
        private static string _recordingsRoot;
        private static IDisposable _subscriptions;
        private static Guid _recordingId;
        private static string _recordingDirectory;
        private static StreamWriter _videoWriter;
        private static StreamWriter _stillWriter;
        private static StreamWriter _trackingWriter;
        private static StreamWriter _vpsWriter;
        private static readonly List<Task> _pendingWrites = new();
        // Video frames encoded at once; frames beyond that are dropped.
        private const int MaxConcurrentEncodes = 3;
        // Video frames are recorded at half resolution: full-resolution encoding at 30 fps starved the
        // phone's main loop (11 fps of images, tracking down to 14 Hz on a Pixel 6 Pro).
        private const int VideoDownscale = 2;

        public static bool Recording => _subscriptions != null;
        public static int VideoFrameCount { get; private set; }
        public static int StillCount { get; private set; }
        public static int TrackingSampleCount { get; private set; }
        public static int VpsAttemptCount { get; private set; }

        public static void Initialize(ICameraProvider cameraProvider)
        {
            _cameraProvider = cameraProvider;
            _recordingsRoot = Path.Combine(Application.persistentDataPath, "LocalizationRecordings");
            Directory.CreateDirectory(_recordingsRoot);
        }

        public static Guid StartRecording(float stillIntervalSeconds, IEnumerable<Guid> mapIds)
        {
            if (_subscriptions != null)
                throw new InvalidOperationException("Recording already running");
            if (_cameraProvider is not ITrackingProvider trackingProvider)
                throw new InvalidOperationException("Recording needs a camera provider that reports every frame");

            _recordingId = Guid.NewGuid();
            _recordingDirectory = Path.Combine(_recordingsRoot, _recordingId.ToString());
            Directory.CreateDirectory(Path.Combine(_recordingDirectory, "video"));
            Directory.CreateDirectory(Path.Combine(_recordingDirectory, "stills"));
            Directory.CreateDirectory(Path.Combine(_recordingDirectory, "vps"));
            VideoFrameCount = 0;
            StillCount = 0;
            TrackingSampleCount = 0;
            VpsAttemptCount = 0;

            _videoWriter = OpenCsv("video.csv", "timestamp_ns,unix_ms,tx,ty,tz,qx,qy,qz,qw");
            _stillWriter = OpenCsv("stills.csv", "timestamp_ns,unix_ms,tx,ty,tz,qx,qy,qz,qw");
            _trackingWriter = OpenCsv("tracking.csv", "timestamp_ns,unix_ms,tracking_state,not_tracking_reason,tx,ty,tz,qx,qy,qz,qw");
            _vpsWriter = OpenCsv("vps.jsonl", null);

            var directory = _recordingDirectory;
            var maps = mapIds.ToList();
            var startedAt = DateTime.UtcNow;
            // Only the manifest needs the camera's configuration. The streams are subscribed on their own:
            // CameraConfig can complete the moment it is subscribed (a camera already running, as on a
            // Magic Leap 2), and a shared copy of it would then have finished before the streams
            // subscribed, so they would never start.
            var cameraConfig = _cameraProvider.CameraConfig();

            VisualPositioningSystem.OnLocalizationAttempt += OnLocalizationAttempt;
            _subscriptions = Disposable.Combine(
                cameraConfig
                    .Take(1)
                    .Subscribe(config => WriteManifest(directory, config, stillIntervalSeconds, maps, startedAt)),
                trackingProvider
                    .EveryFrame(MaxConcurrentEncodes, VideoDownscale)
                    .Subscribe(frame => WriteImage(frame, "video", _videoWriter, () => VideoFrameCount++)),
                _cameraProvider
                    .Frames(stillIntervalSeconds)
                    .Subscribe(frame => WriteImage(frame, "stills", _stillWriter, () => StillCount++)),
                trackingProvider.TrackingSamples().Subscribe(WriteTrackingSample),
                Disposable.Create(() => VisualPositioningSystem.OnLocalizationAttempt -= OnLocalizationAttempt)
            );
            return _recordingId;
        }

        public static Guid StopRecording()
        {
            if (_subscriptions == null)
                throw new InvalidOperationException("Recording not running");

            _subscriptions.Dispose();
            _subscriptions = null;

            _videoWriter.Dispose();
            _stillWriter.Dispose();
            _trackingWriter.Dispose();
            _vpsWriter.Dispose();
            var pending = _pendingWrites.ToArray();
            _pendingWrites.Clear();

            var id = _recordingId;
            var directory = _recordingDirectory;
            UniTask
                .RunOnThreadPool(async () =>
                {
                    // The images are written fire-and-forget; the tar has to wait for the last of them.
                    await Task.WhenAll(pending);
                    WriteTar(directory, TarPath(id));
                })
                .Forget();
            return id;
        }

        public static IEnumerable<Guid> GetRecordings() =>
            Directory.Exists(_recordingsRoot)
                ? new DirectoryInfo(_recordingsRoot).GetDirectories().Select(d => Guid.Parse(d.Name))
                : Array.Empty<Guid>();

        public static string TarPath(Guid id) => Path.Combine(_recordingsRoot, $"{id}.tar");

        public static void DeleteRecording(Guid id)
        {
            if (File.Exists(TarPath(id)))
                File.Delete(TarPath(id));

            var directory = Path.Combine(_recordingsRoot, id.ToString());
            if (Directory.Exists(directory))
                Directory.Delete(directory, recursive: true);
        }

        private static StreamWriter OpenCsv(string name, string header)
        {
            var writer = new StreamWriter(Path.Combine(_recordingDirectory, name)) { AutoFlush = true };
            if (header != null)
                writer.WriteLine(header);
            return writer;
        }

        private static long UnixMs() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        // Frames from a provider without a camera clock fall back to the wall clock, in ns.
        private static long FrameTimestampNs(CameraFrame frame) =>
            frame.TimestampNs != 0 ? frame.TimestampNs : UnixMs() * 1_000_000;

        private static string Pose(Vector3 position, Quaternion rotation) =>
            string.Format(
                CultureInfo.InvariantCulture,
                "{0:R},{1:R},{2:R},{3:R},{4:R},{5:R},{6:R}",
                position.x, position.y, position.z, rotation.x, rotation.y, rotation.z, rotation.w
            );

        private static void SaveImage(string folder, long timestampNs, byte[] bytes)
        {
            // Thousands of writes in a long video recording; only the unfinished ones need keeping.
            if (_pendingWrites.Count > 256)
                _pendingWrites.RemoveAll(task => task.IsCompleted);
            _pendingWrites.Add(
                File.WriteAllBytesAsync(Path.Combine(_recordingDirectory, folder, $"{timestampNs}.jpg"), bytes, CancellationToken.None)
            );
        }

        private static void WriteImage(CameraFrame frame, string folder, StreamWriter writer, Action count)
        {
            if (_subscriptions == null)
                return;

            var timestampNs = FrameTimestampNs(frame);
            SaveImage(folder, timestampNs, frame.ImageBytes);
            writer.WriteLine(
                $"{timestampNs},{UnixMs()},{Pose(frame.CameraTranslationUnityWorldFromCamera, frame.CameraRotationUnityWorldFromCamera)}"
            );
            count();
        }

        private static void WriteTrackingSample(TrackingSample sample)
        {
            if (_subscriptions == null)
                return;

            _trackingWriter.WriteLine(
                $"{sample.TimestampNs},{UnixMs()},{sample.TrackingState},{sample.NotTrackingReason},"
                    + Pose(sample.CameraTranslationUnityWorldFromCamera, sample.CameraRotationUnityWorldFromCamera)
            );
            TrackingSampleCount++;
        }

        private static void OnLocalizationAttempt(LocalizationAttempt attempt)
        {
            if (_subscriptions == null)
                return;

            var timestampNs = FrameTimestampNs(attempt.Frame);
            SaveImage("vps", timestampNs, attempt.Frame.ImageBytes);

            var line = new JObject
            {
                ["timestamp_ns"] = timestampNs,
                ["request_unix_ms"] = attempt.RequestUnixMs,
                ["response_unix_ms"] = attempt.ResponseUnixMs,
                ["camera_position"] = VectorJson(attempt.Frame.CameraTranslationUnityWorldFromCamera),
                ["camera_rotation"] = QuaternionJson(attempt.Frame.CameraRotationUnityWorldFromCamera),
                ["error"] = attempt.Error,
                ["result"] = attempt.Result != null ? JObject.FromObject(attempt.Result) : null,
            };
            if (attempt.Step is StepResult step)
            {
                line["filter"] = new JObject
                {
                    ["rejection"] = step.Rejection.ToString(),
                    ["innovation_mahalanobis_sq"] = step.InnovationMahalanobisSquared,
                    ["snapped"] = step.Snapped,
                    ["had_accepted_before"] = step.HadAcceptedMeasurementBeforeStep,
                    // Unity world from ECEF, column-major, after this step.
                    ["alignment_mean"] = MatrixJson(step.NewState.AlignmentMean),
                    ["alignment_current"] = MatrixJson(step.NewState.AlignmentCurrent),
                };
            }
            _vpsWriter.WriteLine(line.ToString(Formatting.None));
            VpsAttemptCount++;
        }

        private static JArray VectorJson(Vector3 v) => new(v.x, v.y, v.z);

        private static JArray QuaternionJson(Quaternion q) => new(q.x, q.y, q.z, q.w);

        private static JArray MatrixJson(double4x4 m) =>
            new(m.c0.x, m.c0.y, m.c0.z, m.c0.w, m.c1.x, m.c1.y, m.c1.z, m.c1.w,
                m.c2.x, m.c2.y, m.c2.z, m.c2.w, m.c3.x, m.c3.y, m.c3.z, m.c3.w);

        private static void WriteManifest(
            string directory,
            PinholeCameraConfig config,
            float stillIntervalSeconds,
            List<Guid> mapIds,
            DateTime startedAt
        )
        {
            var manifest = new JObject
            {
                ["type"] = ManifestType,
                ["version"] = ManifestVersion,
                ["axis_convention"] = "UNITY",
                ["started_at"] = startedAt.ToString("o", CultureInfo.InvariantCulture),
                ["still_interval_seconds"] = stillIntervalSeconds,
                ["video_downscale"] = VideoDownscale,
                ["map_ids"] = new JArray(mapIds.Select(id => id.ToString())),
                ["device_model"] = SystemInfo.deviceModel,
                ["platform"] = Application.platform.ToString(),
                ["app"] = Application.identifier,
                ["app_version"] = Application.version,
                ["camera"] = JObject.Parse(config.ToJson()),
            };
            File.WriteAllText(Path.Combine(directory, "manifest.json"), manifest.ToString(Formatting.Indented));
        }

        private static void WriteTar(string directory, string tarPath)
        {
            var baseDirectory = new DirectoryInfo(directory);
            using var fileStream = File.Create(tarPath);
            using var tarStream = new TarOutputStream(fileStream, Encoding.UTF8);
            foreach (var file in baseDirectory.EnumerateFiles("*", SearchOption.AllDirectories))
            {
                var entry = TarEntry.CreateTarEntry(Path.GetRelativePath(baseDirectory.FullName, file.FullName).Replace('\\', '/'));
                entry.Size = file.Length;
                entry.ModTime = file.LastWriteTimeUtc;
                tarStream.PutNextEntry(entry);
                using (var input = file.OpenRead())
                    input.CopyTo(tarStream);
                tarStream.CloseEntry();
            }
        }
    }
}
