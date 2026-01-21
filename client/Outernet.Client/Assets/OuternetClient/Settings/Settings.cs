using Outernet.Shared;
using R3;
using UnityEngine;
using Plerion.Core;

namespace Outernet.Client
{
    public static class Settings
    {
        public static bool menuOpen = false;
        public static Vector2 menuPanelDimensions = new Vector2(0, 0);
        public static bool showPointCloud = true;
        public static bool animateNodeIndicators = false;
        public static bool animateUserIndicators = true;
        public static bool localize = true;
        // public static ReactiveProperty<int> numThreads = new ReactiveProperty<int>(1);
        // public static int solverType = 0;
        // public static ReactiveProperty<int> compression = new ReactiveProperty<int>(0);
        // public static LocalizationReducer localizationReducer = LocalizationReducer.RANSAC;
        public static bool fallbackToMostRecent = false;
        public static bool thresholding = false;
        public static int? lightingConditionOverride = null;
        public static int? lightingCondition = null;
        public static float positionThreshold = 0.05f;
        public static float rotationThreshold = 2f;
        public static float positionInlierThreshold = 0.05f;
        public static float rotationInlierThreshold = 0.05f;
        public static bool discardBottomHalf = false;
        public static float confidenceFactor = 1.0f;
        public static int ransacHistorySize = 128;
        public static int favHistorySize = 16;
        public static float favStandardDeviationsThreshold = 2f;
        public static bool useFloorPlaneDetection = true;
    }
}