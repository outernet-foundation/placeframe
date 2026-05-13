using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

using UnityEngine;
using Unity.Mathematics;

using Cysharp.Threading.Tasks;

using FofX;
using FofX.Stateful;

using Outernet.Client.Location;
using CesiumForUnity;
using PlaceframeApiClient.Model;
using PlaceframeApiClient.Api;
using PlaceframeApiClient.Client;
using Placeframe.Core;
using System.Threading.Tasks;

namespace Outernet.Client.AuthoringTools
{
    public class LocationContentManager : MonoBehaviour
    {
        private TaskHandle _updateLocationAndContentTask = TaskHandle.Complete;
        private double2? _loadedLocation;
        private float _loadedDrawDistance;

        private void Awake()
        {
            App.RegisterObserver(
                HandleLocationChanged,
                App.state.apiReady,
                App.state.authoringTools.location,
                App.state.authoringTools.settings.nodeFetchRadius
            );
        }

        private void OnDestroy()
        {
            _updateLocationAndContentTask.Cancel();
        }

        private void HandleLocationChanged(NodeChangeEventArgs args)
        {
            if (!App.state.apiReady.value)
                return;

            _updateLocationAndContentTask.Cancel();

            if (_loadedLocation.Equals(App.state.authoringTools.location.value) &&
                _loadedDrawDistance == App.state.authoringTools.settings.nodeFetchRadius.value)
            {
                return;
            }

            if (!App.state.authoringTools.location.value.HasValue)
            {
                _loadedLocation = App.state.authoringTools.location.value;
                _loadedDrawDistance = App.state.authoringTools.settings.nodeFetchRadius.value;
                App.ExecuteActionOrDelay(new ClearSceneObjectsAction());
                return;
            }

            _updateLocationAndContentTask = TaskHandle.Execute(token => HandleUnsavedChangesAndLoadContent(
                App.state.authoringTools.location.value.Value,
                App.state.authoringTools.settings.nodeFetchRadius.value,
                Utility.GetPreviousValue(App.state.authoringTools.location, args.changes),
                Utility.GetPreviousValue(App.state.authoringTools.settings.nodeFetchRadius, args.changes),
                token
            ));
        }

        private async UniTask HandleUnsavedChangesAndLoadContent(double2 location, float drawDistance, double2? previousLocation, float previousDrawDistance, CancellationToken cancellationToken = default)
        {
            if (App.state.authoringTools.hasUnsavedChanges.value)
            {
                var dialog = Dialogs.UnsavedChangesDialog(
                    title: "Unsaved Changes",
                    text: "Changing locations or node fetch distance will overwrite unsaved changes. \nWould you like to save before changing locations?",
                    allowCancel: true
                );

                var dialogProps = (Dialogs.UnsavedChangesDialogProps)dialog.props;

                cancellationToken.Register(() =>
                {
                    if (dialog == null)
                        return;

                    Destroy(dialog.gameObject);
                });

                await UniTask.WaitUntil(() => dialogProps.status.value != DialogStatus.Pending, cancellationToken: cancellationToken);

                if (dialogProps.status.value == DialogStatus.Canceled)
                {
                    App.state.authoringTools.location.ExecuteSetOrDelay(previousLocation);
                    App.state.authoringTools.settings.nodeFetchRadius.ExecuteSetOrDelay(previousDrawDistance);
                    return;
                }

                if (dialogProps.saveRequested.value)
                {
                    var loadingDialog = Dialogs.Show(
                        title: "Saving",
                        allowCancel: false,
                        minimumWidth: 200,
                        constructControls: props => UIBuilder.Text("Please wait", horizontalAlignment: TMPro.HorizontalAlignmentOptions.Center)
                    );

                    cancellationToken.Register(() =>
                    {
                        if (loadingDialog == null)
                            return;

                        Destroy(loadingDialog.gameObject);
                    });

                    App.state.authoringTools.saveRequested.ExecuteSetOrDelay(true);
                    await UniTask.WaitUntil(() => !App.state.authoringTools.hasUnsavedChanges.value);

                    Destroy(loadingDialog.gameObject);
                }
            }

            _loadedLocation = location;
            _loadedDrawDistance = drawDistance;

            await LoadContent(location.x, location.y, drawDistance, cancellationToken);
        }

