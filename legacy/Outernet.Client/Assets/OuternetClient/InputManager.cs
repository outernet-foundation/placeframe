using System;
using System.Collections.Generic;
using UnityEngine;

namespace Outernet.Client
{
    public interface IPointer
    {
        string ID { get; }
        bool isValid { get; }
        bool pressed { get; }
        GameObject target { get; }

        void Update();
    }

    public class InputManager : MonoBehaviour
    {
        private class PointerData
        {
            public IPointer pointer;
            public bool wasValid;
            public bool wasPressed;
            public GameObject hoverTarget;
            public GameObject pressTarget;
            public GameObject clickTarget;
        }

        private static Dictionary<IPointer, PointerData> _pointers = new Dictionary<IPointer, PointerData>();

        private void Update()
        {
            foreach (var pointerData in _pointers.Values)
                UpdatePointerData(pointerData);
        }

        private void UpdatePointerData(PointerData pointerData)
        {
            pointerData.pointer.Update();

            if (pointerData.pointer.isValid != pointerData.wasValid)
            {
                pointerData.wasValid = pointerData.pointer.isValid;

                if (!pointerData.pointer.isValid)
                {
                    ExecuteHierarchy<IHoverExitHandler>(pointerData.hoverTarget, x => x.OnHoverExit(pointerData.pointer));
                    ExecuteHierarchy<IPressReleaseHandler>(pointerData.pressTarget, x => x.OnPressRelease(pointerData.pointer));

                    pointerData.wasValid = false;
                    pointerData.wasPressed = false;
                    pointerData.hoverTarget = null;
                    pointerData.pressTarget = null;
                    pointerData.clickTarget = null;

                    return;
                }

                pointerData.wasPressed = pointerData.pointer.pressed;
            }

            var currentHoverTarget = FindHandler<IHoverEnterHandler>(pointerData.pointer.target);

            if (pointerData.hoverTarget != currentHoverTarget)
            {
                //send hover changed events
                ExecuteHierarchy<IHoverExitHandler>(pointerData.hoverTarget, x => x.OnHoverExit(pointerData.pointer));
                ExecuteHierarchy<IHoverEnterHandler>(pointerData.pointer.target, x => x.OnHoverEnter(pointerData.pointer));
                pointerData.hoverTarget = currentHoverTarget;
            }

            if (pointerData.wasPressed != pointerData.pointer.pressed)
            {
                pointerData.wasPressed = pointerData.pointer.pressed;

                if (pointerData.pointer.pressed)
                {
                    var pressTarget = ExecuteHierarchy<IPressStartHandler>(pointerData.pointer.target, x => x.OnPressStart(pointerData.pointer));
                    var clickTarget = FindHandler<IClickHandler>(pointerData.pointer.target);

                    // didnt find a press handler... search for a click handler
                    if (pressTarget == null)
                        pressTarget = clickTarget;

                    pointerData.pressTarget = pressTarget;
                    pointerData.clickTarget = clickTarget;
                }
                else if (pointerData.pressTarget != null)
                {
                    //send press release event
                    ExecuteHierarchy<IPressReleaseHandler>(pointerData.pressTarget, x => x.OnPressRelease(pointerData.pointer));

                    //send click event (if valid)
                    if (pointerData.clickTarget == FindHandler<IClickHandler>(pointerData.pointer.target))
                        Execute<IClickHandler>(pointerData.clickTarget, x => x.OnClick(pointerData.pointer));

                    pointerData.pressTarget = null;
                }
            }
        }

        private static GameObject FindHandler<T>(GameObject target)
        {
            if (target == null)
                return null;

            var currUpstream = target.transform;
            while (currUpstream != null)
            {
                if (currUpstream.GetComponent<T>() != null)
                    return currUpstream.gameObject;

                currUpstream = currUpstream.transform.parent;
            }

            return null;
        }

        private static GameObject ExecuteHierarchy<T>(GameObject target, Action<T> execute)
        {
            if (target == null)
                return null;

            var currUpstream = target.transform;
            while (currUpstream != null)
            {
                if (Execute(currUpstream.gameObject, execute))
                    return currUpstream.gameObject;

                currUpstream = currUpstream.transform.parent;
            }

            return null;
        }

        private static bool Execute<T>(GameObject target, Action<T> execute)
        {
            var targetComponents = target.GetComponents<T>();

            foreach (var component in targetComponents)
                execute(component);

            return targetComponents.Length > 0;
        }

        public static void RegisterPointer(IPointer pointer)
        {
            if (_pointers.ContainsKey(pointer))
                throw new Exception("Pointers can only be registered once");

            _pointers.Add(pointer, new PointerData() { pointer = pointer });
        }

        public static void DeregisterPointer(IPointer pointer)
        {
            if (!_pointers.TryGetValue(pointer, out var pointerData))
                return;

            _pointers.Remove(pointer);

            ExecuteHierarchy<IHoverExitHandler>(pointerData.hoverTarget, x => x.OnHoverExit(pointerData.pointer));
            ExecuteHierarchy<IPressReleaseHandler>(pointerData.pressTarget, x => x.OnPressRelease(pointerData.pointer));
        }
    }

    public interface IHoverEnterHandler
    {
        void OnHoverEnter(IPointer pointer);
    }

    public interface IHoverExitHandler
    {
        void OnHoverExit(IPointer pointer);
    }

    public interface IPressStartHandler
    {
        void OnPressStart(IPointer pointer);
    }

    public interface IPressReleaseHandler
    {
        void OnPressRelease(IPointer pointer);
    }

    public interface IClickHandler
    {
        void OnClick(IPointer pointer);
    }
}