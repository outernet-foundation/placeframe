using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

using UnityEngine;
using Unity.Mathematics;

using Cysharp.Threading.Tasks;

using FofX;
using FofX.Stateful;

using CesiumForUnity;
using PlerionApiClient.Model;

namespace Outernet.MapRegistrationTool
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
                App.state.loggedIn,
                App.state.location,
                App.state.settings.nodeFetchRadius
            );
        }

        private void OnDestroy()
        {
            _updateLocationAndContentTask.Cancel();
        }

        private void HandleLocationChanged(NodeChangeEventArgs args)
        {
            if (!App.state.loggedIn.value)
                return;

            _updateLocationAndContentTask.Cancel();

            if (_loadedLocation.Equals(App.state.location.value) &&
                _loadedDrawDistance == App.state.settings.nodeFetchRadius.value)
            {
                return;
            }

            if (!App.state.location.value.HasValue)
            {
                _loadedLocation = App.state.location.value;
                _loadedDrawDistance = App.state.settings.nodeFetchRadius.value;
                App.ExecuteActionOrDelay(new ClearSceneObjectsAction());
                return;
            }

            _updateLocationAndContentTask = TaskHandle.Execute(token => HandleUnsavedChangesAndLoadContent(
                App.state.location.value.Value,
                App.state.settings.nodeFetchRadius.value,
                Utility.GetPreviousValue(App.state.location, args.changes),
                Utility.GetPreviousValue(App.state.settings.nodeFetchRadius, args.changes),
                token
            ));
        }

        private async UniTask HandleUnsavedChangesAndLoadContent(double2 location, float drawDistance, double2? previousLocation, float previousDrawDistance, CancellationToken cancellationToken = default)
        {
            if (App.state.hasUnsavedChanges.value)
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
                    App.state.location.ExecuteSetOrDelay(previousLocation);
                    App.state.settings.nodeFetchRadius.ExecuteSetOrDelay(previousDrawDistance);
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

                    App.state.saveRequested.ExecuteSetOrDelay(true);
                    await UniTask.WaitUntil(() => !App.state.hasUnsavedChanges.value);

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

            var heights = await CesiumAPI.GetHeights(new List<(double latitude, double longitude)> { (latitude, longitude) });
            cancellationToken.ThrowIfCancellationRequested();

            if (heights == null || heights.Count == 0)
                throw new Exception("No heights found.");

            var height = heights[0];
            var ecefCoordinates = CesiumWgs84Ellipsoid.LongitudeLatitudeHeightToEarthCenteredEarthFixed(new double3(longitude, latitude, height));

            App.state.ecefToUnityWorldMatrix.ExecuteSetOrDelay(
                math.inverse(Double4x4.FromTranslationRotation(
                    ecefCoordinates,
                    MapRegistrationTool.Utility.GetEUNRotationFromECEFPosition(ecefCoordinates)
                ))
            );

            List<LocalizationMapRead> maps = default;

            maps = await App.API.GetLocalizationMapsAsync();

            await UniTask.SwitchToMainThread(cancellationToken);

            App.ExecuteActionOrDelay(new SetMapsAction(maps.ToArray()));

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
