using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading;
using Cysharp.Threading.Tasks;
using Plerion.Core;
using PlerionApiClient.Model;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

public static class LocalCaptureController
{
    static ARAnchorManager anchorManager;
    static ARAnchor captureAnchor;

    static Guid sessionId;
    static string sessionDirectory;
    static StreamWriter poseWriter;

    static string recordingsRoot;

    static string SessionDir(string name) => Path.Combine(recordingsRoot, name);

    static string ZipPath(string name) => Path.Combine(recordingsRoot, $"{name}.zip");

    public static void Initialize()
    {
        recordingsRoot = Path.Combine(Application.persistentDataPath, "Captures");
        Directory.CreateDirectory(recordingsRoot);

        anchorManager = UnityEngine.Object.FindAnyObjectByType<ARAnchorManager>();
    }

    public static IEnumerable<Guid> GetCaptures()
    {
        if (!Directory.Exists(recordingsRoot))
            return Array.Empty<Guid>();

        return new DirectoryInfo(recordingsRoot).GetDirectories().Select(d => d.Name).Select(name => Guid.Parse(name));
    }

    public static async UniTask<Stream> GetCapture(Guid captureId) =>
        await TarUtils.CreateTarAsync(SessionDir(captureId.ToString()));

    public static async UniTask StartCapture(
        float requestedCaptureIntervalSeconds,
        CancellationToken cancellationToken = default
    )
    {
        sessionId = Guid.NewGuid();
        sessionDirectory = SessionDir(sessionId.ToString());
        Directory.CreateDirectory(Path.Combine(sessionDirectory, "rig0"));
        Directory.CreateDirectory(Path.Combine(sessionDirectory, "rig0", "camera0"));

        poseWriter = new StreamWriter(Path.Combine(sessionDirectory, "rig0", "frames.csv")) { AutoFlush = true };
        poseWriter.WriteLine("timestamp,tx,ty,tz,qx,qy,qz,qw");

        await UniTask.WaitUntil(
            () => ARSession.state == ARSessionState.SessionTracking,
            cancellationToken: cancellationToken
        );

        var cameraManager = UnityEngine.Object.FindAnyObjectByType<ARCameraManager>();

        captureAnchor = (
            await anchorManager.TryAddAnchorAsync(
                new Pose(
                    cameraManager.transform.position,
                    Quaternion.Euler(0f, cameraManager.transform.eulerAngles.y, 0f)
                )
            )
        ).value;

        await UniTask.WaitUntil(
            () => ARSession.state == ARSessionState.SessionTracking,
            cancellationToken: cancellationToken
        );

        var cameraConfig = await VisualPositioningSystem.CameraProvider.Start(
            requestedCaptureIntervalSeconds,
            () =>
            {
                // Don't capture if we lost tracking
                if (
                    ARSession.state != ARSessionState.SessionTracking
                    || captureAnchor.trackingState == TrackingState.None
                )
                {
                    Debug.LogWarning("Tracking lost, skipping frame capture");
                    return null;
                }

                var cameraTransform = UnityEngine.Camera.main.transform;
                return (
                    captureAnchor.transform.InverseTransformPoint(cameraTransform.position),
                    Quaternion.Inverse(captureAnchor.transform.rotation) * cameraTransform.rotation
                );
            },
            async (bytes, cameraPosition, cameraRotation) =>
            {
                long timestampMilliseconds = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

                var absoluteImagePath = Path.Combine(
                    sessionDirectory,
                    "rig0",
                    "camera0",
                    $"{timestampMilliseconds}.jpg"
                );
                Directory.CreateDirectory(Path.GetDirectoryName(absoluteImagePath)!);
                await File.WriteAllBytesAsync(absoluteImagePath, bytes);

                // Write out pose
                poseWriter.WriteLine(
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
        );

        // Write out capture session manifest
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
                                new CameraConfig(cameraConfig)
                            ),
                        }
                    ),
                }
            ).ToJson()
        );
    }

    public static async UniTask StopCapture()
    {
        await VisualPositioningSystem.CameraProvider.Stop();

        poseWriter?.Dispose();
        poseWriter = null;

        await UniTask.RunOnThreadPool(() =>
            System.IO.Compression.ZipFile.CreateFromDirectory(sessionDirectory, ZipPath(sessionId.ToString()))
        );
    }

    public static bool CaptureExists(Guid id) => File.Exists(ZipPath(id.ToString()));

    public static void DeleteCapture(Guid id)
    {
        if (File.Exists(ZipPath(id.ToString())))
            File.Delete(ZipPath(id.ToString()));

        if (Directory.Exists(SessionDir(id.ToString())))
            Directory.Delete(SessionDir(id.ToString()), recursive: true);
    }
}
