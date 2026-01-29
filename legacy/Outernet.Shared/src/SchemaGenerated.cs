using System;
using System.Collections.Generic;
using MessagePack;
using UnityEngine;

namespace Outernet.Shared
{
    public partial class RoomRecord : SyncedRecord<RoomRecord, RoomRecord.InitializationData, IntLiteral28>
    {
        public class InitializationData
        {
            public Dictionary<Guid, UserRecord.InitializationData> users;
            public Dictionary<Guid, NodeRecord.InitializationData> placePoints;
            public bool settingsShowPointCloud;
            public bool settingsAnimateNodeIndicators;
            public LocalizationReducer settingsLocalizationReducer;
            public bool settingsEnableLocalizationThreshold;
            public bool settingsFallbackToMostRecent;
            public float settingsPositionThreshold;
            public float settingsRotationThreshold;
            public float settingsPositionInlierThreshold;
            public float settingsRotationInlierThreshold;
            public bool settingsDiscardBottomHalf;
            public float settingsConfidenceFactor;
            public int settingsRansacHistorySize;
            public int settingsFavHistorySize;
            public float settingsFavThreshold;
            public bool settingsUseFloorPlaneDetection;
            public float settingsNodeFetchRadius;
            public int settingsNodeFetchLimit;
            public TilesetMode settingsTerrainTilesetMode;
            public TilesetMode settingsOSMTilesetMode;
            public TilesetMode settingsNYCTilesetMode;
            public TilesetMode settingsGoogleTilesetMode;
            public bool settingsDynamicFocusDistance;
            public bool settingsShowEyeDebug;
            public bool settingsLocalize;
            public bool settingsAnimateUserIndicators;
            public HashSet<Guid> settingsVisibleLayers;

            public InitializationData()
            {
                users = new Dictionary<Guid, UserRecord.InitializationData>();
                placePoints = new Dictionary<Guid, NodeRecord.InitializationData>();
                settingsShowPointCloud = false;
                settingsAnimateNodeIndicators = false;
                settingsLocalizationReducer = LocalizationReducer.RANSAC;
                settingsEnableLocalizationThreshold = true;
                settingsFallbackToMostRecent = false;
                settingsPositionThreshold = 0.04f;
                settingsRotationThreshold = 2.0f;
                settingsPositionInlierThreshold = 0.32f;
                settingsRotationInlierThreshold = 2.0f;
                settingsDiscardBottomHalf = false;
                settingsConfidenceFactor = 1.0f;
                settingsRansacHistorySize = 128;
                settingsFavHistorySize = 16;
                settingsFavThreshold = 2.0f;
                settingsUseFloorPlaneDetection = true;
                settingsNodeFetchRadius = 160f;
                settingsNodeFetchLimit = 64;
                settingsTerrainTilesetMode = TilesetMode.Disable;
                settingsOSMTilesetMode = TilesetMode.Hide;
                settingsNYCTilesetMode = TilesetMode.Disable;
                settingsGoogleTilesetMode = TilesetMode.Disable;
                settingsDynamicFocusDistance = true;
                settingsShowEyeDebug = false;
                settingsLocalize = true;
                settingsAnimateUserIndicators = true;
                settingsVisibleLayers = new HashSet<Guid>();
            }
        }

        public InitializationData GetInitializationData()
        {
            var initializationData = new InitializationData();
            initializationData.settingsShowPointCloud = settingsShowPointCloud.Value;
            initializationData.settingsAnimateNodeIndicators = settingsAnimateNodeIndicators.Value;
            initializationData.settingsLocalizationReducer = settingsLocalizationReducer.Value;
            initializationData.settingsEnableLocalizationThreshold = settingsEnableLocalizationThreshold.Value;
            initializationData.settingsFallbackToMostRecent = settingsFallbackToMostRecent.Value;
            initializationData.settingsPositionThreshold = settingsPositionThreshold.Value;
            initializationData.settingsRotationThreshold = settingsRotationThreshold.Value;
            initializationData.settingsPositionInlierThreshold = settingsPositionInlierThreshold.Value;
            initializationData.settingsRotationInlierThreshold = settingsRotationInlierThreshold.Value;
            initializationData.settingsDiscardBottomHalf = settingsDiscardBottomHalf.Value;
            initializationData.settingsConfidenceFactor = settingsConfidenceFactor.Value;
            initializationData.settingsRansacHistorySize = settingsRansacHistorySize.Value;
            initializationData.settingsFavHistorySize = settingsFavHistorySize.Value;
            initializationData.settingsFavThreshold = settingsFavThreshold.Value;
            initializationData.settingsUseFloorPlaneDetection = settingsUseFloorPlaneDetection.Value;
            initializationData.settingsNodeFetchRadius = settingsNodeFetchRadius.Value;
            initializationData.settingsNodeFetchLimit = settingsNodeFetchLimit.Value;
            initializationData.settingsTerrainTilesetMode = settingsTerrainTilesetMode.Value;
            initializationData.settingsOSMTilesetMode = settingsOSMTilesetMode.Value;
            initializationData.settingsNYCTilesetMode = settingsNYCTilesetMode.Value;
            initializationData.settingsGoogleTilesetMode = settingsGoogleTilesetMode.Value;
            initializationData.settingsDynamicFocusDistance = settingsDynamicFocusDistance.Value;
            initializationData.settingsShowEyeDebug = settingsShowEyeDebug.Value;
            initializationData.settingsLocalize = settingsLocalize.Value;
            initializationData.settingsAnimateUserIndicators = settingsAnimateUserIndicators.Value;
            initializationData.settingsVisibleLayers = new HashSet<Guid>(settingsVisibleLayers.GetItems());

            return initializationData;
        }

