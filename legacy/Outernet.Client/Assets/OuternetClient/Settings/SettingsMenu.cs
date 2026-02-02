using UnityEngine.UI;
using TMPro;
using UnityEngine;
using Outernet.Shared;
using R3;
using System.Collections.Generic;
using System.Linq;
using CesiumForUnity;
using Outernet.Client.Location;
using Cysharp.Threading.Tasks;
using System;
using Unity.Mathematics;
using Placeframe.Core;

namespace Outernet.Client
{
    public class SettingsMenu : MonoBehaviour
    {
        public TextMeshProUGUI framerate;
        public TextMeshProUGUI loadedMaps;
        public TextMeshProUGUI localizationRate;
        public TextMeshProUGUI successRate;
        public TextMeshProUGUI confidenceHistory;
        public TextMeshProUGUI preciseLatitude;
        public TextMeshProUGUI preciseLongitude;
        public TextMeshProUGUI preciseHeading;
        public TextMeshProUGUI ransacScore;
        public TextMeshProUGUI roomName;
        public TextMeshProUGUI hubConnectionStatus;
        public TextMeshProUGUI roomConnectionStatus;
        public TextMeshProUGUI focusDistance;
        public TextMeshProUGUI lightingCondition;
        public TMP_Dropdown lightingConditionDropdown;
        public Toggle localize;
        public Toggle showPointCloud;
        public Toggle showIndicators;
        public Toggle animateNodeIndicators;
        public Toggle animateUserIndicators;
        public Toggle dynamicFocusDistance;
        public Toggle showEyeDebug;
        public TMP_Dropdown visibleLayers;
        public TMP_Dropdown terrainTilesetMode;
        public TMP_Dropdown OSMTilesetMode;
        public TMP_Dropdown nycTilesetMode;
        public TMP_Dropdown googleTilesetMode;
        public TMP_Dropdown localizationReducer;
        public Toggle fallbackToMostRecent;
        public Toggle enableThresholding;
        public Toggle useFloorPlaneDetection;
        public Slider positionThreshold;
        public Slider rotationThreshold;
        public Slider positionInlierThreshold;
        public Slider rotationInlierThreshold;
        public Toggle discardBottomHalf;
        public Slider confidenceFactor;
        public Slider ransacHistorySize;
        public Slider favHistorySize;
        public Slider favStandardDeviationsThreshold;
        public Slider nodeFetchRadius;
        public Slider nodeFetchLimit;

        public TextMeshProUGUI nodeFetchRadiusText;
        public TextMeshProUGUI nodeFetchLimitText;
        public TextMeshProUGUI positionThresholdText;
        public TextMeshProUGUI rotationThresholdText;
        public TextMeshProUGUI positionInlierThresholdText;
        public TextMeshProUGUI rotationInlierThresholdText;
        public TextMeshProUGUI confidenceFactorText;
        public TextMeshProUGUI ransacHistorySizeText;
        public TextMeshProUGUI favHistorySizeText;
        public TextMeshProUGUI favStandardDeviationsThresholdText;

        public List<GameObject> ransacSettings;
        public List<GameObject> favSettings;

        private int frameCount = 0;
        private float elapsedTime = 0.0f;
        private IDisposable subscriptions;

        public void Initialize()
        {
            localizationReducer.AddOptions(new List<string> { "None", "FAV", "RANSAC" });
            terrainTilesetMode.AddOptions(new List<string> { "Disable", "Hide", "Show" });
            OSMTilesetMode.AddOptions(new List<string> { "Disable", "Hide", "Show" });
            nycTilesetMode.AddOptions(new List<string> { "Disable", "Hide", "Show" });
            googleTilesetMode.AddOptions(new List<string> { "Disable", "Hide", "Show" });
            lightingConditionDropdown.AddOptions(new List<string> { "None", "Day", "Dusk", "Night" });

            subscriptions = Disposable.Combine(
                dynamicFocusDistance.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsDynamicFocusDistance.EnqueueSet(value)),

                App.State_Old.settingsDynamicFocusDistance.Subscribe(value =>
                    dynamicFocusDistance.isOn = value.Value),

                showEyeDebug.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsShowEyeDebug.EnqueueSet(value)),

                App.State_Old.settingsShowEyeDebug.Subscribe(value =>
                    showEyeDebug.isOn = value.Value),

