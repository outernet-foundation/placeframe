using Placeframe.Core;
using UnityEngine;

namespace Plerion.MakeItSing
{
    [CreateAssetMenu(fileName = "Prefabs", menuName = "Scriptable Objects/Prefabs")]
    public class Prefabs : ScriptableObject
    {
        private static Prefabs _instance;

        public static LocalizationMapManager LocalizationMapManager => _instance.localizationMapManager;

        public LocalizationMapManager localizationMapManager;

        public void Initialize()
        {
            _instance = this;
        }
    }
}