        public RoomRecord(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem)
        {
            users = new SyncedDictionary<Guid, UserRecord, UserRecord.InitializationData>(syncedStateSystem, (syncedStateSystem) => new UserRecord(syncedStateSystem));
            nodes = new SyncedDictionary<Guid, NodeRecord, NodeRecord.InitializationData>(syncedStateSystem, (syncedStateSystem) => new NodeRecord(syncedStateSystem));
            settingsShowPointCloud = new SyncedProperty<bool>(syncedStateSystem);
            settingsAnimateNodeIndicators = new SyncedProperty<bool>(syncedStateSystem);
            settingsLocalizationReducer = new SyncedProperty<LocalizationReducer>(syncedStateSystem);
            settingsEnableLocalizationThreshold = new SyncedProperty<bool>(syncedStateSystem);
            settingsFallbackToMostRecent = new SyncedProperty<bool>(syncedStateSystem);
            settingsPositionThreshold = new SyncedProperty<float>(syncedStateSystem);
            settingsRotationThreshold = new SyncedProperty<float>(syncedStateSystem);
            settingsPositionInlierThreshold = new SyncedProperty<float>(syncedStateSystem);
            settingsRotationInlierThreshold = new SyncedProperty<float>(syncedStateSystem);
            settingsDiscardBottomHalf = new SyncedProperty<bool>(syncedStateSystem);
            settingsConfidenceFactor = new SyncedProperty<float>(syncedStateSystem);
            settingsRansacHistorySize = new SyncedProperty<int>(syncedStateSystem);
            settingsFavHistorySize = new SyncedProperty<int>(syncedStateSystem);
            settingsFavThreshold = new SyncedProperty<float>(syncedStateSystem);
            settingsUseFloorPlaneDetection = new SyncedProperty<bool>(syncedStateSystem);
            settingsNodeFetchRadius = new SyncedProperty<float>(syncedStateSystem);
            settingsNodeFetchLimit = new SyncedProperty<int>(syncedStateSystem);
            settingsTerrainTilesetMode = new SyncedProperty<TilesetMode>(syncedStateSystem);
            settingsOSMTilesetMode = new SyncedProperty<TilesetMode>(syncedStateSystem);
            settingsNYCTilesetMode = new SyncedProperty<TilesetMode>(syncedStateSystem);
            settingsGoogleTilesetMode = new SyncedProperty<TilesetMode>(syncedStateSystem);
            settingsDynamicFocusDistance = new SyncedProperty<bool>(syncedStateSystem);
            settingsShowEyeDebug = new SyncedProperty<bool>(syncedStateSystem);
            settingsLocalize = new SyncedProperty<bool>(syncedStateSystem);
            settingsAnimateUserIndicators = new SyncedProperty<bool>(syncedStateSystem);
            settingsVisibleLayers = new SyncedSet<Guid>(syncedStateSystem);

            SetupDeltaSubscription(users, 0);
            SetupDeltaSubscription(nodes, 1);
            SetupDeltaSubscription(settingsShowPointCloud, 2);
            SetupDeltaSubscription(settingsAnimateNodeIndicators, 3);
            SetupDeltaSubscription(settingsLocalizationReducer, 4);
            SetupDeltaSubscription(settingsEnableLocalizationThreshold, 5);
            SetupDeltaSubscription(settingsFallbackToMostRecent, 6);
            SetupDeltaSubscription(settingsPositionThreshold, 7);
            SetupDeltaSubscription(settingsRotationThreshold, 8);
            SetupDeltaSubscription(settingsPositionInlierThreshold, 9);
            SetupDeltaSubscription(settingsRotationInlierThreshold, 10);
            SetupDeltaSubscription(settingsDiscardBottomHalf, 11);
            SetupDeltaSubscription(settingsConfidenceFactor, 12);
            SetupDeltaSubscription(settingsRansacHistorySize, 13);
            SetupDeltaSubscription(settingsFavHistorySize, 14);
            SetupDeltaSubscription(settingsFavThreshold, 15);
            SetupDeltaSubscription(settingsUseFloorPlaneDetection, 16);
            SetupDeltaSubscription(settingsNodeFetchRadius, 17);
            SetupDeltaSubscription(settingsNodeFetchLimit, 18);
            SetupDeltaSubscription(settingsTerrainTilesetMode, 19);
            SetupDeltaSubscription(settingsOSMTilesetMode, 20);
            SetupDeltaSubscription(settingsNYCTilesetMode, 21);
            SetupDeltaSubscription(settingsGoogleTilesetMode, 22);
            SetupDeltaSubscription(settingsDynamicFocusDistance, 23);
            SetupDeltaSubscription(settingsShowEyeDebug, 24);
            SetupDeltaSubscription(settingsLocalize, 25);
            SetupDeltaSubscription(settingsAnimateUserIndicators, 26);
            SetupDeltaSubscription(settingsVisibleLayers, 27);
        }

