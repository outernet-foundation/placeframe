using Cysharp.Threading.Tasks;
using Placeframe.Core;
using UnityEngine;

namespace Outernet.Client
{
    public class LocalizationManager : MonoBehaviour
    {
        private void Awake()
        {
            // This will ultimately be predicated on App.state.roughGrainedLocation
            LoadMaps().Forget();
        }

        private async UniTask LoadMaps()
        {
            var maps = await App.API.GetLocalizationMapsAsync();

            foreach (var map in maps)
                VisualPositioningSystem.AddLocalizationMap(map.Id);
        }
    }
}
