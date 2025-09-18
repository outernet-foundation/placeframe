using System;
using System.Linq;

using Unity.Mathematics;
using UnityEngine;

using Outernet.Client.Location;

using FofX.Stateful;

using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using PlerionClient.Model;

namespace Outernet.Client.AuthoringTools
{
    public static class Utility
    {
        public static void DisplayDialog(Component dialog)
            => DisplayDialog(dialog.gameObject);

        public static void DisplayDialog(GameObject dialog)
        {
            var scrim = UnityEngine.Object.Instantiate(AuthoringToolsPrefabs.Scrim);
            scrim.transform.SetAsLastSibling();
            dialog.transform.SetParent(scrim.transform, false);
            dialog.GetMonoBehaviourEventHelper().onDestroyed.AddListener(_ => UnityEngine.Object.Destroy(scrim.gameObject));
        }

        public static MonoBehaviourEventHelper GetMonoBehaviourEventHelper(this Component component)
            => component.gameObject.GetMonoBehaviourEventHelper();

        public static MonoBehaviourEventHelper GetMonoBehaviourEventHelper(this GameObject gameObject)
            => gameObject.GetOrAddComponent<MonoBehaviourEventHelper>();

        public static T GetOrAddComponent<T>(this GameObject gameObject) where T : Component
            => gameObject.TryGetComponent<T>(out var result) ? result : gameObject.AddComponent<T>();

        public static Component GetOrAddComponent(this GameObject gameObject, Type type)
            => gameObject.TryGetComponent(type, out var result) ? result : gameObject.AddComponent(type);

        public static void CalcSelectedGroupTransform(out Vector3 position, out Quaternion rotation)
        {
            Vector3 pos = default;
            Quaternion rot = default;
            int count = 0;

            foreach (var node in App.state.authoringTools.SelectedNodes())
            {
                pos += node.position.value;
                rot = node.rotation.value;
                count++;
            }

            pos /= count;

            position = pos;
            rotation = count == 1 ? rot : Quaternion.identity;
        }

        public static void SetFrom<T>(this ObservableList<ObservablePrimitive<T>> list, T[] array)
        {
            while (list.count > array.Length)
                list.RemoveAt(list.count - 1);

            while (list.count < array.Length)
                list.Add();

            for (int i = 0; i < array.Length; i++)
                list[i].value = array[i];
        }

        public static void SetFrom<TKey, TValue, TSource>(this ObservableDictionary<TKey, TValue> dictionary, TSource[] values, Func<TSource, TKey> keySelector, Action<TSource, TValue> copyTo)
            where TValue : IObservableNode, new()
        {
            var toRemove = dictionary.keys.Except(values.Select(keySelector)).ToArray();

            foreach (var removed in toRemove)
                dictionary.Remove(removed);

            var toAdd = values.Select(keySelector).Except(dictionary.keys).ToArray();

            foreach (var added in toAdd)
                dictionary.Add(added);

            foreach (var value in values)
                copyTo(value, dictionary[keySelector(value)]);
        }

        public static bool HasAttribute<T>(this IObservableNode node) where T : Attribute
            => node.TryGetAttribute(out T _);

        public static bool TryGetAttribute<T>(this IObservableNode node, out T attribute) where T : Attribute
        {
            foreach (var att in node.attributes)
            {
                if (att is T casted)
                {
                    attribute = casted;
                    return true;
                }
            }

            attribute = null;
            return false;
        }

        public static void AddListener(this UnityEngine.EventSystems.EventTrigger eventTrigger, EventTriggerType id, UnityAction<BaseEventData> callback)
        {
            var entry = new UnityEngine.EventSystems.EventTrigger.Entry();
            entry.eventID = id;
            entry.callback.AddListener(callback);
            eventTrigger.triggers.Add(entry);
        }

        public static bool KeyboardIsFocused()
        {
            return EventSystem.current.currentSelectedGameObject != null &&
                EventSystem.current.currentSelectedGameObject.TryGetComponent(out TMPro.TMP_InputField inputField) &&
                inputField.isFocused;
        }

        public static Key GetPlatformCommandKey()
        {
            switch (Application.platform)
            {
                case RuntimePlatform.OSXEditor:
                    return Key.LeftCtrl;
                case RuntimePlatform.WindowsEditor:
                    return Key.CapsLock;
                case RuntimePlatform.OSXPlayer:
                    return Key.LeftCommand;
                default:
                    return Key.LeftCtrl;
            }
        }

        public static Color WithAlpha(this Color color, float alpha)
            => new Color(color.r, color.g, color.b, alpha);

        public static T GetPreviousValue<T>(this ObservablePrimitive<T> primitive, List<NodeChangeData> changes)
        {
            if (changes == null || changes.Count == 0)
                return primitive.value;

            foreach (var change in changes)
            {
                if (change.source == primitive && change.changeType == ChangeType.Set)
                    return (T)change.previousValue;
            }

            return primitive.value;
        }

        public static LocalizationMapModel ToMapRecord(Guid nodeID)
        {
            var map = App.state.authoringTools.maps[nodeID];
            var ecef = Client.Utility.LocalToEcef(
                App.state.localToEcefMatrix.value,
                map.position.value,
                map.rotation.value
            );

            return new LocalizationMapModel(
                id: map.id,
                name: map.name.value,
                lighting: (int)map.lighting.value,
                color: (int)map.color.value,
                active: true,
                positionX: ecef.position.x,
                positionY: ecef.position.y,
                positionZ: ecef.position.z,
                rotationX: ecef.rotation.value.x,
                rotationY: ecef.rotation.value.y,
                rotationZ: ecef.rotation.value.z,
                rotationW: ecef.rotation.value.w,
                points: map.localInputImagePositions.SelectMany(EnumerateComponents).ToList()
            );
        }

        public static IEnumerable<double> EnumerateComponents(double3 value)
        {
            yield return value.x;
            yield return value.y;
            yield return value.z;
        }

        public static NodeModel ToExhibitModel(Guid nodeID)
        {
            var node = App.state.nodes[nodeID];
            var exhibit = App.state.exhibits[nodeID];
            var ecef = Client.Utility.LocalToEcef(
                App.state.localToEcefMatrix.value,
                node.position.value,
                node.rotation.value
            );

            return new NodeModel(
                id: node.id,
                name: node.name.value,
                active: true,
                positionX: ecef.position.x,
                positionY: ecef.position.y,
                positionZ: ecef.position.z,
                rotationX: ecef.rotation.value.x,
                rotationY: ecef.rotation.value.y,
                rotationZ: ecef.rotation.value.z,
                rotationW: ecef.rotation.value.w,
                link: exhibit.link.value,
                linkType: (int)exhibit.linkType.value,
                label: exhibit.label.value,
                labelType: (int)exhibit.labelType.value,
                labelScale: exhibit.labelScale.value,
                labelWidth: exhibit.labelWidth.value,
                labelHeight: exhibit.labelHeight.value,
                layer: node.layer.value,
                parent: node.parentID.value
            );
        }

        public static LayerModel ToLayerModel(Guid sceneObjectID)
        {
            var layer = App.state.layers[sceneObjectID];
            return new LayerModel(layer.id, layer.layerName.value);
        }
    }
}