        public override void Initialize(InitializationData initializationData)
        {
            users.Initialize(initializationData.users);
            nodes.Initialize(initializationData.placePoints);
            settingsAnimateNodeIndicators.Initialize(initializationData.settingsAnimateNodeIndicators);
            settingsShowPointCloud.Initialize(initializationData.settingsShowPointCloud);
            settingsLocalizationReducer.Initialize(initializationData.settingsLocalizationReducer);
            settingsEnableLocalizationThreshold.Initialize(initializationData.settingsEnableLocalizationThreshold);
            settingsFallbackToMostRecent.Initialize(initializationData.settingsFallbackToMostRecent);
            settingsPositionThreshold.Initialize(initializationData.settingsPositionThreshold);
            settingsRotationThreshold.Initialize(initializationData.settingsRotationThreshold);
            settingsPositionInlierThreshold.Initialize(initializationData.settingsPositionInlierThreshold);
            settingsRotationInlierThreshold.Initialize(initializationData.settingsRotationInlierThreshold);
            settingsDiscardBottomHalf.Initialize(initializationData.settingsDiscardBottomHalf);
            settingsConfidenceFactor.Initialize(initializationData.settingsConfidenceFactor);
            settingsRansacHistorySize.Initialize(initializationData.settingsRansacHistorySize);
            settingsFavHistorySize.Initialize(initializationData.settingsFavHistorySize);
            settingsFavThreshold.Initialize(initializationData.settingsFavThreshold);
            settingsUseFloorPlaneDetection.Initialize(initializationData.settingsUseFloorPlaneDetection);
            settingsNodeFetchRadius.Initialize(initializationData.settingsNodeFetchRadius);
            settingsNodeFetchLimit.Initialize(initializationData.settingsNodeFetchLimit);
            settingsTerrainTilesetMode.Initialize(initializationData.settingsTerrainTilesetMode);
            settingsOSMTilesetMode.Initialize(initializationData.settingsOSMTilesetMode);
            settingsNYCTilesetMode.Initialize(initializationData.settingsNYCTilesetMode);
            settingsGoogleTilesetMode.Initialize(initializationData.settingsGoogleTilesetMode);
            settingsDynamicFocusDistance.Initialize(initializationData.settingsDynamicFocusDistance);
            settingsShowEyeDebug.Initialize(initializationData.settingsShowEyeDebug);
            settingsLocalize.Initialize(initializationData.settingsLocalize);
            settingsAnimateUserIndicators.Initialize(initializationData.settingsAnimateUserIndicators);
            settingsVisibleLayers.Initialize(initializationData.settingsVisibleLayers);
        }

        protected override void DisposeGenerated()
        {
            users.Dispose();
            nodes.Dispose();
            settingsShowPointCloud.Dispose();
            settingsAnimateNodeIndicators.Dispose();
            settingsLocalizationReducer.Dispose();
            settingsEnableLocalizationThreshold.Dispose();
            settingsFallbackToMostRecent.Dispose();
            settingsPositionThreshold.Dispose();
            settingsRotationThreshold.Dispose();
            settingsPositionInlierThreshold.Dispose();
            settingsRotationInlierThreshold.Dispose();
            settingsDiscardBottomHalf.Dispose();
            settingsConfidenceFactor.Dispose();
            settingsRansacHistorySize.Dispose();
            settingsFavHistorySize.Dispose();
            settingsFavThreshold.Dispose();
            settingsUseFloorPlaneDetection.Dispose();
            settingsNodeFetchRadius.Dispose();
            settingsNodeFetchLimit.Dispose();
            settingsTerrainTilesetMode.Dispose();
            settingsOSMTilesetMode.Dispose();
            settingsNYCTilesetMode.Dispose();
            settingsGoogleTilesetMode.Dispose();
            settingsDynamicFocusDistance.Dispose();
            settingsShowEyeDebug.Dispose();
            settingsLocalize.Dispose();
            settingsAnimateUserIndicators.Dispose();
            settingsVisibleLayers.Dispose();
        }

        public override void Serialize(ref MessagePackWriter writer)
        {
            users.Serialize(ref writer);
            nodes.Serialize(ref writer);
            settingsShowPointCloud.Serialize(ref writer);
            settingsAnimateNodeIndicators.Serialize(ref writer);
            settingsLocalizationReducer.Serialize(ref writer);
            settingsEnableLocalizationThreshold.Serialize(ref writer);
            settingsFallbackToMostRecent.Serialize(ref writer);
            settingsPositionThreshold.Serialize(ref writer);
            settingsRotationThreshold.Serialize(ref writer);
            settingsPositionInlierThreshold.Serialize(ref writer);
            settingsRotationInlierThreshold.Serialize(ref writer);
            settingsDiscardBottomHalf.Serialize(ref writer);
            settingsConfidenceFactor.Serialize(ref writer);
            settingsRansacHistorySize.Serialize(ref writer);
            settingsFavHistorySize.Serialize(ref writer);
            settingsFavThreshold.Serialize(ref writer);
            settingsUseFloorPlaneDetection.Serialize(ref writer);
            settingsNodeFetchRadius.Serialize(ref writer);
            settingsNodeFetchLimit.Serialize(ref writer);
            settingsTerrainTilesetMode.Serialize(ref writer);
            settingsOSMTilesetMode.Serialize(ref writer);
            settingsNYCTilesetMode.Serialize(ref writer);
            settingsGoogleTilesetMode.Serialize(ref writer);
            settingsDynamicFocusDistance.Serialize(ref writer);
            settingsShowEyeDebug.Serialize(ref writer);
            settingsLocalize.Serialize(ref writer);
            settingsAnimateUserIndicators.Serialize(ref writer);
            settingsVisibleLayers.Serialize(ref writer);
        }

        public override void Deserialize(ref MessagePackReader reader)
        {
            users.Deserialize(ref reader);
            nodes.Deserialize(ref reader);
            settingsShowPointCloud.Deserialize(ref reader);
            settingsAnimateNodeIndicators.Deserialize(ref reader);
            settingsLocalizationReducer.Deserialize(ref reader);
            settingsEnableLocalizationThreshold.Deserialize(ref reader);
            settingsFallbackToMostRecent.Deserialize(ref reader);
            settingsPositionThreshold.Deserialize(ref reader);
            settingsRotationThreshold.Deserialize(ref reader);
            settingsPositionInlierThreshold.Deserialize(ref reader);
            settingsRotationInlierThreshold.Deserialize(ref reader);
            settingsDiscardBottomHalf.Deserialize(ref reader);
            settingsConfidenceFactor.Deserialize(ref reader);
            settingsRansacHistorySize.Deserialize(ref reader);
            settingsFavHistorySize.Deserialize(ref reader);
            settingsFavThreshold.Deserialize(ref reader);
            settingsUseFloorPlaneDetection.Deserialize(ref reader);
            settingsNodeFetchRadius.Deserialize(ref reader);
            settingsNodeFetchLimit.Deserialize(ref reader);
            settingsTerrainTilesetMode.Deserialize(ref reader);
            settingsOSMTilesetMode.Deserialize(ref reader);
            settingsNYCTilesetMode.Deserialize(ref reader);
            settingsGoogleTilesetMode.Deserialize(ref reader);
            settingsDynamicFocusDistance.Deserialize(ref reader);
            settingsShowEyeDebug.Deserialize(ref reader);
            settingsLocalize.Deserialize(ref reader);
            settingsAnimateUserIndicators.Deserialize(ref reader);
            settingsVisibleLayers.Deserialize(ref reader);
        }

