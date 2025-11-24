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
using Unity.Mathematics;
using PlerionApiClient.Model;


public static class LocalCaptureController
{
    static ARCameraManager cameraManager;
    static ARAnchorManager anchorManager;
    static ARAnchor captureAnchor;
    static float captureIntervalSeconds;
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
        anchorManager = UnityEngine.Object.FindObjectOfType<ARAnchorManager>();
        captureIntervalSeconds = requestedCaptureIntervalSeconds;

        Application.targetFrameRate = 30;

        await UniTask.WaitUntil(
            () => Permission.HasUserAuthorizedPermission(Permission.Camera),
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

        await UniTask.WaitUntil(
            () => ARSession.state == ARSessionState.SessionTracking,
            cancellationToken: cancellationToken);

        captureAnchor = (await anchorManager.TryAddAnchorAsync(new Pose(cameraManager.transform.position, cameraManager.transform.rotation))).value;

        await UniTask.WaitUntil(
            () => captureAnchor.trackingState == TrackingState.Tracking,
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

        first_frame = true;
        nextCaptureTime = 0;

        // Put the zip *next to* the sessionDirectory
        string zipFilePath = ZipPath(sessionId.ToString());
        System.IO.Compression.ZipFile.CreateFromDirectory(sessionDirectory, zipFilePath);
    }

    static void OnCameraFrameReceived(ARCameraFrameEventArgs args)
    {
        // Don't capture if we lost tracking of the capture anchor
        if (captureAnchor.trackingState != TrackingState.Tracking)
        {
            Debug.LogWarning("Capture anchor lost tracking; skipping frame.");
            return;
        }

        // Throttle capture to the requested interval.
        if (Time.time < nextCaptureTime) return;
        nextCaptureTime = Time.time + captureIntervalSeconds;

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

            // Write out rig config
            File.WriteAllText(
                Path.Combine(sessionDirectory, "config.json"),

                    new RigConfig(
                        new List<Rig>
                        {
                            new Rig(
                                "rig0",
                                new List<RigCamera>
                                {
                                    new RigCamera(
                                        "camera0",
                                        true,
                                        new PlerionApiClient.Model.Quaternion(0, 0, 0, 1),
                                        new PlerionApiClient.Model.Vector3(0, 0, 0),
                                        new Intrinsics(new PinholeCamera(
                                            intrinsics.resolution.x,
                                            intrinsics.resolution.y,
                                            PinholeCamera.MirroringEnum.None,
                                            PinholeCamera.RotationEnum._90CCW,
                                            PinholeCamera.ModelEnum.PINHOLE,
                                            intrinsics.focalLength.x,
                                            intrinsics.focalLength.y,
                                            flipped ? (intrinsics.resolution.x - 1) - intrinsics.principalPoint.x : intrinsics.principalPoint.x,
                                            intrinsics.principalPoint.y
                                        ))
                                    )
                                }
                            )
                        }
                    ).ToJson()

            );

            // Done with first frame setup
            first_frame = false;
        }

        // Acquire the latest CPU image.
        if (!cameraManager.TryAcquireLatestCpuImage(out var cpuImage)) return;

        long timestampMilliseconds = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        // Compute camera pose relative to the capture anchor
        var framePosition = captureAnchor.transform.InverseTransformPoint(cameraManager.transform.position);
        var frameRotation = UnityEngine.Quaternion.Inverse(captureAnchor.transform.rotation) * cameraManager.transform.rotation;

        // Change basis from Unity to OpenCV
        var (rotationWorldFromCamera_openCV, cameraCenterInWorld_openCV) =
                OpenCVFromUnity(new float3x3(frameRotation), new float3(framePosition));

        // Write world_from_camera rotation (as quaternion) and camera_center_in_world
        var quaternionWorldFromCamera_openCV = new quaternion(rotationWorldFromCamera_openCV);
        poseWriter.WriteLine(string.Format(
            CultureInfo.InvariantCulture,
                "{0},{1},{2},{3},{4},{5},{6},{7}",
            timestampMilliseconds,
            cameraCenterInWorld_openCV.x, cameraCenterInWorld_openCV.y, cameraCenterInWorld_openCV.z,
            quaternionWorldFromCamera_openCV.value.x, quaternionWorldFromCamera_openCV.value.y,
            quaternionWorldFromCamera_openCV.value.z, quaternionWorldFromCamera_openCV.value.w));

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
