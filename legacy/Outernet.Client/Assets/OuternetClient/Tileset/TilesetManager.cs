using System;
using System.Collections.Generic;
using CesiumForUnity;
using Cysharp.Threading.Tasks;
using Outernet.Shared;
using Unity.Mathematics;
using UnityEngine;
using R3;
using System.Linq;
using R3.Triggers;
using Unity.VisualScripting;

namespace Outernet.Client
{
    public static class TilesetManager
    {
        private sealed class TilesetWrapper : IDisposable
        {
            public Cesium3DTileset cesium;
            private ReactiveProperty<TilesetMode> modeProperty = new(TilesetMode.Disable);
            public IDisposable connectionStatusSubscription;
            public IDisposable modeSubscription;

            public TilesetWrapper(Cesium3DTileset cesium)
            {
                this.cesium = cesium;

                connectionStatusSubscription = ConnectionManager.RoomConnectionStatusStream.Subscribe(status =>
                {
                    if (status == ConnectionManager.RoomConnectionStatus.Connected)
                    {
                        switch (cesium.name)
                        {
                            case "Cesium World Terrain":
                                modeSubscription = App.State_Old.settingsTerrainTilesetMode.Subscribe(mode =>
                                {
                                    modeProperty.Value = mode.Value;
                                });
                                break;
                            case "Cesium OSM Buildings":
                                modeSubscription = App.State_Old.settingsOSMTilesetMode.Subscribe(mode =>
                                {
                                    modeProperty.Value = mode.Value;
                                });
                                break;
                            case "New York City 3D Buildings":
                                modeSubscription = App.State_Old.settingsNYCTilesetMode.Subscribe(mode =>
                                {
                                    modeProperty.Value = mode.Value;
                                });
                                break;
                        }
                    }
                    else
                    {
                        if (modeSubscription != null)
                        {
                            modeSubscription?.Dispose();
                            modeSubscription = null;
                        }
                    }
                });

                cesium.OnTileGameObjectCreated += go =>
                {
                    DisposableBag tileSubscriptions = new();
                    foreach (var meshRenderer in go.GetComponentsInChildren<MeshRenderer>(true))
                    {
                        tileSubscriptions.Add(SetupSubscription(meshRenderer));
                    }
                };
            }

            IDisposable SetupSubscription(MeshRenderer meshRenderer)
                => modeProperty.Subscribe(mode =>
                {
                    if (meshRenderer.IsDestroyed()) return;

                    switch (mode)
                    {
                        case TilesetMode.Show:
                            meshRenderer.enabled = true;
                            meshRenderer.material.shader = defaultShader;
                            break;
                        case TilesetMode.Disable:
                            meshRenderer.enabled = false;
                            break;
                        case TilesetMode.Hide:
#if UNITY_EDITOR
                            meshRenderer.enabled = false;
#else
                            meshRenderer.enabled = true;
#endif
                            meshRenderer.material.shader = depthOnlyShader;
                            break;
                    }
                });

            public void Dispose()
            {
                connectionStatusSubscription?.Dispose();
                modeSubscription?.Dispose();
            }
        }

        private static readonly Dictionary<string, TilesetWrapper> tilesets = new();
        private static Shader depthOnlyShader;
        private static Shader defaultShader;

        public static void Initialize()
        {
            foreach (var c3d in UnityEngine.Object.FindObjectsByType<Cesium3DTileset>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                tilesets[c3d.name] = new TilesetWrapper(c3d);

                if (c3d.name == "Cesium World Terrain" ||
                    c3d.name == "Cesium OSM Buildings" ||
                    c3d.name == "New York City 3D Buildings")
                {
                    c3d.gameObject.SetActive(true);
                }
            }

            depthOnlyShader = Resources.Load<Shader>("DepthOnly");
            defaultShader = tilesets["Cesium OSM Buildings"].cesium.opaqueMaterial.shader;
        }

        public static async UniTask<double> GetHeight(double latitude, double longitude)
        {
            var h = await tilesets["Cesium World Terrain"]
                .cesium.SampleHeightMostDetailed(new double3(longitude, latitude, 0));
            return h.longitudeLatitudeHeightPositions[0].z;
        }
    }
}