        protected override void SerializeDeltaGenerated(ref MessagePackWriter writer, int key)
        {
            switch (key)
            {
                case 0: users.SerializeDelta(ref writer); break;
                case 1: nodes.SerializeDelta(ref writer); break;
                case 2: settingsShowPointCloud.SerializeDelta(ref writer); break;
                case 3: settingsAnimateNodeIndicators.SerializeDelta(ref writer); break;
                case 4: settingsLocalizationReducer.SerializeDelta(ref writer); break;
                case 5: settingsEnableLocalizationThreshold.SerializeDelta(ref writer); break;
                case 6: settingsFallbackToMostRecent.SerializeDelta(ref writer); break;
                case 7: settingsPositionThreshold.SerializeDelta(ref writer); break;
                case 8: settingsRotationThreshold.SerializeDelta(ref writer); break;
                case 9: settingsPositionInlierThreshold.SerializeDelta(ref writer); break;
                case 10: settingsRotationInlierThreshold.SerializeDelta(ref writer); break;
                case 11: settingsDiscardBottomHalf.SerializeDelta(ref writer); break;
                case 12: settingsConfidenceFactor.SerializeDelta(ref writer); break;
                case 13: settingsRansacHistorySize.SerializeDelta(ref writer); break;
                case 14: settingsFavHistorySize.SerializeDelta(ref writer); break;
                case 15: settingsFavThreshold.SerializeDelta(ref writer); break;
                case 16: settingsUseFloorPlaneDetection.SerializeDelta(ref writer); break;
                case 17: settingsNodeFetchRadius.SerializeDelta(ref writer); break;
                case 18: settingsNodeFetchLimit.SerializeDelta(ref writer); break;
                case 19: settingsTerrainTilesetMode.SerializeDelta(ref writer); break;
                case 20: settingsOSMTilesetMode.SerializeDelta(ref writer); break;
                case 21: settingsNYCTilesetMode.SerializeDelta(ref writer); break;
                case 22: settingsGoogleTilesetMode.SerializeDelta(ref writer); break;
                case 23: settingsDynamicFocusDistance.SerializeDelta(ref writer); break;
                case 24: settingsShowEyeDebug.SerializeDelta(ref writer); break;
                case 25: settingsLocalize.SerializeDelta(ref writer); break;
                case 26: settingsAnimateUserIndicators.SerializeDelta(ref writer); break;
                case 27: settingsVisibleLayers.SerializeDelta(ref writer); break;
            }
        }

        protected override void DeserializeDeltaGenerated(ref MessagePackReader reader, int key)
        {
            switch (key)
            {
                case 0: users.DeserializeDelta(ref reader); break;
                case 1: nodes.DeserializeDelta(ref reader); break;
                case 2: settingsShowPointCloud.DeserializeDelta(ref reader); break;
                case 3: settingsAnimateNodeIndicators.DeserializeDelta(ref reader); break;
                case 4: settingsLocalizationReducer.DeserializeDelta(ref reader); break;
                case 5: settingsEnableLocalizationThreshold.DeserializeDelta(ref reader); break;
                case 6: settingsFallbackToMostRecent.DeserializeDelta(ref reader); break;
                case 7: settingsPositionThreshold.DeserializeDelta(ref reader); break;
                case 8: settingsRotationThreshold.DeserializeDelta(ref reader); break;
                case 9: settingsPositionInlierThreshold.DeserializeDelta(ref reader); break;
                case 10: settingsRotationInlierThreshold.DeserializeDelta(ref reader); break;
                case 11: settingsDiscardBottomHalf.DeserializeDelta(ref reader); break;
                case 12: settingsConfidenceFactor.DeserializeDelta(ref reader); break;
                case 13: settingsRansacHistorySize.DeserializeDelta(ref reader); break;
                case 14: settingsFavHistorySize.DeserializeDelta(ref reader); break;
                case 15: settingsFavThreshold.DeserializeDelta(ref reader); break;
                case 16: settingsUseFloorPlaneDetection.DeserializeDelta(ref reader); break;
                case 17: settingsNodeFetchRadius.DeserializeDelta(ref reader); break;
                case 18: settingsNodeFetchLimit.DeserializeDelta(ref reader); break;
                case 19: settingsTerrainTilesetMode.DeserializeDelta(ref reader); break;
                case 20: settingsOSMTilesetMode.DeserializeDelta(ref reader); break;
                case 21: settingsNYCTilesetMode.DeserializeDelta(ref reader); break;
                case 22: settingsGoogleTilesetMode.DeserializeDelta(ref reader); break;
                case 23: settingsDynamicFocusDistance.DeserializeDelta(ref reader); break;
                case 24: settingsShowEyeDebug.DeserializeDelta(ref reader); break;
                case 25: settingsLocalize.DeserializeDelta(ref reader); break;
                case 26: settingsAnimateUserIndicators.DeserializeDelta(ref reader); break;
                case 27: settingsVisibleLayers.DeserializeDelta(ref reader); break;
            }
        }

