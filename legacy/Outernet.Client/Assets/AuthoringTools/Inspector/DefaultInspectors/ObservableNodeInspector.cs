using System;
using FofX.Stateful;
using UnityEngine;

namespace Outernet.Client.AuthoringTools
{
    public abstract class ObservableNodeInspector<T> : Control<ObservableNodeInspector<T>.Props> where T : IObservableNode
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<string> targetNodePath { get; private set; }
            public ObservablePrimitive<bool> interactableSelf { get; private set; }

            public ObservablePrimitive<bool> targetIsReadonly { get; private set; }
            public ObservablePrimitive<bool> interactable { get; private set; }

            public Props() { }

            public Props(string targetNodePath, bool interactableSelf)
            {
                this.targetNodePath = new ObservablePrimitive<string>(targetNodePath);
                this.interactableSelf = new ObservablePrimitive<bool>(interactableSelf);
            }

            protected override void PostInitializeInternal()
            {
                targetIsReadonly.RegisterDerived(
                    _ =>
                    {
                        if (!App.state.TryFindChild(targetNodePath.value, out var target))
                        {
                            targetIsReadonly.value = false;
                            return;
                        }

                        targetIsReadonly.value = target.isDerived || target.HasAttribute<ReadonlyInUIAttribute>();
                    },
                    ObservationScope.Self,
                    targetNodePath
                );

                interactable.RegisterDerived(
                    _ => interactable.value = interactableSelf.value && !targetIsReadonly.value,
                    ObservationScope.Self,
                    targetNodePath
                );
            }
        }

        public RectTransform rect;

        public void Setup(string path = default, bool interactableSelf = default)
            => InitializeAndBind(new Props(path, interactableSelf));

        protected override void Bind()
        {
            AddBinding(Bindings.Track(
                _ => App.state.TryFindChild(props.targetNodePath.value, out var target) ? (T)target : default,
                target => Equals(target, default) ? Bindings.Empty() : BindTarget(target),
                new ObserverParameters() { scope = ObservationScope.Self },
                props.targetNodePath
            ));
        }

        protected abstract IDisposable BindTarget(T target);
    }
}