using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using Cysharp.Threading.Tasks;
using ICSharpCode.SharpZipLib.Tar;
using PlaceframeApiClient.Model;
using R3;
using UnityEngine;

namespace Placeframe.Core
{
    public static class CaptureManager
    {
        private static ICameraProvider _cameraProvider;
        private static string _recordingsRoot;
        private static IDisposable _subscriptions;
        private static Guid _sessionId;
        private static StreamWriter _poseWriter;

        public static void Initialize(ICameraProvider cameraProvider)
        {
            _cameraProvider = cameraProvider;
            _recordingsRoot = Path.Combine(Application.persistentDataPath, "Captures");
            Directory.CreateDirectory(_recordingsRoot);
        }

        public static void StartCapture(float intervalSeconds)
        {
            if (_subscriptions != null)
                throw new InvalidOperationException("Capture already running");

            _sessionId = Guid.NewGuid();
            var sessionDirectory = SessionDir(_sessionId.ToString());
            Directory.CreateDirectory(Path.Combine(sessionDirectory, "rig0"));
            Directory.CreateDirectory(Path.Combine(sessionDirectory, "rig0", "camera0"));

            _poseWriter = new StreamWriter(Path.Combine(sessionDirectory, "rig0", "frames.csv")) { AutoFlush = true };
            _poseWriter.WriteLine("timestamp,tx,ty,tz,qx,qy,qz,qw");

            var cameraConfigObservable = _cameraProvider
                // Get camera configuration asynchronously
                .CameraConfig()
                // Share the observable so multiple subscriptions trigger only one camera config fetch
                .Share();

            _subscriptions = Disposable.Combine(
                cameraConfigObservable
                    // Write the capture manifest once using the camera configuration
                    .Take(1)
                    .Subscribe(config => WriteManifest(sessionDirectory, config)),
                cameraConfigObservable
                    // Observe CameraFrames (with camera pose anchoring, to prevent pose discontinuities due to tracking loss)
                    .SelectMany(_ => _cameraProvider.Frames(intervalSeconds, useCameraPoseAnchoring: true))
                    // Write each new CameraFrame to disk
                    .SubscribeAwait(
                        (frame, cancellationToken) => WriteFrame(sessionDirectory, frame, cancellationToken),
                        // Skip frames if they pile up
                        AwaitOperation.Drop
                    )
            );
        }

        public static void StopCapture()
        {
            if (_subscriptions == null)
                throw new InvalidOperationException("Capture not running");

            UniTask
                .RunOnThreadPool(() =>
                    System.IO.Compression.ZipFile.CreateFromDirectory(
                        SessionDir(_sessionId.ToString()),
                        ZipPath(_sessionId.ToString())
                    )
                )
                .Forget();

            _subscriptions.Dispose();
            _subscriptions = null;

            _poseWriter?.Dispose();
            _poseWriter = null;
        }

        public static IEnumerable<Guid> GetCaptures()
        {
            if (!Directory.Exists(_recordingsRoot))
                return Array.Empty<Guid>();

            return new DirectoryInfo(_recordingsRoot)
                .GetDirectories()
                .Select(d => d.Name)
                .Select(name => Guid.Parse(name));
        }

        public static async UniTask<Stream> GetCaptureTar(Guid captureId)
        {
            var directoryPath = SessionDir(captureId.ToString());
            if (!Directory.Exists(directoryPath))
                throw new DirectoryNotFoundException(directoryPath);

            var baseDirectory = new DirectoryInfo(directoryPath);
            var memoryStream = new MemoryStream();

            using (var tarStream = new TarOutputStream(memoryStream, Encoding.UTF8))
            {
                tarStream.IsStreamOwner = false;

                foreach (var file in baseDirectory.EnumerateFiles("*", SearchOption.AllDirectories))
                {
                    var relativePath = Path.GetRelativePath(baseDirectory.FullName, file.FullName).Replace('\\', '/');
                    var entry = TarEntry.CreateTarEntry(relativePath);
                    entry.Size = file.Length;
                    entry.ModTime = file.LastWriteTimeUtc;

                    tarStream.PutNextEntry(entry);
                    using (var fileStream = file.OpenRead())
                    {
                        await fileStream.CopyToAsync(tarStream).ConfigureAwait(false);
                    }
                    tarStream.CloseEntry();
                }

                tarStream.Close();
            }

            memoryStream.Position = 0;
            return memoryStream;
        }

        public static void DeleteCapture(Guid id)
        {
            if (File.Exists(ZipPath(id.ToString())))
                File.Delete(ZipPath(id.ToString()));

            if (Directory.Exists(SessionDir(id.ToString())))
                Directory.Delete(SessionDir(id.ToString()), recursive: true);
        }

        private static string SessionDir(string name) => Path.Combine(_recordingsRoot, name);

        private static string ZipPath(string name) => Path.Combine(_recordingsRoot, $"{name}.zip");

        private static void WriteManifest(string sessionDirectory, PinholeCameraConfig config) =>
            File.WriteAllText(
                Path.Combine(sessionDirectory, "manifest.json"),
                new CaptureSessionManifest(
                    AxisConvention.UNITY,
                    new List<RigConfig>
                    {
                        new RigConfig(
                            "rig0",
                            new List<RigCameraConfig>
                            {
                                new RigCameraConfig(
                                    "camera0",
                                    true,
                                    new Float4(0, 0, 0, 1),
                                    new Float3(0, 0, 0),
                                    config
                                ),
                            }
                        ),
                    }
                ).ToJson()
            );

        private static async UniTask WriteFrame(string sessionDirectory, CameraFrame frame, CancellationToken _)
        {
            var bytes = frame.ImageBytes;
            var cameraPosition = frame.CameraTranslationUnityWorldFromCamera;
            var cameraRotation = frame.CameraRotationUnityWorldFromCamera;

            long timestampMilliseconds = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

            var absoluteImagePath = Path.Combine(sessionDirectory, "rig0", "camera0", $"{timestampMilliseconds}.jpg");

            // Deliberately not awaiting this or making it cancellable, to prevent writing the bytes but not the pose
            File.WriteAllBytesAsync(absoluteImagePath, bytes, CancellationToken.None).AsUniTask().Forget();

            await _poseWriter.WriteLineAsync(
                string.Format(
                    CultureInfo.InvariantCulture,
                    "{0},{1},{2},{3},{4},{5},{6},{7}",
                    timestampMilliseconds,
                    cameraPosition.x,
                    cameraPosition.y,
                    cameraPosition.z,
                    cameraRotation.x,
                    cameraRotation.y,
                    cameraRotation.z,
                    cameraRotation.w
                )
            );
        }
    }
}