                localize.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsLocalize.EnqueueSet(value)),

                // ConnectionManager.RoomConnectionRequested.Subscribe(name => roomName.SetText(name)),
                ConnectionManager.HubConnectionStatusStream.Subscribe(status => hubConnectionStatus.SetText(status.ToString())),
                ConnectionManager.RoomConnectionStatusStream.Subscribe(status => roomConnectionStatus.SetText(status.ToString())),

                lightingConditionDropdown.onValueChanged.AsObservable().Subscribe(value =>
                {
                    value -= 1;
                    Settings.lightingConditionOverride = value == -1 ? null : value;
                }),

                terrainTilesetMode.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsTerrainTilesetMode.EnqueueSet((TilesetMode)Enum.Parse(
                        typeof(TilesetMode), terrainTilesetMode.options[value].text))),

                OSMTilesetMode.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsOSMTilesetMode.EnqueueSet((TilesetMode)Enum.Parse(
                        typeof(TilesetMode), OSMTilesetMode.options[value].text))),

                nycTilesetMode.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsNYCTilesetMode.EnqueueSet((TilesetMode)Enum.Parse(
                        typeof(TilesetMode), nycTilesetMode.options[value].text))),

                googleTilesetMode.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsGoogleTilesetMode.EnqueueSet((TilesetMode)Enum.Parse(
                        typeof(TilesetMode), googleTilesetMode.options[value].text))),

                visibleLayers.BindLayersDropdown(App.state.layers, App.state.settings.visibleLayers),

                App.State_Old.settingsTerrainTilesetMode.Subscribe(settingsTerrainTilesetMode =>
                    terrainTilesetMode.value = terrainTilesetMode.options.FindIndex(option =>
                        option.text == settingsTerrainTilesetMode.Value.ToString())),

                App.State_Old.settingsOSMTilesetMode.Subscribe(settingsOSMTilesetMode =>
                    OSMTilesetMode.value = OSMTilesetMode.options.FindIndex(option =>
                        option.text == settingsOSMTilesetMode.Value.ToString())),

                App.State_Old.settingsNYCTilesetMode.Subscribe(settingsNYCTilesetMode =>
                    nycTilesetMode.value = nycTilesetMode.options.FindIndex(option =>
                        option.text == settingsNYCTilesetMode.Value.ToString())),

                App.State_Old.settingsGoogleTilesetMode.Subscribe(settingsGoogleTilesetMode =>
                    googleTilesetMode.value = googleTilesetMode.options.FindIndex(option =>
                        option.text == settingsGoogleTilesetMode.Value.ToString())),

                nodeFetchRadius.onValueChanged.AsObservable().Subscribe(value =>
                {
                    App.State_Old.settingsNodeFetchRadius.EnqueueSet(SliderToRadius(value));
                    nodeFetchRadiusText.SetText(SliderToRadius(value).ToString());
                }),

                nodeFetchLimit.onValueChanged.AsObservable().Subscribe(value =>
                {
                    App.State_Old.settingsNodeFetchLimit.EnqueueSet(SliderToLimit(value));
                    nodeFetchLimitText.SetText(SliderToLimit(value).ToString());
                }),

                App.State_Old.settingsNodeFetchRadius.Subscribe(settingsNodeFetchRadius =>
                    nodeFetchRadius.value = radiusToSlider(settingsNodeFetchRadius.Value)),

                App.State_Old.settingsNodeFetchLimit.Subscribe(settingsNodeFetchLimit =>
                    nodeFetchLimit.value = limitToSlider(settingsNodeFetchLimit.Value)),

                showPointCloud.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsShowPointCloud.EnqueueSet(value)),

                showIndicators.onValueChanged.AsObservable().Subscribe(value =>
                    App.state.settings.showIndicators.ExecuteSetOrDelay(value)
                ),

                App.state.settings.showIndicators.OnChange(show =>
                    showIndicators.isOn = show
                ),

                animateNodeIndicators.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsAnimateNodeIndicators.EnqueueSet(value)),

                animateUserIndicators.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsAnimateUserIndicators.EnqueueSet(value)),

                enableThresholding.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsEnableLocalizationThreshold.EnqueueSet(value)),

                fallbackToMostRecent.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsFallbackToMostRecent.EnqueueSet(value)),

                useFloorPlaneDetection.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsUseFloorPlaneDetection.EnqueueSet(value)),

                localizationReducer.onValueChanged.AsObservable().Subscribe(value =>
                {
                    LocalizationReducer parsedValue = (LocalizationReducer)Enum.Parse(
                        typeof(LocalizationReducer), localizationReducer.options[value].text);

                    App.State_Old.settingsLocalizationReducer.EnqueueSet(parsedValue);
                }),

                positionThreshold.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsPositionThreshold.EnqueueSet(SliderToPositionThreshold(value))),

                rotationThreshold.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsRotationThreshold.EnqueueSet(SliderToRotationThreshold(value))),

                positionInlierThreshold.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsPositionInlierThreshold.EnqueueSet(SliderToPositionThreshold(value))),

                rotationInlierThreshold.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsRotationInlierThreshold.EnqueueSet(SliderToRotationThreshold(value))),

                discardBottomHalf.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsDiscardBottomHalf.EnqueueSet(value)),

                confidenceFactor.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsConfidenceFactor.EnqueueSet(value)),

                ransacHistorySize.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsRansacHistorySize.EnqueueSet(SliderToHistorySize(value))),

                favHistorySize.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsFavHistorySize.EnqueueSet(SliderToHistorySize(value))),

                favStandardDeviationsThreshold.onValueChanged.AsObservable().Subscribe(value =>
                    App.State_Old.settingsFavThreshold.EnqueueSet(value)),

                App.State_Old.settingsShowPointCloud.Subscribe(settingsShowPointCloud =>
                    showPointCloud.isOn = settingsShowPointCloud.Value),

                App.State_Old.settingsAnimateNodeIndicators.Subscribe(settingsAnimateIndicators =>
                    animateNodeIndicators.isOn = settingsAnimateIndicators.Value),

                App.State_Old.settingsAnimateUserIndicators.Subscribe(settingsAnimateIndicators =>
                    animateUserIndicators.isOn = settingsAnimateIndicators.Value),

                App.State_Old.settingsEnableLocalizationThreshold.Subscribe(
                    settingsEnableLocalizationThreshold =>
                        enableThresholding.isOn = settingsEnableLocalizationThreshold.Value),

                App.State_Old.settingsFallbackToMostRecent.Subscribe(settingsFallbackToMostRecent =>
                    fallbackToMostRecent.isOn = settingsFallbackToMostRecent.Value),

                App.State_Old.settingsUseFloorPlaneDetection.Subscribe(settingsUseFloorPlaneDetection =>
                    useFloorPlaneDetection.isOn = settingsUseFloorPlaneDetection.Value),

                App.State_Old.settingsLocalizationReducer.Subscribe(settingsLocalizationReducer =>
                {
                    localizationReducer.value = localizationReducer.options.FindIndex(option =>
                        option.text == settingsLocalizationReducer.Value.ToString());

                    ransacSettings.ForEach(setting => setting.SetActive(settingsLocalizationReducer.Value == LocalizationReducer.RANSAC));
                    favSettings.ForEach(setting => setting.SetActive(settingsLocalizationReducer.Value == LocalizationReducer.FAV));
                }),

                App.State_Old.settingsPositionThreshold.Subscribe(settingsPositionThreshold =>
                {
                    positionThreshold.value = positionThresholdToSlider(settingsPositionThreshold.Value);
                    positionThresholdText.SetText(settingsPositionThreshold.Value.ToString());
                }),

                App.State_Old.settingsRotationThreshold.Subscribe(settingsRotationThreshold =>
                {
                    rotationThreshold.value = rotationThresholdToSlider(settingsRotationThreshold.Value);
                    rotationThresholdText.SetText(settingsRotationThreshold.Value.ToString());
                }),

                App.State_Old.settingsPositionInlierThreshold.Subscribe(settingsPositionInlierThreshold =>
                {
                    positionInlierThreshold.value = positionThresholdToSlider(settingsPositionInlierThreshold.Value);
                    positionInlierThresholdText.SetText(settingsPositionInlierThreshold.Value.ToString());
                }),

                App.State_Old.settingsRotationInlierThreshold.Subscribe(settingsRotationInlierThreshold =>
                {
                    rotationInlierThreshold.value = rotationThresholdToSlider(settingsRotationInlierThreshold.Value);
                    rotationInlierThresholdText.SetText(settingsRotationInlierThreshold.Value.ToString());
                }),

                App.State_Old.settingsDiscardBottomHalf.Subscribe(settingsDiscardBottomHalf =>
                    discardBottomHalf.isOn = settingsDiscardBottomHalf.Value),

                App.State_Old.settingsConfidenceFactor.Subscribe(settingsConfidenceFactor =>
                {
                    confidenceFactor.value = settingsConfidenceFactor.Value;
                    confidenceFactorText.SetText(settingsConfidenceFactor.Value.ToString());
                }),

                App.State_Old.settingsRansacHistorySize.Subscribe(settingsRansacHistorySize =>
                {
                    ransacHistorySize.value = historySizeToSlider(settingsRansacHistorySize.Value);
                    ransacHistorySizeText.SetText(settingsRansacHistorySize.Value.ToString());
                }),

                App.State_Old.settingsFavHistorySize.Subscribe(settingsFavHistorySize =>
                {
                    favHistorySize.value = historySizeToSlider(settingsFavHistorySize.Value);
                    favHistorySizeText.SetText(settingsFavHistorySize.Value.ToString());
                }),

                App.State_Old.settingsFavThreshold.Subscribe(settingsFavThreshold =>
                {
                    favStandardDeviationsThreshold.value = settingsFavThreshold.Value;
                    favStandardDeviationsThresholdText.SetText(settingsFavThreshold.Value.ToString());
                })
            );

            // showPointCloud.transform.parent.parent.gameObject.SetActive(false);
            // animateIndicators.transform.parent.parent.gameObject.SetActive(false);
            // confidenceHistory.transform.parent.gameObject.SetActive(false);
            preciseLatitude.transform.parent.gameObject.SetActive(false);
            preciseLongitude.transform.parent.gameObject.SetActive(false);
            preciseHeading.transform.parent.gameObject.SetActive(false);
            showEyeDebug.transform.parent.parent.gameObject.SetActive(false);
            dynamicFocusDistance.transform.parent.parent.gameObject.SetActive(false);
            // OSMTilesetMode.transform.parent.parent.gameObject.SetActive(false);
            nycTilesetMode.transform.parent.parent.gameObject.SetActive(false);
            // loadedMaps.transform.parent.gameObject.SetActive(false);
            roomConnectionStatus.transform.parent.gameObject.SetActive(false);
            hubConnectionStatus.transform.parent.gameObject.SetActive(false);
            // roomName.transform.parent.gameObject.SetActive(false);
            // nodeFetchRadius.transform.parent.parent.parent.gameObject.SetActive(false);

            localizationRate.transform.parent.gameObject.SetActive(false);
            terrainTilesetMode.transform.parent.parent.gameObject.SetActive(false);
            googleTilesetMode.transform.parent.parent.gameObject.SetActive(false);
            useFloorPlaneDetection.transform.parent.parent.gameObject.SetActive(false);
            successRate.transform.parent.gameObject.SetActive(false);
            ransacScore.transform.parent.gameObject.SetActive(false);
            localizationReducer.transform.parent.parent.gameObject.SetActive(false);
            fallbackToMostRecent.transform.parent.parent.gameObject.SetActive(false);
            enableThresholding.transform.parent.parent.gameObject.SetActive(false);
            positionThreshold.transform.parent.parent.parent.gameObject.SetActive(false);
            rotationThreshold.transform.parent.parent.parent.gameObject.SetActive(false);
            positionInlierThreshold.transform.parent.parent.parent.gameObject.SetActive(false);
            rotationInlierThreshold.transform.parent.parent.parent.gameObject.SetActive(false);
            discardBottomHalf.transform.parent.parent.gameObject.SetActive(false);
            confidenceFactor.transform.parent.parent.parent.gameObject.SetActive(false);
            ransacHistorySize.transform.parent.parent.parent.gameObject.SetActive(false);
            favHistorySize.transform.parent.parent.parent.gameObject.SetActive(false);
            favStandardDeviationsThreshold.transform.parent.parent.parent.gameObject.SetActive(false);
        }

        private float SliderToRadius(float value)
        {
            var result = 5 * Mathf.Pow(2, value);
            return result;
        }

        private int SliderToLimit(float value)
        {
            var result = (int)Mathf.Pow(2, value);
            return result;
        }

        private float radiusToSlider(float value)
        {
            var result = Mathf.Round(Mathf.Log(value / 5, 2));
            return result;
        }

        private float limitToSlider(float value)
        {
            var result = Mathf.Round(Mathf.Log(value, 2));
            return result;
        }

        private float SliderToPositionThreshold(float value)
        {
            var result = 0.01f * Mathf.Pow(2, value);
            return result;
        }

        private float positionThresholdToSlider(float value)
        {
            var result = Mathf.Round(Mathf.Log(value / 0.01f, 2));
            return result;
        }

        private float SliderToRotationThreshold(float value)
        {
            var result = 0.5f * Mathf.Pow(2, value);
            return result;
        }

        private float rotationThresholdToSlider(float value)
        {
            var result = Mathf.Round(Mathf.Log(value / 0.5f, 2));
            return result;
        }

        private int SliderToHistorySize(float value)
        {
            var result = (int)Mathf.Pow(2, value);
            return result;
        }

        private float historySizeToSlider(int value)
        {
            var result = Mathf.Round(Mathf.Log(value, 2));
            return result;
        }

        public void Terminate()
        {
            subscriptions.Dispose();
        }

        public void RealUpdate()
        {
            frameCount++;
            elapsedTime += Time.unscaledDeltaTime;

            if (elapsedTime >= 1.0f)
            {
                framerate.SetText(string.Format("{0:0.00}", frameCount / elapsedTime));

                frameCount = 0;
                elapsedTime = 0.0f;
            }

            // TODO EP: Poll Maps And Display Names
            // loadedMaps.SetText(string.Join("\n", MapManager.Maps.Select(map => $"{map.Name} [{MapManager.maps[map.Id].status}]")));

            // localizationRate.SetText(string.Format("{0:0.00}", Localizer.Status.localizationCount));
            // successRate.SetText(string.Format("{0:0.00}", Localizer.Status.successCount));

            // TODO EP: Remove confidence history
            //confidenceHistory.SetText(string.Format("{0:0.00}", string.Join(", ", Localizer.Status.confidenceHistory.Reverse<float>().Take(8).Reverse())));

            // ransacScore.SetText(string.Format("{0:0.00}", RANSAC.Score));

            var cameraEcefTransform = VisualPositioningSystem.UnityWorldToEcef(Camera.main.transform.position, Camera.main.transform.rotation);
            var longitudeLatitudeHeight = CesiumWgs84Ellipsoid.EarthCenteredEarthFixedToLongitudeLatitudeHeight(cameraEcefTransform.position);
            preciseLatitude.SetText(string.Format("{0:0.000000}", longitudeLatitudeHeight.y));
            preciseLongitude.SetText(string.Format("{0:0.000000}", longitudeLatitudeHeight.x));

            // Adapted from eastNorthUpToFixedFrame in this file https://github.com/CesiumGS/cesium-native/blob/main/CesiumGeospatial/src/GlobeTransforms.cpp
            var up = CesiumWgs84Ellipsoid.GeodeticSurfaceNormal(cameraEcefTransform.position);
            var east = math.normalize(new double3(-cameraEcefTransform.position.y, cameraEcefTransform.position.x, 0));
            var north = math.cross(up, east);

            // Negatives here are to account for handedness difference
            var eunRotation = Quaternion.LookRotation(-north.ToFloats(), -up.ToFloats());
            var ecefRotation = new Quaternion((float)cameraEcefTransform.rotation.value.x, (float)cameraEcefTransform.rotation.value.y, (float)cameraEcefTransform.rotation.value.z, (float)cameraEcefTransform.rotation.value.w);
            var relativeRotation = Quaternion.Inverse(eunRotation) * ecefRotation;
            var heading = relativeRotation.eulerAngles.y; // degrees

            if (heading > 180)
            {
                heading -= 360;
            }

            preciseHeading.SetText(string.Format("{0:0.00}", heading));

            focusDistance.SetText(string.Format("{0:0.00}", Camera.main.stereoConvergence));
            lightingCondition.SetText(Settings.lightingCondition.ToString());
        }
    }
}