        protected override void ClearDeltaGenerated()
        {
            users.ClearDelta();
            nodes.ClearDelta();
            settingsShowPointCloud.ClearDelta();
            settingsAnimateNodeIndicators.ClearDelta();
            settingsLocalizationReducer.ClearDelta();
            settingsEnableLocalizationThreshold.ClearDelta();
            settingsFallbackToMostRecent.ClearDelta();
            settingsPositionThreshold.ClearDelta();
            settingsRotationThreshold.ClearDelta();
            settingsPositionInlierThreshold.ClearDelta();
            settingsRotationInlierThreshold.ClearDelta();
            settingsDiscardBottomHalf.ClearDelta();
            settingsConfidenceFactor.ClearDelta();
            settingsRansacHistorySize.ClearDelta();
            settingsFavHistorySize.ClearDelta();
            settingsFavThreshold.ClearDelta();
            settingsUseFloorPlaneDetection.ClearDelta();
            settingsNodeFetchRadius.ClearDelta();
            settingsNodeFetchLimit.ClearDelta();
            settingsTerrainTilesetMode.ClearDelta();
            settingsOSMTilesetMode.ClearDelta();
            settingsNYCTilesetMode.ClearDelta();
            settingsGoogleTilesetMode.ClearDelta();
            settingsDynamicFocusDistance.ClearDelta();
            settingsShowEyeDebug.ClearDelta();
            settingsLocalize.ClearDelta();
            settingsAnimateUserIndicators.ClearDelta();
            settingsVisibleLayers.ClearDelta();
        }
    }

    public partial class GeoPoseRecord : SyncedRecord<GeoPoseRecord, GeoPoseRecord.InitializationData, IntLiteral2>
    {
        public class InitializationData
        {
            public Double3 ecefPosition;
            public Quaternion ecefRotation;

            public InitializationData()
            {
                ecefPosition = new Double3();
                ecefRotation = new Quaternion(0, 0, 0, 1);
            }
        }

        public GeoPoseRecord(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem)
        {
            ecefPosition = new SyncedProperty<Double3>(syncedStateSystem);
            ecefRotation = new SyncedProperty<Quaternion>(syncedStateSystem);

            SetupDeltaSubscription(ecefPosition, 0);
            SetupDeltaSubscription(ecefRotation, 1);
        }

        public override void Initialize(InitializationData initializationData)
        {
            ecefPosition.Initialize(initializationData.ecefPosition);
            ecefRotation.Initialize(initializationData.ecefRotation);
        }

        protected override void DisposeGenerated()
        {
            ecefPosition.Dispose();
            ecefRotation.Dispose();
        }

        public override void Serialize(ref MessagePackWriter writer)
        {
            ecefPosition.Serialize(ref writer);
            ecefRotation.Serialize(ref writer);
        }

        public override void Deserialize(ref MessagePackReader reader)
        {
            ecefPosition.Deserialize(ref reader);
            ecefRotation.Deserialize(ref reader);
        }

        protected override void SerializeDeltaGenerated(ref MessagePackWriter writer, int key)
        {
            switch (key)
            {
                case 0: ecefPosition.SerializeDelta(ref writer); break;
                case 1: ecefRotation.SerializeDelta(ref writer); break;
            }
        }

        protected override void DeserializeDeltaGenerated(ref MessagePackReader reader, int key)
        {
            switch (key)
            {
                case 0: ecefPosition.DeserializeDelta(ref reader); break;
                case 1: ecefRotation.DeserializeDelta(ref reader); break;
            }
        }

        protected override void ClearDeltaGenerated()
        {
            ecefPosition.ClearDelta();
            ecefRotation.ClearDelta();
        }
    }

    public partial class UserRecord : SyncedRecord<UserRecord, UserRecord.InitializationData, IntLiteral20>
    {
        public class InitializationData
        {
            public GeoPoseRecord.InitializationData geoPose;
            public bool hasGeoPose;
            public GeoPoseRecord.InitializationData settingsMenuGeoPose;
            public Vector2 settingsMenuDimensions;
            public SettingsMenuState settingsMenuOpen;
            // public bool settingsLocalize;
            // public int settingsNumThreads;
            // public int settingsSolverType;
            // public int settingsCompression;
            public Vector3 leftPalmPosition;
            public Quaternion leftPalmRotation;
            public Vector3 rightPalmPosition;
            public Quaternion rightPalmRotation;
            // public Lighting settingsLightingCondition;
            public string userName;

            public InitializationData()
            {
                geoPose = new GeoPoseRecord.InitializationData();
                hasGeoPose = false;
                settingsMenuGeoPose = new GeoPoseRecord.InitializationData();
                settingsMenuDimensions = new Vector2();
                settingsMenuOpen = SettingsMenuState.ClosedLeftPalm;
                // settingsLocalize = false;
                // settingsNumThreads = 0;
                // settingsSolverType = 0;
                // settingsCompression = 0;
                leftPalmPosition = new Vector3();
                leftPalmRotation = new Quaternion(0, 0, 0, 1);
                rightPalmPosition = new Vector3();
                rightPalmRotation = new Quaternion(0, 0, 0, 1);
                // settingsLightingCondition = Lighting.Day;
                userName = "";
            }
        }