        private async UniTask LoadContent(double latitude, double longitude, double radius, CancellationToken cancellationToken = default)
        {
            App.ExecuteActionOrDelay(new SetLocationContentLoadedAction(false));

            var dialog = Dialogs.Show(
                title: "Loading Content",
                allowCancel: false,
                minimumWidth: 250,
                constructControls: props => UIBuilder.Text("Please wait", horizontalAlignment: TMPro.HorizontalAlignmentOptions.Center)
            );

            cancellationToken.Register(() =>
            {
                if (dialog == null)
                    return;

                Destroy(dialog.gameObject);
            });

            // Determine ground level (height above WGS84 ellipsoid) at the specified latitude and longitude
            SceneReferences.GroundTileset.suspendUpdate = false;
            var heightSamplingResult = await SceneReferences.GroundTileset.SampleHeightMostDetailed(
                new double3(longitude, latitude, 0)
            );
            var groundLevelHeightAboveWGS84Ellipsoid = heightSamplingResult.longitudeLatitudeHeightPositions[0].z;
            SceneReferences.GroundTileset.suspendUpdate = true;

            // Convert cartographic coordinates to ECEF coordinates, and use the ENU frame at that location for orientation
            var ecefPosition = WGS84.CartographicToEcef(
                CartographicCoordinates.FromLongitudeLatitudeHeight(
                    longitude,
                    latitude,
                    groundLevelHeightAboveWGS84Ellipsoid
                )
            );
            var ecefRotation = WGS84.GetEastNorthUpFrameInEcef(ecefPosition);

            // Set Cesium georeference to that position and orientation
            SceneReferences.CesiumGeoreference.SetOriginEarthCenteredEarthFixed(
                ecefPosition.x,
                ecefPosition.y,
                ecefPosition.z
            );
            // SceneReferences.CesiumGeoreference.transform.rotation = math.inverse(ecefRotation.ToQuaternion());

            // Update the application's ECEF to Unity world matrix.
            var (ecefPositionUnityBasis, ecefRotationUnityBasis) = LocationUtilities.ChangeBasisUnityFromEcef(ecefPosition, ecefRotation);
            var ecefFromUnityTransformUnityBasis = Double4x4.FromTranslationRotation(
                ecefPositionUnityBasis,
                ecefRotationUnityBasis
            );

            var unityFromEcefTransformUnityBasis = math.inverse(ecefFromUnityTransformUnityBasis);
            VisualPositioningSystem.SetEcefToUnityTransform(unityFromEcefTransformUnityBasis);

            List<LocalizationMapRead> maps = default;
            List<NodeRead> nodes = null;
            List<GroupRead> nodeGroups = null;

            await UniTask.WhenAll(
                App.API.GetLocalizationMapsAsync().ContinueWith(x => maps = x),
                App.API.GetLocalizationMapsAsync(positionX: ecefPosition.x, positionY: ecefPosition.y, positionZ: ecefPosition.z, radius: radius),
                App.API.GetNodesAsync(positionX: ecefPosition.x, positionY: ecefPosition.y, positionZ: ecefPosition.z, radius: radius)
                    .ContinueWith(x =>
                    {
                        nodes = x;
                        return GetNodeGroupsRecursive(x);
                    })
                    .ContinueWith(x => nodeGroups = x)
            );

            await UniTask.SwitchToMainThread(cancellationToken);

            App.ExecuteActionOrDelay(
                new SetMapsAction(maps.ToArray()),
                new SetNodesAction(nodes.ToArray()),
                new SetNodeGroupsAction(nodeGroups.ToArray())
            );

            Destroy(dialog.gameObject);

            App.ExecuteActionOrDelay(new SetLocationContentLoadedAction(true));
        }

        private async UniTask<List<GroupRead>> GetNodeGroupsRecursive(List<NodeRead> nodes, CancellationToken cancellationToken = default)
        {
            var groups = new List<GroupRead>();

            var directGroups = await App.API.GetGroupsAsync(
                nodes.Where(x => x.ParentId.HasValue)
                    .Select(x => x.ParentId.Value)
                    .Distinct()
                    .ToList()
            );

            groups.AddRange(directGroups);

            cancellationToken.ThrowIfCancellationRequested();

            while (groups.Any(x => x.ParentId.HasValue && !groups.Any(y => y.Id == x.ParentId)))
            {
                var recursiveGroups = await App.API.GetGroupsAsync(
                    groups.Where(x => x.ParentId.HasValue && !groups.Any(y => y.Id == x.ParentId))
                        .Select(x => x.ParentId.Value)
                        .Distinct()
                        .ToList()
                );

                groups.AddRange(recursiveGroups);

                cancellationToken.ThrowIfCancellationRequested();
            }

            return groups;
        }
    }
}
