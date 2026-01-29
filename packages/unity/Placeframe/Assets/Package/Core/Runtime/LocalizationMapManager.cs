using System;
using System.Collections.Generic;
using UnityEngine;

namespace Plerion.Core
{
    public class LocalizationMapManager : MonoBehaviour
    {
        public LocalizationMap localizationMapPrefab;
        private Dictionary<Guid, LocalizationMap> _visualizers = new Dictionary<Guid, LocalizationMap>();

        private void Awake()
        {
            VisualPositioningSystem.SetLocalizationMapManager(this);
        }

        public void AddMap(Guid mapID, bool visible)
        {
            if (_visualizers.ContainsKey(mapID))
                throw new InvalidOperationException($"Map {mapID} is already added");

            _visualizers[mapID] = Instantiate(localizationMapPrefab, Vector3.zero, Quaternion.identity);
            _visualizers[mapID].SetVisible(visible);
            _visualizers[mapID].Initialize(mapID);
        }

        public void RemoveMap(Guid mapID)
        {
            if (!_visualizers.ContainsKey(mapID))
                throw new InvalidOperationException($"Map {mapID} is not added");

            Destroy(_visualizers[mapID].gameObject);
            _visualizers.Remove(mapID);
        }

        public void SetVisible(bool visible)
        {
            foreach (var visualizer in _visualizers.Values)
            {
                visualizer.SetVisible(visible);
            }
        }
    }
}