        public UserRecord(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem)
        {
            geoPose = new GeoPoseRecord(syncedStateSystem);
            hasGeoPose = new SyncedProperty<bool>(syncedStateSystem);
            settingsMenuGeoPose = new GeoPoseRecord(syncedStateSystem);
            settingsMenuDimensions = new SyncedProperty<Vector2>(syncedStateSystem);
            settingsMenuOpen = new SyncedProperty<SettingsMenuState>(syncedStateSystem);
            // settingsLocalize = new SyncedProperty<bool>(syncedStateSystem);
            // settingsNumThreads = new SyncedProperty<int>(syncedStateSystem);
            // settingsSolverType = new SyncedProperty<int>(syncedStateSystem);
            // settingsCompression = new SyncedProperty<int>(syncedStateSystem);
            leftPalmLocalPosition = new SyncedProperty<Vector3>(syncedStateSystem);
            leftPalmLocalRotation = new SyncedProperty<Quaternion>(syncedStateSystem);
            rightPalmLocalPosition = new SyncedProperty<Vector3>(syncedStateSystem);
            rightPalmLocalRotation = new SyncedProperty<Quaternion>(syncedStateSystem);
            // settingsLightingCondition = new SyncedProperty<Lighting>(syncedStateSystem);
            userName = new SyncedProperty<string>(syncedStateSystem);

            SetupDeltaSubscription(geoPose, 0);
            SetupDeltaSubscription(hasGeoPose, 1);
            SetupDeltaSubscription(settingsMenuGeoPose, 2);
            SetupDeltaSubscription(settingsMenuDimensions, 3);
            SetupDeltaSubscription(settingsMenuOpen, 4);
            // SetupDeltaSubscription(settingsLocalize, 7);
            // SetupDeltaSubscription(settingsNumThreads, 8);
            // SetupDeltaSubscription(settingsSolverType, 9);
            // SetupDeltaSubscription(settingsCompression, 10);
            SetupDeltaSubscription(leftPalmLocalPosition, 14);
            SetupDeltaSubscription(rightPalmLocalPosition, 15);
            SetupDeltaSubscription(rightPalmLocalPosition, 16);
            SetupDeltaSubscription(rightPalmLocalRotation, 17);
            // SetupDeltaSubscription(settingsLightingCondition, 18);
            SetupDeltaSubscription(userName, 19);
        }

        public override void Initialize(InitializationData initializationData)
        {
            geoPose.Initialize(initializationData.geoPose);
            hasGeoPose.Initialize(initializationData.hasGeoPose);
            settingsMenuGeoPose.Initialize(initializationData.settingsMenuGeoPose);
            settingsMenuDimensions.Initialize(initializationData.settingsMenuDimensions);
            settingsMenuOpen.Initialize(initializationData.settingsMenuOpen);
            // settingsLocalize.Initialize(initializationData.settingsLocalize);
            // settingsNumThreads.Initialize(initializationData.settingsNumThreads);
            // settingsSolverType.Initialize(initializationData.settingsSolverType);
            // settingsCompression.Initialize(initializationData.settingsCompression);
            leftPalmLocalPosition.Initialize(initializationData.leftPalmPosition);
            leftPalmLocalRotation.Initialize(initializationData.leftPalmRotation);
            rightPalmLocalPosition.Initialize(initializationData.rightPalmPosition);
            rightPalmLocalRotation.Initialize(initializationData.rightPalmRotation);
            // settingsLightingCondition.Initialize(initializationData.settingsLightingCondition);
            userName.Initialize(initializationData.userName);
        }

        protected override void DisposeGenerated()
        {
            geoPose.Dispose();
            hasGeoPose.Dispose();
            settingsMenuGeoPose.Dispose();
            settingsMenuDimensions.Dispose();
            settingsMenuOpen.Dispose();
            // settingsLocalize.Dispose();
            // settingsNumThreads.Dispose();
            // settingsSolverType.Dispose();
            // settingsCompression.Dispose();
            leftPalmLocalPosition.Dispose();
            leftPalmLocalRotation.Dispose();
            rightPalmLocalPosition.Dispose();
            rightPalmLocalRotation.Dispose();
            // settingsLightingCondition.Dispose();
            userName.Dispose();
        }

        public override void Serialize(ref MessagePackWriter writer)
        {
            geoPose.Serialize(ref writer);
            hasGeoPose.Serialize(ref writer);
            settingsMenuGeoPose.Serialize(ref writer);
            settingsMenuDimensions.Serialize(ref writer);
            settingsMenuOpen.Serialize(ref writer);
            // settingsLocalize.Serialize(ref writer);
            // settingsNumThreads.Serialize(ref writer);
            // settingsSolverType.Serialize(ref writer);
            // settingsCompression.Serialize(ref writer);
            leftPalmLocalPosition.Serialize(ref writer);
            leftPalmLocalRotation.Serialize(ref writer);
            rightPalmLocalPosition.Serialize(ref writer);
            rightPalmLocalRotation.Serialize(ref writer);
            // settingsLightingCondition.Serialize(ref writer);
            userName.Serialize(ref writer);
        }

        public override void Deserialize(ref MessagePackReader reader)
        {
            geoPose.Deserialize(ref reader);
            hasGeoPose.Deserialize(ref reader);
            settingsMenuGeoPose.Deserialize(ref reader);
            settingsMenuDimensions.Deserialize(ref reader);
            settingsMenuOpen.Deserialize(ref reader);
            // settingsLocalize.Deserialize(ref reader);
            // settingsNumThreads.Deserialize(ref reader);
            // settingsSolverType.Deserialize(ref reader);
            // settingsCompression.Deserialize(ref reader);
            leftPalmLocalPosition.Deserialize(ref reader);
            leftPalmLocalRotation.Deserialize(ref reader);
            rightPalmLocalPosition.Deserialize(ref reader);
            rightPalmLocalRotation.Deserialize(ref reader);
            // settingsLightingCondition.Deserialize(ref reader);
            userName.Deserialize(ref reader);
        }

        protected override void SerializeDeltaGenerated(ref MessagePackWriter writer, int key)
        {
            switch (key)
            {
                case 0: geoPose.SerializeDelta(ref writer); break;
                case 1: hasGeoPose.SerializeDelta(ref writer); break;
                case 2: settingsMenuGeoPose.SerializeDelta(ref writer); break;
                case 3: settingsMenuDimensions.SerializeDelta(ref writer); break;
                case 4: settingsMenuOpen.SerializeDelta(ref writer); break;
                // case 7: settingsLocalize.SerializeDelta(ref writer); break;
                // case 8: settingsNumThreads.SerializeDelta(ref writer); break;
                // case 9: settingsSolverType.SerializeDelta(ref writer); break;
                // case 10: settingsCompression.SerializeDelta(ref writer); break;
                case 14: leftPalmLocalPosition.SerializeDelta(ref writer); break;
                case 15: leftPalmLocalRotation.SerializeDelta(ref writer); break;
                case 16: rightPalmLocalPosition.SerializeDelta(ref writer); break;
                case 17: rightPalmLocalRotation.SerializeDelta(ref writer); break;
                // case 18: settingsLightingCondition.SerializeDelta(ref writer); break;
                case 19: userName.SerializeDelta(ref writer); break;
            }
        }

