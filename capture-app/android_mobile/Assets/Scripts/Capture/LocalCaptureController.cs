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
using Unity.Mathematics;

public static class LocalCaptureController
{
    static ARCameraManager cameraManager;
    static float captureIntervalSeconds;
    static Vector3 startingPosition;
    static Quaternion startingRotation;
    static XRCameraConfiguration? bestConfig = null;

    static Guid sessionId;
    static string sessionDirectory;
    static StreamWriter poseWriter;
    static readonly object inputOutputLock = new();

    static bool first_frame = true;
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

        foreach (var config in cameraManager.GetConfigurations(Allocator.Temp))
        {
            if (bestConfig == null ||
                (config.width * config.height) > (bestConfig.Value.width * bestConfig.Value.height))
            {
                bestConfig = config;
            }
        }

        if (bestConfig.HasValue)
        {
            cameraManager.currentConfiguration = bestConfig;
            Debug.Log($"Selected camera configuration: {bestConfig.Value.width}x{bestConfig.Value.height} @ {bestConfig.Value.framerate}fps");
        }
        else
        {
            Debug.LogWarning("No camera configurations available.");
        }

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

        first_frame = true;
        nextCaptureTime = 0;

        // Put the zip *next to* the sessionDirectory
        string zipFilePath = ZipPath(sessionId.ToString());
        System.IO.Compression.ZipFile.CreateFromDirectory(sessionDirectory, zipFilePath);
    }

    static void OnCameraFrameReceived(ARCameraFrameEventArgs args)
    {
        // sometimes the camera image itself is flipped, so we might need to un-flip it
        var flipped = true; // TODO figure out how to detect this properly

        if (first_frame)
        {
            // Wait until we get intrinsics and they match the selected config
            if (!cameraManager.TryGetIntrinsics(out var intrinsics) ||
                intrinsics.resolution.x != bestConfig?.width ||
                intrinsics.resolution.y != bestConfig?.height)
            {
                return;
            }

            // Record the starting pose to rebase subsequent poses against
            startingPosition = cameraManager.transform.position;
            startingRotation = cameraManager.transform.rotation;

            // Write out rig config
            File.WriteAllText(
                Path.Combine(sessionDirectory, "config.json"),
                JsonUtility.ToJson(
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
                                        // Adjust principal point to account for mirroring the image
                                        flipped ? (intrinsics.resolution.x - 1) - intrinsics.principalPoint.x : intrinsics.principalPoint.x,
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
            ));

            // Done with first frame setup
            first_frame = false;
        }

        // Throttle capture to the requested interval.
        if (Time.time < nextCaptureTime) return;
        nextCaptureTime = Time.time + captureIntervalSeconds;

        // Acquire the latest CPU image.
        if (!cameraManager.TryAcquireLatestCpuImage(out var cpuImage)) return;

        long timestampMilliseconds = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        // Convert from world-from-camera to camera-from-world (COLMAP expects the latter for pose priors)
        float3x3 rotationCameraFromWorld_unity = math.transpose(new float3x3(cameraManager.transform.rotation));
        float3 translationCameraFromWorld_unity = -math.mul(rotationCameraFromWorld_unity, new float3(cameraManager.transform.position));

        // Change basis from Unity to OpenCV
        var (rotationCameraFromWorld_openCV, translationCameraFromWorld_openCV) =
            OpenCVFromUnity(rotationCameraFromWorld_unity, translationCameraFromWorld_unity);

        // Write pose prior
        var quaternionCameraFromWorld_openCV = new quaternion(rotationCameraFromWorld_openCV);
        poseWriter.WriteLine(string.Format(
            CultureInfo.InvariantCulture,
            "{0},{1},{2},{3},{4},{5},{6},{7}",
            timestampMilliseconds,
            translationCameraFromWorld_openCV.x, translationCameraFromWorld_openCV.y, translationCameraFromWorld_openCV.z,
            quaternionCameraFromWorld_openCV.value.x, quaternionCameraFromWorld_openCV.value.y,
            quaternionCameraFromWorld_openCV.value.z, quaternionCameraFromWorld_openCV.value.w));

        // Save jpeg
        SaveImageAsync(cpuImage, flipped, Path.Combine(sessionDirectory, "rig0", "camera0", $"{timestampMilliseconds}.jpg")).Forget();
    }

    static float3x3 basisOpenCV = new float3x3(
        new float3(1f, 0f, 0f),
        new float3(0f, -1f, 0f),
        new float3(0f, 0f, 1f)
    );
    static float3x3 basisUnity = float3x3.identity;
    static float3x3 basisChangeUnityFromOpenCV = math.mul(math.transpose(basisUnity), basisOpenCV);
    static float3x3 basisChangeOpenCVFromUnity = math.transpose(basisChangeUnityFromOpenCV);
    public static (float3x3, float3) UnityFromOpenCV(float3x3 rotation, float3 translation)
        => (math.mul(basisChangeUnityFromOpenCV, math.mul(rotation, basisChangeOpenCVFromUnity)), math.mul(basisChangeUnityFromOpenCV, translation));
    public static (float3x3, float3) OpenCVFromUnity(float3x3 rotation, float3 translation)
        => (math.mul(basisChangeOpenCVFromUnity, math.mul(rotation, basisChangeUnityFromOpenCV)), math.mul(basisChangeOpenCVFromUnity, translation));

    static async UniTask SaveImageAsync(
        XRCpuImage cpuImage,
        bool flipped,
        string absoluteImagePath)
    {
        var conversion = new XRCpuImage.ConversionParams(
            cpuImage,
            TextureFormat.RGBA32,
            // Mirror the image on the X axis to match the display orientation
            flipped ? XRCpuImage.Transformation.MirrorX : XRCpuImage.Transformation.None);

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
