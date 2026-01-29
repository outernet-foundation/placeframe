// https://github.com/dotnet/project-system/issues/5551
#nullable enable

using System;
using MessagePack;
using UnityEngine;

namespace Outernet.Shared
{
    public enum SettingsMenuState
    {
        OpenLeftPalm,
        OpenRightPalm,
        ClosedLeftPalm,
        ClosedRightPalm,
    }

    public enum LocalizationReducer
    {
        None,
        FAV,
        RANSAC,
    }

    public enum LinkType
    {
        None,
        Address,
        Annotation,
        ImageList,
    }

    public enum LabelType
    {
        Automatic,
        Text,
        Image,
    }

    public static class Conversions
    {
        public static LinkType LinkType(PlaceframeApiClient.Model.LinkType linkType)
        {
            return linkType switch
            {
                PlaceframeApiClient.Model.LinkType.None => Shared.LinkType.None,
                PlaceframeApiClient.Model.LinkType.Address => Shared.LinkType.Address,
                PlaceframeApiClient.Model.LinkType.Annotation => Shared.LinkType.Annotation,
                PlaceframeApiClient.Model.LinkType.ImageList => Shared.LinkType.ImageList,
                _ => throw new ArgumentOutOfRangeException(nameof(linkType), linkType, null),
            };
        }

        public static PlaceframeApiClient.Model.LinkType LinkType(LinkType linkType)
        {
            return linkType switch
            {
                Shared.LinkType.None => PlaceframeApiClient.Model.LinkType.None,
                Shared.LinkType.Address => PlaceframeApiClient.Model.LinkType.Address,
                Shared.LinkType.Annotation => PlaceframeApiClient.Model.LinkType.Annotation,
                Shared.LinkType.ImageList => PlaceframeApiClient.Model.LinkType.ImageList,
                _ => throw new ArgumentOutOfRangeException(nameof(linkType), linkType, null),
            };
        }

        public static LabelType LabelType(PlaceframeApiClient.Model.LabelType labelType)
        {
            return labelType switch
            {
                PlaceframeApiClient.Model.LabelType.Automatic => Shared.LabelType.Automatic,
                PlaceframeApiClient.Model.LabelType.Image => Shared.LabelType.Image,
                PlaceframeApiClient.Model.LabelType.Text => Shared.LabelType.Text,
                _ => throw new ArgumentOutOfRangeException(nameof(labelType), labelType, null),
            };
        }

        public static PlaceframeApiClient.Model.LabelType LabelType(LabelType labelType)
        {
            return labelType switch
            {
                Shared.LabelType.Automatic => PlaceframeApiClient.Model.LabelType.Automatic,
                Shared.LabelType.Image => PlaceframeApiClient.Model.LabelType.Image,
                Shared.LabelType.Text => PlaceframeApiClient.Model.LabelType.Text,
                _ => throw new ArgumentOutOfRangeException(nameof(labelType), labelType, null),
            };
        }
    }

    public enum TilesetMode
    {
        Disable,
        Hide,
        Show,
    }

    public partial class RoomRecord
    {
        [Key(0)]
        public SyncedDictionary<Guid, UserRecord, UserRecord.InitializationData> users { get; private set; }

        [Key(1)]
        public SyncedDictionary<Guid, NodeRecord, NodeRecord.InitializationData> nodes { get; private set; }

        [Key(2)]
        public SyncedProperty<bool> settingsShowPointCloud { get; private set; }

        [Key(3)]
        public SyncedProperty<bool> settingsAnimateNodeIndicators { get; private set; }

        [Key(4)]
        public SyncedProperty<LocalizationReducer> settingsLocalizationReducer { get; private set; }

        [Key(5)]
        public SyncedProperty<bool> settingsEnableLocalizationThreshold { get; private set; }

        [Key(6)]
        public SyncedProperty<bool> settingsFallbackToMostRecent { get; private set; }

        [Key(7)]
        public SyncedProperty<float> settingsPositionThreshold { get; private set; }

        [Key(8)]
        public SyncedProperty<float> settingsRotationThreshold { get; private set; }

        [Key(9)]
        public SyncedProperty<float> settingsPositionInlierThreshold { get; private set; }

        [Key(10)]
        public SyncedProperty<float> settingsRotationInlierThreshold { get; private set; }

        [Key(11)]
        public SyncedProperty<bool> settingsDiscardBottomHalf { get; private set; }

        [Key(12)]
        public SyncedProperty<float> settingsConfidenceFactor { get; private set; }

        [Key(13)]
        public SyncedProperty<int> settingsRansacHistorySize { get; private set; }

        [Key(14)]
        public SyncedProperty<int> settingsFavHistorySize { get; private set; }

        [Key(15)]
        public SyncedProperty<float> settingsFavThreshold { get; private set; }

        [Key(16)]
        public SyncedProperty<bool> settingsUseFloorPlaneDetection { get; private set; }

        [Key(17)]
        public SyncedProperty<float> settingsNodeFetchRadius { get; private set; }

        [Key(18)]
        public SyncedProperty<int> settingsNodeFetchLimit { get; private set; }

