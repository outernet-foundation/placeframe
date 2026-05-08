using UnityEngine;
using Nessle;
using ObserveThing;
using System.Collections.Generic;
using UnityEngine.UI;
using FofX;
using Cysharp.Threading.Tasks;
using System.Threading;
using System;

namespace Plerion.MakeItSing
{
    public struct AnimatedListProps
    {
        public ElementProps element;
        public LayoutProps layout;
        public IValueObservable<RectOffset> padding;
        public IValueObservable<float> spacing;
        public IValueObservable<TextAnchor> childAlignment;
        public IValueObservable<bool> reverseArrangement;
        public IValueObservable<bool> childForceExpandHeight;
        public IValueObservable<bool> childForceExpandWidth;
        public IValueObservable<bool> childControlWidth;
        public IValueObservable<bool> childControlHeight;
        public IValueObservable<bool> childScaleWidth;
        public IValueObservable<bool> childScaleHeight;
        public IListObservable<IControl> children;
    }

    public class AnimatedListControl : Control<AnimatedListProps>
    {
        public RectTransform animateOutParent;
        public LayoutGroupControl layout;
        private Dictionary<uint, TransitionHelper> _transitions = new Dictionary<uint, TransitionHelper>();

        private class TransitionHelper
        {
            public AnimatedListElementContainer element { get; }
            private Vector3 _positionCache;

            private Vector3 _targetLocalPosition;
            private float _targetAlpha;
            private float _duration;
            private Action<bool> _onComplete;
            private TaskHandle _transition = TaskHandle.Complete;

            public TransitionHelper(AnimatedListElementContainer element)
            {
                this.element = element;
            }

            private void PlayTransition(Vector3 targetLocalPosition, float targetAlpha, float duration, Action<bool> onComplete = default)
            {
                if (!_transition.complete && _onComplete != null)
                    _onComplete(false);

                _targetLocalPosition = targetLocalPosition;
                _targetAlpha = targetAlpha;
                _duration = duration;
                _onComplete = onComplete;

                if (_transition.complete)
                    _transition = TaskHandle.Execute(AnimateTransition);
            }

            private async UniTask AnimateTransition(CancellationToken token = default)
            {
                Vector3 positionVelocity = default;
                float alphaVelocity = default;

                while (!token.IsCancellationRequested)
                {
                    element.body.rectTransform.localPosition = Vector3.SmoothDamp(element.body.rectTransform.localPosition, _targetLocalPosition, ref positionVelocity, _duration);
                    element.alpha = Mathf.SmoothDamp(element.alpha, _targetAlpha, ref alphaVelocity, _duration);

                    //finish here
                    if (element.alpha - _targetAlpha < 0.001f && (element.body.rectTransform.localPosition - _targetLocalPosition).sqrMagnitude < 0.001f * 0.001f)
                        break;

                    await UniTask.Yield(PlayerLoopTiming.LastPostLateUpdate);
                }

                element.body.rectTransform.localPosition = _targetLocalPosition;
                element.alpha = _targetAlpha;

                _onComplete?.Invoke(true);
            }

            public void CacheWorldPosition()
            {
                _positionCache = element.body.rectTransform.position;
            }

            public void RestoreWorldPosition()
            {
                element.body.rectTransform.position = _positionCache;
            }

            public void PlayAnimateInTransition(Action<bool> onComplete = default)
            {
                element.body.rectTransform.localPosition = new Vector3(0, -28f, 0);
                element.alpha = 0;
                PlayTransition(Vector3.zero, 1, 0.25f, onComplete);
            }

            public void PlayAnimateOutTransition(Action<bool> onComplete = default)
            {
                PlayTransition(
                    element.body.rectTransform.localPosition,
                    0,
                    0.125f,
                    onComplete
                );
            }

            public void PlayMoveTransition(Action<bool> onComplete = default)
            {
                PlayTransition(Vector3.zero, 1, 0.25f, onComplete);
            }
        }

        protected override void SetupInternal()
        {
            layout.Setup(new()
            {
                padding = props.padding,
                spacing = props.spacing,
                childAlignment = props.childAlignment,
                reverseArrangement = props.reverseArrangement,
                childForceExpandHeight = props.childForceExpandHeight,
                childForceExpandWidth = props.childForceExpandWidth,
                childControlWidth = props.childControlWidth,
                childControlHeight = props.childControlHeight,
                childScaleWidth = props.childScaleWidth,
                childScaleHeight = props.childScaleHeight
            });

            AddBinding(
                layout,
                props.element.Subscribe(this),
                props.layout.Subscribe(this),
                props.children?.SubscribeWithId(
                    onAdd: (id, index, value) =>
                    {
                        var element = GenerateElementContainer(value);

                        foreach (var transition in _transitions.Values)
                            transition.CacheWorldPosition();

                        element.transform.SetParent(rectTransform, false);
                        element.transform.SetSiblingIndex(index);

                        LayoutRebuilder.ForceRebuildLayoutImmediate(rectTransform);

                        foreach (var transition in _transitions.Values)
                        {
                            transition.RestoreWorldPosition();
                            Debug.DrawRay(transition.element.body.rectTransform.position, transition.element.body.rectTransform.forward, Color.green);
                            transition.PlayMoveTransition();
                        }

                        var added = new TransitionHelper(element);
                        added.PlayAnimateInTransition();
                        _transitions.Add(id, added);
                    },
                    onRemove: (id, index, value) =>
                    {
                        foreach (var transition in _transitions.Values)
                            transition.CacheWorldPosition();

                        var removed = _transitions[id];
                        _transitions.Remove(id);

                        removed.element.transform.SetParent(animateOutParent, true);

                        LayoutRebuilder.ForceRebuildLayoutImmediate(rectTransform);

                        removed.RestoreWorldPosition();
                        removed.PlayAnimateOutTransition(complete =>
                        {
                            if (complete)
                                Destroy(removed.element.gameObject);
                        });

                        foreach (var transition in _transitions.Values)
                        {
                            transition.RestoreWorldPosition();
                            transition.PlayMoveTransition();
                        }

                        // UnityEditor.EditorApplication.isPaused = true;
                    },
                    onDispose: () =>
                    {
                        foreach (var transition in _transitions.Values)
                            Destroy(transition.element.gameObject);
                    }
                )
            );
        }

        private AnimatedListElementContainer GenerateElementContainer(IControl child)
        {
            var container = new GameObject(nameof(AnimatedListElementContainer), typeof(RectTransform), typeof(AnimatedListElementContainer)).GetComponent<AnimatedListElementContainer>();
            child.rectTransform.SetParent(container.transform, false);
            container.Setup(child);

            return container;
        }
    }
}