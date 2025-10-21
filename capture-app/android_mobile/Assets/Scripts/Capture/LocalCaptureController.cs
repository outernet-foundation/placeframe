using System;
using System.Globalization;
using System.IO;
using System.Threading;
using System.Linq;
using Cysharp.Threading.Tasks;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Android;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using System.Collections.Generic;
using static RigConfig;

public static class LocalCaptureController
{


    static ARCameraManager cameraManager;
    static float captureIntervalSeconds;

    static Guid sessionId;
    static string sessionDirectory;
    static StreamWriter poseWriter;
    static readonly object inputOutputLock = new();

    static bool configWritten;
    static float nextCaptureTime;

    static string recordingsRoot;
    static string SessionDir(string name) => Path.Combine(recordingsRoot, name);
    static string ZipPath(string name) => Path.Combine(recordingsRoot, $"{name}.zip");

    public static void Initialize()
    {
        recordingsRoot = Path.Combine(Application.persistentDataPath, "Captures");
    }

    public static IEnumerable<Guid> GetCaptures()
    {
        if (!Directory.Exists(recordingsRoot))
            return Array.Empty<Guid>();

        return new DirectoryInfo(recordingsRoot)
            .GetDirectories()
            .Select(d => d.Name)
            .Select(name => Guid.Parse(name));
    }

    public static async UniTask<Stream> GetCapture(Guid captureId)
        => await TarUtils.CreateTarAsync(SessionDir(captureId.ToString()));

    public static async UniTask StartCapture(
        CancellationToken cancellationToken,
        float requestedCaptureIntervalSeconds)
    {
        var root = recordingsRoot;
        Debug.Log($"Capture root: {root}");
        Directory.CreateDirectory(recordingsRoot); // ensure root exists

        cameraManager = UnityEngine.Object.FindObjectOfType<ARCameraManager>();
        captureIntervalSeconds = requestedCaptureIntervalSeconds;

        Application.targetFrameRate = 30;

        await UniTask.WaitUntil(
            () => Permission.HasUserAuthorizedPermission(Permission.Camera),
            cancellationToken: cancellationToken);

        await UniTask.WaitUntil(
            () => ARSession.state == ARSessionState.SessionTracking,
            cancellationToken: cancellationToken);

        sessionId = Guid.NewGuid();
        sessionDirectory = SessionDir(sessionId.ToString());
        Directory.CreateDirectory(Path.Combine(sessionDirectory, "rig0"));
        Directory.CreateDirectory(Path.Combine(sessionDirectory, "rig0", "camera0"));

        poseWriter = new StreamWriter(
            Path.Combine(sessionDirectory, "rig0", "frames.csv"))
        {
            AutoFlush = true
        };
        poseWriter.WriteLine("timestamp,tx,ty,tz,qx,qy,qz,qw");

        cameraManager.frameReceived += OnCameraFrameReceived;
    }

    public static void StopCapture()
    {
        poseWriter?.Dispose();
        poseWriter = null;

        if (cameraManager != null)
        {
            cameraManager.frameReceived -= OnCameraFrameReceived;
            cameraManager = null;
        }

        configWritten = false;
        nextCaptureTime = 0;

        // Put the zip *next to* the sessionDirectory
        string zipFilePath = ZipPath(sessionId.ToString());
        System.IO.Compression.ZipFile.CreateFromDirectory(sessionDirectory, zipFilePath);
    }

    static void OnCameraFrameReceived(ARCameraFrameEventArgs _)
    {
        // Write config.json once
        if (!configWritten && cameraManager.TryGetIntrinsics(out var intrinsics))
        {
            var json = JsonUtility.ToJson(
                new RigConfig()
                {
                    rigs = new Rig[]
                    {
                        new()
                        {
                            id = "rig0",
                            cameras = new RigCamera[]
                            {
                                new RigCamera()
                                {
                                    id = "camera0",
                                    model = "PINHOLE",
                                    width = intrinsics.resolution.x,
                                    height = intrinsics.resolution.y,
                                    intrinsics = new float[]
                                    {
                                        intrinsics.focalLength.x,
                                        intrinsics.focalLength.y,
                                        intrinsics.principalPoint.x,
                                        intrinsics.principalPoint.y
                                    },
                                    ref_sensor = true,
                                    rotation = new float[] {0, 0, 0, 1},
                                    translation = new float[] {0, 0, 0}
                                }
                            }
                        }
                    }
                }
            );

            File.WriteAllText(
                Path.Combine(sessionDirectory, "config.json"),
                json
            );

            configWritten = true;
        }

        // Throttle capture to the requested interval.
        if (Time.time < nextCaptureTime) return;
        nextCaptureTime = Time.time + captureIntervalSeconds;

        // Acquire the latest CPU image.
        if (!cameraManager.TryAcquireLatestCpuImage(out var cpuImage)) return;

        long timestampMilliseconds = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        // Write pose row: timestamp, tx,ty,tz, qx,qy,qz,qw
        lock (inputOutputLock)
        {
            poseWriter.WriteLine(string.Format(
                CultureInfo.InvariantCulture,
                "{0},{1},{2},{3},{4},{5},{6},{7}",
                timestampMilliseconds,
                cameraManager.transform.position.x,
                cameraManager.transform.position.y,
                cameraManager.transform.position.z,
                cameraManager.transform.rotation.x,
                cameraManager.transform.rotation.y,
                cameraManager.transform.rotation.z,
                cameraManager.transform.rotation.w));
        }

        // Save the jpg off-thread.
        SaveImageAsync(cpuImage, Path.Combine(sessionDirectory, "rig0", "camera0", $"{timestampMilliseconds}.jpg")).Forget();
    }

    static async UniTask SaveImageAsync(
        XRCpuImage cpuImage,
        string absoluteImagePath)
    {
        var conversion = new XRCpuImage.ConversionParams(
            cpuImage,
            TextureFormat.RGBA32,
            XRCpuImage.Transformation.None);

        int byteCount = cpuImage.GetConvertedDataSize(conversion);
        using var pixelBuffer = new NativeArray<byte>(byteCount, Allocator.TempJob);
        cpuImage.Convert(conversion, pixelBuffer);
        cpuImage.Dispose();

        var texture = new Texture2D(
            conversion.outputDimensions.x,
            conversion.outputDimensions.y,
            TextureFormat.RGBA32,
            false);

        texture.LoadRawTextureData(pixelBuffer);
        texture.Apply(false, false);
        byte[] jpgBytes = texture.EncodeToJPG();
        UnityEngine.Object.Destroy(texture);

        Directory.CreateDirectory(Path.GetDirectoryName(absoluteImagePath)!);
        await File.WriteAllBytesAsync(absoluteImagePath, jpgBytes);
    }
}