        protected override void DeserializeDeltaGenerated(ref MessagePackReader reader, int key)
        {
            switch (key)
            {
                case 0: geoPose.DeserializeDelta(ref reader); break;
                case 1: hasGeoPose.DeserializeDelta(ref reader); break;
                case 2: settingsMenuGeoPose.DeserializeDelta(ref reader); break;
                case 3: settingsMenuDimensions.DeserializeDelta(ref reader); break;
                case 4: settingsMenuOpen.DeserializeDelta(ref reader); break;
                // case 7: settingsLocalize.DeserializeDelta(ref reader); break;
                // case 8: settingsNumThreads.DeserializeDelta(ref reader); break;
                // case 9: settingsSolverType.DeserializeDelta(ref reader); break;
                // case 10: settingsCompression.DeserializeDelta(ref reader); break;
                case 14: leftPalmLocalPosition.DeserializeDelta(ref reader); break;
                case 15: leftPalmLocalRotation.DeserializeDelta(ref reader); break;
                case 16: rightPalmLocalPosition.DeserializeDelta(ref reader); break;
                case 17: rightPalmLocalRotation.DeserializeDelta(ref reader); break;
                // case 18: settingsLightingCondition.DeserializeDelta(ref reader); break;
                case 19: userName.DeserializeDelta(ref reader); break;
            }
        }

        protected override void ClearDeltaGenerated()
        {
            geoPose.ClearDelta();
            hasGeoPose.ClearDelta();
            settingsMenuGeoPose.ClearDelta();
            settingsMenuDimensions.ClearDelta();
            settingsMenuOpen.ClearDelta();
            // settingsLocalize.ClearDelta();
            // settingsNumThreads.ClearDelta();
            // settingsSolverType.ClearDelta();
            // settingsCompression.ClearDelta();
            leftPalmLocalPosition.ClearDelta();
            leftPalmLocalRotation.ClearDelta();
            rightPalmLocalPosition.ClearDelta();
            rightPalmLocalRotation.ClearDelta();
            // settingsLightingCondition.ClearDelta();
            userName.ClearDelta();
        }
    }

    public partial class NodeRecord : SyncedRecord<NodeRecord, NodeRecord.InitializationData, IntLiteral16>
    {
        public class InitializationData
        {
            public HashSet<Guid> hoveringUsers;
            public Guid interactingUser;
            public GeoPoseRecord.InitializationData exhibitGeoPose;
            public bool exhibitOpen;
            public Vector2 exhibitPanelDimensions;
            public float exhibitPanelScrollPosition;
            public GeoPoseRecord.InitializationData geoPose;
            public string label;
            public string link;
            public float labelScale;
            public float labelWidth;
            public float labelHeight;
            public LinkType linkType;
            public LabelType labelType;
            public Guid layer;

            public InitializationData()
            {
                hoveringUsers = new HashSet<Guid>();
                interactingUser = Guid.Empty;
                exhibitGeoPose = new GeoPoseRecord.InitializationData();
                exhibitOpen = false;
                exhibitPanelDimensions = new Vector2();
                exhibitPanelScrollPosition = 0;
                geoPose = new GeoPoseRecord.InitializationData();
                link = "";
                labelScale = 1;
                labelWidth = 0;
                labelHeight = 0;
                linkType = LinkType.None;
                label = "";
                layer = Guid.Empty;
            }
        }

        public NodeRecord(SyncedStateSystem syncedStateSystem) : base(syncedStateSystem)
        {
            hoveringUsers = new SyncedSet<Guid>(syncedStateSystem);
            interactingUser = new SyncedProperty<Guid>(syncedStateSystem);
            exhibitGeoPose = new GeoPoseRecord(syncedStateSystem);
            exhibitOpen = new SyncedProperty<bool>(syncedStateSystem);
            exhibitPanelDimensions = new SyncedProperty<Vector2>(syncedStateSystem);
            exhibitPanelScrollPosition = new SyncedProperty<float>(syncedStateSystem);
            geoPose = new GeoPoseRecord(syncedStateSystem);
            link = new SyncedProperty<string>(syncedStateSystem);
            labelScale = new SyncedProperty<float>(syncedStateSystem);
            labelWidth = new SyncedProperty<float>(syncedStateSystem);
            labelHeight = new SyncedProperty<float>(syncedStateSystem);
            linkType = new SyncedProperty<LinkType>(syncedStateSystem);
            labelType = new SyncedProperty<LabelType>(syncedStateSystem);
            label = new SyncedProperty<string>(syncedStateSystem);
            layer = new SyncedProperty<Guid>(syncedStateSystem);

            SetupDeltaSubscription(hoveringUsers, 0);
            SetupDeltaSubscription(interactingUser, 1);
            SetupDeltaSubscription(exhibitGeoPose, 2);
            SetupDeltaSubscription(exhibitPanelDimensions, 3);
            SetupDeltaSubscription(exhibitPanelScrollPosition, 4);
            SetupDeltaSubscription(exhibitOpen, 5);
            SetupDeltaSubscription(geoPose, 6);
            SetupDeltaSubscription(link, 8);
            SetupDeltaSubscription(labelScale, 9);
            SetupDeltaSubscription(labelWidth, 10);
            SetupDeltaSubscription(labelHeight, 11);
            SetupDeltaSubscription(linkType, 12);
            SetupDeltaSubscription(label, 13);
            SetupDeltaSubscription(labelType, 14);
            SetupDeltaSubscription(layer, 15);
        }

