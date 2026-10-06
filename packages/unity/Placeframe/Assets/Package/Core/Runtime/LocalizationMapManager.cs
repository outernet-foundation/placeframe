using System;
using System.Collections.Generic;
using UnityEngine;

namespace Placeframe.Core
{
    public class LocalizationMapVisualizerManager : MonoBehaviour
    {
        public LocalizationMapVisualizer localizationMapPrefab;
        private bool _visible = true;
        private Dictionary<Guid, LocalizationMapVisualizer> _visualizers = new Dictionary<Guid, LocalizationMapVisualizer>();

        private void Awake()
        {
            VisualPositioningSystem.OnLocalizationMapAdded += AddMap;
            VisualPositioningSystem.OnLocalizationMapRemoved += RemoveMap;

            foreach (var map in VisualPositioningSystem.LocalizationMaps)
                AddMap(map);
        }

        private void OnDestroy()
        {
            VisualPositioningSystem.OnLocalizationMapAdded -= AddMap;
            VisualPositioningSystem.OnLocalizationMapRemoved -= RemoveMap;
        }

        public void AddMap(Guid mapID)
        {
            if (_visualizers.ContainsKey(mapID))
                throw new InvalidOperationException($"Map {mapID} is already added");

            _visualizers[mapID] = Instantiate(localizationMapPrefab, Vector3.zero, Quaternion.identity);
            _visualizers[mapID].SetVisible(_visible);
            _visualizers[mapID].Load(mapID);
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
            _visible = visible;

            foreach (var visualizer in _visualizers.Values)
                visualizer.SetVisible(visible);
        }
    }
}
