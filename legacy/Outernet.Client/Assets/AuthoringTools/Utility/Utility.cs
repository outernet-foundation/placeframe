using System;
using System.Collections.Generic;
using System.Linq;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Outernet.Client.Location;
using Outernet.Shared;
using Placeframe.Core;
using PlaceframeApiClient.Model;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using Color = UnityEngine.Color;
using Quaternion = UnityEngine.Quaternion;
using Vector3 = UnityEngine.Vector3;

namespace Outernet.Client.AuthoringTools
{
    public static class Utility
    {
        public static void DisplayDialog(Component dialog) => DisplayDialog(dialog.gameObject);

        public static void DisplayDialog(GameObject dialog)
        {
            var scrim = UnityEngine.Object.Instantiate(AuthoringToolsPrefabs.Scrim);
            scrim.transform.SetAsLastSibling();
            dialog.transform.SetParent(scrim.transform, false);
            dialog
                .GetMonoBehaviourEventHelper()
                .onDestroyed.AddListener(_ => UnityEngine.Object.Destroy(scrim.gameObject));
        }

        public static MonoBehaviourEventHelper GetMonoBehaviourEventHelper(this Component component) =>
            component.gameObject.GetMonoBehaviourEventHelper();

        public static MonoBehaviourEventHelper GetMonoBehaviourEventHelper(this GameObject gameObject) =>
            gameObject.GetOrAddComponent<MonoBehaviourEventHelper>();

        public static T GetOrAddComponent<T>(this GameObject gameObject)
            where T : Component =>
            gameObject.TryGetComponent<T>(out var result) ? result : gameObject.AddComponent<T>();

        public static Component GetOrAddComponent(this GameObject gameObject, Type type) =>
            gameObject.TryGetComponent(type, out var result) ? result : gameObject.AddComponent(type);