        [Key(19)]
        public SyncedProperty<TilesetMode> settingsTerrainTilesetMode { get; private set; }

        [Key(20)]
        public SyncedProperty<TilesetMode> settingsOSMTilesetMode { get; private set; }

        [Key(21)]
        public SyncedProperty<TilesetMode> settingsNYCTilesetMode { get; private set; }

        [Key(22)]
        public SyncedProperty<TilesetMode> settingsGoogleTilesetMode { get; private set; }

        [Key(23)]
        public SyncedProperty<bool> settingsDynamicFocusDistance { get; private set; }

        [Key(24)]
        public SyncedProperty<bool> settingsShowEyeDebug { get; private set; }

        [Key(25)]
        public SyncedProperty<bool> settingsLocalize { get; private set; }

        [Key(26)]
        public SyncedProperty<bool> settingsAnimateUserIndicators { get; private set; }

        [Key(27)]
        public SyncedSet<Guid> settingsVisibleLayers { get; private set; }
    }

    public partial class GeoPoseRecord
    {
        [Key(0)]
        public SyncedProperty<Double3> ecefPosition { get; private set; }

        [Key(1)]
        public SyncedProperty<Quaternion> ecefRotation { get; private set; }
    }

    public partial class UserRecord
    {
        [Key(0)]
        public GeoPoseRecord geoPose { get; private set; }

        [Key(1)]
        public SyncedProperty<bool> hasGeoPose { get; private set; }

        [Key(2)]
        public GeoPoseRecord settingsMenuGeoPose { get; private set; }

        [Key(3)]
        public SyncedProperty<Vector2> settingsMenuDimensions { get; private set; }

        [Key(4)]
        public SyncedProperty<SettingsMenuState> settingsMenuOpen { get; private set; }

        // [Key(5)] public SyncedProperty<bool> settingsShowPointCloud { get; private set; }
        // [Key(6)] public SyncedProperty<bool> settingsAnimateIndicators { get; private set; }
        // [Key(7)] public SyncedProperty<bool> settingsLocalize { get; private set; }
        // [Key(8)] public SyncedProperty<int> settingsNumThreads { get; private set; }
        // [Key(9)] public SyncedProperty<int> settingsSolverType { get; private set; }
        // [Key(10)] public SyncedProperty<int> settingsCompression { get; private set; }
        // [Key(11)] public SyncedProperty<LocalizationReducer> settingsLocalizationReducer { get; private set; }
        // [Key(12)] public SyncedProperty<Vector3> settingsMenuLocalPosition { get; private set; }
        // [Key(13)] public SyncedProperty<Quaternion> settingsMenuLocalRotation { get; private set; }
        [Key(14)]
        public SyncedProperty<Vector3> leftPalmLocalPosition { get; private set; }

        [Key(15)]
        public SyncedProperty<Quaternion> leftPalmLocalRotation { get; private set; }

        [Key(16)]
        public SyncedProperty<Vector3> rightPalmLocalPosition { get; private set; }

        [Key(17)]
        public SyncedProperty<Quaternion> rightPalmLocalRotation { get; private set; }

        // [Key(18)] public SyncedProperty<Lighting> settingsLightingCondition { get; private set; }
        [Key(19)]
        public SyncedProperty<string> userName { get; private set; }
    }

    public partial class NodeRecord
    {
        [Key(0)]
        public SyncedSet<Guid> hoveringUsers { get; private set; }

        [Key(1)]
        public SyncedProperty<Guid> interactingUser { get; private set; }

        [Key(2)]
        public GeoPoseRecord exhibitGeoPose { get; private set; }

        [Key(3)]
        public SyncedProperty<Vector2> exhibitPanelDimensions { get; private set; }

        [Key(4)]
        public SyncedProperty<float> exhibitPanelScrollPosition { get; private set; }

        [Key(5)]
        public SyncedProperty<bool> exhibitOpen { get; private set; }

        [Key(6)]
        public GeoPoseRecord geoPose { get; private set; }

        // [Key(7)] public SyncedProperty<string> label { get; private set; }
        [Key(8)]
        public SyncedProperty<string> link { get; private set; }

        [Key(9)]
        public SyncedProperty<float> labelScale { get; private set; }

        [Key(10)]
        public SyncedProperty<float> labelWidth { get; private set; }

        [Key(11)]
        public SyncedProperty<float> labelHeight { get; private set; }

        [Key(12)]
        public SyncedProperty<LinkType> linkType { get; private set; }

        [Key(13)]
        public SyncedProperty<string> label { get; private set; }

        [Key(14)]
        public SyncedProperty<LabelType> labelType { get; private set; }

        [Key(15)]
        public SyncedProperty<Guid> layer { get; private set; }
    }

    [MessagePackObject]
    public struct Double3
    {
        public Double3(double x, double y, double z)
        {
            this.x = x;
            this.y = y;
            this.z = z;
        }

        [Key(0)]
        public double x;

        [Key(1)]
        public double y;

        [Key(2)]
        public double z;
    }
}
