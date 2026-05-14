using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using Placeframe.Core;
using Unity.Mathematics;
using UnityEngine;
using ObserveThing;
using System.Collections.Generic;

namespace Plerion.MakeItSing
{
    public class LocalizationManager : MonoBehaviour
    {
        private double MAP_LOAD_RADIUS = 100;
        private TaskHandle _updateMapsTask = TaskHandle.Complete;
        private IDisposable _subscriptions;

        private void Awake()
        {
            _subscriptions = new ComposedDisposable(
                StateObservables.SubscribeOperationsRecursive(HandleRoughGrainedLocationChanged, App.state.roughGrainedLocation, App.state.loggedIn),
                App.state.loggedIn
                    .ObservableSkipWhile(() => !App.state.loggedIn.value)
                    .Subscribe(
                        onNext: loggedIn =>
                        {
                            if (!loggedIn && VisualPositioningSystem.Localizing)
                                VisualPositioningSystem.StopLocalizing();
                        }
                    )
            );
        }

        private void OnDestroy()
        {
            _updateMapsTask.Cancel();
            _subscriptions.Dispose();
        }

        private void HandleRoughGrainedLocationChanged(IReadOnlyList<IStateOperation> args)
        {
            if (!App.state.loggedIn.value)
                return;

            _updateMapsTask.Cancel();
            _updateMapsTask = TaskHandle.Execute(token => UpdateMaps(App.state.roughGrainedLocation.value.x, App.state.roughGrainedLocation.value.y, token));
        }

        private async UniTask UpdateMaps(double latitude, double longitude, CancellationToken cancellationToken = default)
        {
            // Determine ground level (height above WGS84 ellipsoid) at the specified latitude and longitude
            // SceneReferences.GroundTileset.suspendUpdate = false;
            // var heightSamplingResult = await SceneReferences.GroundTileset.SampleHeightMostDetailed(
            //     new double3(longitude, latitude, 0)
            // );

            // cancellationToken.ThrowIfCancellationRequested();

            // var groundLevelHeightAboveWGS84Ellipsoid = heightSamplingResult.longitudeLatitudeHeightPositions[0].z;
            // SceneReferences.GroundTileset.suspendUpdate = true;

            float groundLevelHeightAboveWGS84Ellipsoid = 0;

            // Convert cartographic coordinates to ECEF coordinates, and use the ENU frame at that location for orientation
            var ecefPosition = WGS84.CartographicToEcef(
                CartographicCoordinates.FromLongitudeLatitudeHeight(
                    longitude,
                    latitude,
                    groundLevelHeightAboveWGS84Ellipsoid
                )
            );

            ecefPosition = new double3(0, 0, 0);

            await VisualPositioningSystem.SetLocalizationMaps(ecefPosition, MAP_LOAD_RADIUS, cancellationToken);

            if (App.state.loggedIn.value && VisualPositioningSystem.LoadedMapCount > 0 && !VisualPositioningSystem.Localizing)
                VisualPositioningSystem.StartLocalizing(1f);
        }
    }
}