        public static void CalcSelectedGroupTransform(out Vector3 position, out Quaternion rotation)
        {
            double3 pos = default;
            Quaternion rot = default;
            int count = 0;

            foreach (var transform in App.state.authoringTools.SelectedTransforms())
            {
                pos += transform.position.value;
                rot = transform.rotation.value;
                count++;
            }

            pos /= count;

            var localTransform = VisualPositioningSystem.EcefToUnityWorld(pos, rot);

            position = localTransform.position;
            rotation = count == 1 ? localTransform.rotation : Quaternion.identity;
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

        public static void SetFrom<TKey, TValue, TSource>(
            this ObservableDictionary<TKey, TValue> dictionary,
            TSource[] values,
            Func<TSource, TKey> keySelector,
            Action<TSource, TValue> copyTo
        )
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

        public static bool HasAttribute<T>(this IObservableNode node)
            where T : Attribute => node.TryGetAttribute(out T _);

        public static bool TryGetAttribute<T>(this IObservableNode node, out T attribute)
            where T : Attribute
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

        public static void AddListener(
            this UnityEngine.EventSystems.EventTrigger eventTrigger,
            EventTriggerType id,
            UnityAction<BaseEventData> callback
        )
        {
            var entry = new UnityEngine.EventSystems.EventTrigger.Entry();
            entry.eventID = id;
            entry.callback.AddListener(callback);
            eventTrigger.triggers.Add(entry);
        }

        public static bool KeyboardIsFocused()
        {
            return EventSystem.current.currentSelectedGameObject != null
                && EventSystem.current.currentSelectedGameObject.TryGetComponent(out TMPro.TMP_InputField inputField)
                && inputField.isFocused;
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

        public static Color WithAlpha(this Color color, float alpha) => new Color(color.r, color.g, color.b, alpha);

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

        public static GroupBatchCreate ToGroupBatchCreate(Guid sceneObjectID)
        {
            var group = App.state.authoringTools.nodeGroups[sceneObjectID];

            return new GroupBatchCreate(group.id, group.name.value) { ParentId = group.parentID.value };
        }

        public static GroupBatchUpdate ToGroupUpdate(Guid sceneObjectID)
        {
            var group = App.state.authoringTools.nodeGroups[sceneObjectID];

            return new GroupBatchUpdate(id: group.id) { Name = group.name.value, ParentId = group.parentID.value };
        }

        public static LocalizationMapCreate ToMapCreate(Guid sceneObjectID)
        {
            var map = App.state.authoringTools.maps[sceneObjectID];
            var transform = App.state.transforms[sceneObjectID];

            return new LocalizationMapCreate(
                reconstructionId: map.reconstructionID.value,
                positionX: transform.position.value.x,
                positionY: transform.position.value.y,
                positionZ: transform.position.value.z,
                rotationX: transform.rotation.value.x,
                rotationY: transform.rotation.value.y,
                rotationZ: transform.rotation.value.z,
                rotationW: transform.rotation.value.w,
                color: 0 //TODO EP: What should this value be? Do we even want to use it if we're going to use the colors from the point cloud?
            )
            {
                Lighting = map.lighting.value,
                Name = map.name.value,
                Active = true,
            };
        }

        public static LocalizationMapBatchUpdate ToMapUpdate(Guid sceneObjectID)
        {
            var map = App.state.authoringTools.maps[sceneObjectID];
            var transform = App.state.transforms[sceneObjectID];

            return new LocalizationMapBatchUpdate(id: map.uuid)
            {
                Name = map.name.value,
                Lighting = map.lighting.value,
                Active = true,
                PositionX = transform.position.value.x,
                PositionY = transform.position.value.y,
                PositionZ = transform.position.value.z,
                RotationX = transform.rotation.value.x,
                RotationY = transform.rotation.value.y,
                RotationZ = transform.rotation.value.z,
                RotationW = transform.rotation.value.w,
            };
        }

        public static NodeBatchCreate ToNodeBatchCreate(Guid sceneObjectID)
        {
            var node = App.state.nodes[sceneObjectID];
            var transform = App.state.transforms[sceneObjectID];

            return new NodeBatchCreate(
                id: node.id,
                name: node.name.value,
                positionX: transform.position.value.x,
                positionY: transform.position.value.y,
                positionZ: transform.position.value.z,
                rotationX: transform.rotation.value.x,
                rotationY: transform.rotation.value.y,
                rotationZ: transform.rotation.value.z,
                rotationW: transform.rotation.value.w,
                labelWidth: node.labelWidth.value,
                labelHeight: node.labelHeight.value,
                labelScale: node.labelScale.value,
                labelType: Conversions.LabelType(node.labelType.value),
                label: node.label.value,
                linkType: Conversions.LinkType(node.linkType.value),
                link: node.link.value
            )
            {
                Active = true,
                LayerId = node.layer.value,
                ParentId = node.parentID.value,
            };
        }

        public static NodeBatchUpdate ToNodeUpdate(Guid sceneObjectID)
        {
            var node = App.state.nodes[sceneObjectID];
            var transform = App.state.transforms[sceneObjectID];

            return new NodeBatchUpdate(id: node.id)
            {
                Name = node.name.value,
                Active = true,
                PositionX = transform.position.value.x,
                PositionY = transform.position.value.y,
                PositionZ = transform.position.value.z,
                RotationX = transform.rotation.value.x,
                RotationY = transform.rotation.value.y,
                RotationZ = transform.rotation.value.z,
                RotationW = transform.rotation.value.w,
                Link = node.link.value,
                LinkType = Conversions.LinkType(node.linkType.value),
                Label = node.label.value,
                LabelType = Conversions.LabelType(node.labelType.value),
                LabelScale = node.labelScale.value,
                LabelWidth = node.labelWidth.value,
                LabelHeight = node.labelHeight.value,
                LayerId = node.layer.value,
                ParentId = node.parentID.value,
            };
        }

        public static LayerCreate ToLayerCreate(Guid sceneObjectID)
        {
            var layer = App.state.layers[sceneObjectID];
            return new LayerCreate(layer.layerName.value) { Id = layer.id };
        }

        public static LayerBatchUpdate ToLayerUpdate(Guid sceneObjectID)
        {
            var layer = App.state.layers[sceneObjectID];
            return new LayerBatchUpdate(layer.id) { Name = layer.layerName.value };
        }
    }
}