        public override void Initialize(InitializationData initializationData)
        {
            hoveringUsers.Initialize(initializationData.hoveringUsers);
            interactingUser.Initialize(initializationData.interactingUser);
            exhibitGeoPose.Initialize(initializationData.exhibitGeoPose);
            exhibitOpen.Initialize(initializationData.exhibitOpen);
            exhibitPanelDimensions.Initialize(initializationData.exhibitPanelDimensions);
            exhibitPanelScrollPosition.Initialize(initializationData.exhibitPanelScrollPosition);
            geoPose.Initialize(initializationData.geoPose);
            link.Initialize(initializationData.link);
            labelScale.Initialize(initializationData.labelScale);
            labelWidth.Initialize(initializationData.labelWidth);
            labelHeight.Initialize(initializationData.labelHeight);
            linkType.Initialize(initializationData.linkType);
            label.Initialize(initializationData.label);
            labelType.Initialize(initializationData.labelType);
            layer.Initialize(initializationData.layer);
        }

        protected override void DisposeGenerated()
        {
            hoveringUsers.Dispose();
            interactingUser.Dispose();
            exhibitGeoPose.Dispose();
            exhibitOpen.Dispose();
            exhibitPanelDimensions.Dispose();
            exhibitPanelScrollPosition.Dispose();
            geoPose.Dispose();
            link.Dispose();
            labelScale.Dispose();
            labelWidth.Dispose();
            labelHeight.Dispose();
            linkType.Dispose();
            label.Dispose();
            labelType.Dispose();
            layer.Dispose();
        }

        public override void Serialize(ref MessagePackWriter writer)
        {
            hoveringUsers.Serialize(ref writer);
            interactingUser.Serialize(ref writer);
            exhibitGeoPose.Serialize(ref writer);
            exhibitOpen.Serialize(ref writer);
            exhibitPanelDimensions.Serialize(ref writer);
            exhibitPanelScrollPosition.Serialize(ref writer);
            geoPose.Serialize(ref writer);
            link.Serialize(ref writer);
            labelScale.Serialize(ref writer);
            labelWidth.Serialize(ref writer);
            labelHeight.Serialize(ref writer);
            linkType.Serialize(ref writer);
            label.Serialize(ref writer);
            labelType.Serialize(ref writer);
            layer.Serialize(ref writer);
        }

        public override void Deserialize(ref MessagePackReader reader)
        {
            hoveringUsers.Deserialize(ref reader);
            interactingUser.Deserialize(ref reader);
            exhibitGeoPose.Deserialize(ref reader);
            exhibitOpen.Deserialize(ref reader);
            exhibitPanelDimensions.Deserialize(ref reader);
            exhibitPanelScrollPosition.Deserialize(ref reader);
            geoPose.Deserialize(ref reader);
            link.Deserialize(ref reader);
            labelScale.Deserialize(ref reader);
            labelWidth.Deserialize(ref reader);
            labelHeight.Deserialize(ref reader);
            linkType.Deserialize(ref reader);
            label.Deserialize(ref reader);
            labelType.Deserialize(ref reader);
            layer.Deserialize(ref reader);
        }

        protected override void SerializeDeltaGenerated(ref MessagePackWriter writer, int key)
        {
            switch (key)
            {
                case 0: hoveringUsers.SerializeDelta(ref writer); break;
                case 1: interactingUser.SerializeDelta(ref writer); break;
                case 2: exhibitGeoPose.SerializeDelta(ref writer); break;
                case 3: exhibitPanelDimensions.SerializeDelta(ref writer); break;
                case 4: exhibitPanelScrollPosition.SerializeDelta(ref writer); break;
                case 5: exhibitOpen.SerializeDelta(ref writer); break;
                case 6: geoPose.SerializeDelta(ref writer); break;
                case 8: link.SerializeDelta(ref writer); break;
                case 9: labelScale.SerializeDelta(ref writer); break;
                case 10: labelWidth.SerializeDelta(ref writer); break;
                case 11: labelHeight.SerializeDelta(ref writer); break;
                case 12: linkType.SerializeDelta(ref writer); break;
                case 13: label.SerializeDelta(ref writer); break;
                case 14: labelType.SerializeDelta(ref writer); break;
                case 15: layer.SerializeDelta(ref writer); break;
            }
        }

        protected override void DeserializeDeltaGenerated(ref MessagePackReader reader, int key)
        {
            switch (key)
            {
                case 0: hoveringUsers.DeserializeDelta(ref reader); break;
                case 1: interactingUser.DeserializeDelta(ref reader); break;
                case 2: exhibitGeoPose.DeserializeDelta(ref reader); break;
                case 3: exhibitPanelDimensions.DeserializeDelta(ref reader); break;
                case 4: exhibitPanelScrollPosition.DeserializeDelta(ref reader); break;
                case 5: exhibitOpen.DeserializeDelta(ref reader); break;
                case 6: geoPose.DeserializeDelta(ref reader); break;
                case 8: link.DeserializeDelta(ref reader); break;
                case 9: labelScale.DeserializeDelta(ref reader); break;
                case 10: labelWidth.DeserializeDelta(ref reader); break;
                case 11: labelHeight.DeserializeDelta(ref reader); break;
                case 12: linkType.DeserializeDelta(ref reader); break;
                case 13: label.DeserializeDelta(ref reader); break;
                case 14: labelType.DeserializeDelta(ref reader); break;
                case 15: layer.DeserializeDelta(ref reader); break;
            }
        }

        protected override void ClearDeltaGenerated()
        {
            hoveringUsers.ClearDelta();
            interactingUser.ClearDelta();
            exhibitGeoPose.ClearDelta();
            exhibitOpen.ClearDelta();
            exhibitPanelDimensions.ClearDelta();
            exhibitPanelScrollPosition.ClearDelta();
            geoPose.ClearDelta();
            link.ClearDelta();
            labelScale.ClearDelta();
            labelWidth.ClearDelta();
            labelHeight.ClearDelta();
            linkType.ClearDelta();
            label.ClearDelta();
            labelType.ClearDelta();
            layer.ClearDelta();
        }
    }
}
