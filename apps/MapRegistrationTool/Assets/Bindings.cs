using System;
using System.Collections.Generic;
using System.Linq;

using UnityEngine.Events;
using UnityEngine;
using Unity.Mathematics;

using FofX;
using FofX.Stateful;

namespace Placeframe.MapRegistrationTool
{
    public static class Bindings
    {
        private class ActionDisposable : IDisposable
        {
            private bool _disposed;
            private Action _onDispose;

            public ActionDisposable(Action onDispose)
            {
                _onDispose = onDispose;
            }

            public void Dispose()
            {
                if (_disposed)
                    return;

                _disposed = true;
                _onDispose.Invoke();
            }
        }

        public class CompositeDisposable : IDisposable
        {
            private bool _disposed;
            private HashSet<IDisposable> _disposables;

            public CompositeDisposable(IEnumerable<IDisposable> disposables)
            {
                _disposables = new HashSet<IDisposable>(disposables);
            }

            public CompositeDisposable(params IDisposable[] disposables)
            {
                _disposables = new HashSet<IDisposable>(disposables);
            }

            public void Add(IDisposable disposable)
            {
                _disposables.Add(disposable);
            }

            public void Remove(IDisposable disposable)
            {
                _disposables.Remove(disposable);
            }

            public void Dispose()
            {
                if (_disposed)
                    return;

                _disposed = true;

                foreach (var disposable in _disposables)
                    disposable.Dispose();
            }
        }

        public static IDisposable OnRelease(Action onRelease)
            => new ActionDisposable(onRelease);

        public static IDisposable DestroyOnRelease(this UnityEngine.Object obj)
            => OnRelease(() => UnityEngine.Object.Destroy(obj));

        public static IDisposable Compose(IEnumerable<IDisposable> bindings)
            => new CompositeDisposable(bindings);

        public static IDisposable Compose(params IDisposable[] bindings)
            => new CompositeDisposable(bindings);

        public static IDisposable Observer(ObserverDelegate observer, ObservationScope scope, params IObservableNode[] nodes)
            => Observer(observer, new ObserverParameters() { scope = scope }, nodes);

        public static IDisposable Observer(ObserverDelegate observer, ObserverParameters parameters, params IObservableNode[] nodes)
        {
            var context = nodes[0].context;
            context.RegisterObserver(observer, parameters, nodes);
            return OnRelease(() => context.DeregisterObserver(observer));
        }

        public static IDisposable Derive<T>(this T derived, ObserverDelegate observer, ObservationScope scope, params IObservableNode[] nodes)
            where T : IObservableNode
        {
            derived.RegisterDerived(observer, scope, nodes);
            return OnRelease(derived.DeregisterDerived);
        }

        public static IDisposable DynamicBind(Func<NodeChangeEventArgs, IDisposable> bind, ObservationScope scope, params IObservableNode[] nodes)
        {
            IDisposable binding = Empty();
            return Compose(
                Observer(
                    args =>
                    {
                        binding?.Dispose();

                        if (nodes.All(x => x.disposed))
                            return;

                        binding = bind(args);
                    },
                    scope,
                    nodes
                ),
                OnRelease(() => binding?.Dispose())
            );
        }

        public static IDisposable DynamicBind<T>(this ObservablePrimitive<T> primitive, Func<T, IDisposable> onChange)
        {
            return DynamicBind
            (
                args => onChange(primitive.value),
                ObservationScope.Self,
                primitive
            );
        }

        public static IDisposable Track<T>(Func<NodeChangeEventArgs, T> track, Action<T> onChange, ObserverParameters parameters, params IObservableNode[] nodes)
        {
            T currentValue = default;
            IDisposable binding = default;

            binding = Compose(
                Observer(
                    args =>
                    {
                        if (nodes.Any(x => x.disposed))
                        {
                            binding?.Dispose();
                            binding = null;
                            return;
                        }

                        T newValue = track(args);
                        if (!Equals(newValue, currentValue))
                        {
                            currentValue = newValue;
                            onChange(currentValue);
                        }
                    },
                    parameters,
                    nodes
                )
            );

            return binding;
        }

        public static IDisposable Track<T>(Func<NodeChangeEventArgs, T> track, Func<T, IDisposable> bind, ObserverParameters parameters, params IObservableNode[] nodes)
        {
            IDisposable subBinding = null;
            return Compose(
                Track(
                    track,
                    x =>
                    {
                        subBinding?.Dispose();
                        subBinding = bind(x);
                    },
                    parameters,
                    nodes
                ),
                OnRelease(() => subBinding?.Dispose())
            );
        }

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, Action<KVP<TKey, TValue>> onChanged)
            where TValue : IObservableNode, new() => dictionary.Track(key, false, onChanged);

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, bool isDerived, Action<KVP<TKey, TValue>> onChanged)
            where TValue : IObservableNode, new()
        {
            return Track(
                args => dictionary.TryGetValue(key, out var value) ?
                    new KVP<TKey, TValue>(key, value) :
                    default,
                onChanged,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = isDerived },
                dictionary
            );
        }

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, Func<KVP<TKey, TValue>, IDisposable> bind)
            where TValue : IObservableNode, new() => dictionary.Track(key, false, bind);

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, TKey key, bool isDerived, Func<KVP<TKey, TValue>, IDisposable> bind)
            where TValue : IObservableNode, new()
        {
            return Track(
                args => dictionary.TryGetValue(key, out var value) ?
                    new KVP<TKey, TValue>(key, value) :
                    default,
                bind,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = isDerived },
                dictionary
            );
        }

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, ObservablePrimitive<TKey> key, Action<KVP<TKey, TValue>> onChanged)
            where TValue : IObservableNode, new() => dictionary.Track(key, false, onChanged);

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, ObservablePrimitive<TKey> key, bool isDerived, Action<KVP<TKey, TValue>> onChanged)
            where TValue : IObservableNode, new()
        {
            return Track(
                args => dictionary.TryGetValue(key.value, out var value) ?
                    new KVP<TKey, TValue>(key.value, value) :
                    default,
                onChanged,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = isDerived },
                dictionary,
                key
            );
        }

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, ObservablePrimitive<TKey> key, Func<KVP<TKey, TValue>, IDisposable> bind)
            where TValue : IObservableNode, new() => dictionary.Track(key, false, bind);

        public static IDisposable Track<TKey, TValue>(this ObservableDictionary<TKey, TValue> dictionary, ObservablePrimitive<TKey> key, bool isDerived, Func<KVP<TKey, TValue>, IDisposable> bind)
            where TValue : IObservableNode, new()
        {
            return Track(
                args => dictionary.TryGetValue(key.value, out var value) ?
                    new KVP<TKey, TValue>(key.value, value) :
                    default,
                bind,
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = isDerived },
                dictionary,
                key
            );
        }

        public static IDisposable List<TElement, TView>(this IObservableCollection<TElement> collection, Transform parent, Func<TElement, TView> getView)
            where TView : Component, IDisposable
        {
            return collection.Each(
                x =>
                {
                    var view = getView(x);
                    view.transform.SetParent(parent, false);
                    return view;
                }
            );
        }

        public static IDisposable Each<T>(this IObservableCollection<T> collection, Action<T> onAdd)
            => collection.Each(value => { if (collection.Contains(value)) onAdd(value); return Empty(); });

        public static IDisposable Each<T>(this IObservableCollection<T> collection, Func<T, IDisposable> bind)
            => collection.Each(default, bind);

        public static IDisposable Each<T>(this IObservableCollection<T> collection, bool isDerived, Func<T, IDisposable> bind)
        {
            Dictionary<T, IDisposable> bindingByElement = new Dictionary<T, IDisposable>();
            return Compose(
                Observer(
                    args =>
                    {
                        if (args.initialize)
                        {
                            foreach (var element in collection)
                                bindingByElement.Add(element, bind(element));

                            return;
                        }

                        foreach (var change in args.changes)
                        {
                            if (change.changeType == ChangeType.Add)
                            {
                                bindingByElement.Add(
                                    (T)change.collectionElement,
                                    bind((T)change.collectionElement)
                                );
                            }
                            else if (change.changeType == ChangeType.Remove)
                            {
                                var binding = bindingByElement[(T)change.collectionElement];
                                bindingByElement.Remove((T)change.collectionElement);
                                binding.Dispose();
                            }
                        }
                    },
                    new ObserverParameters() { scope = ObservationScope.Self, isDerived = isDerived },
                    collection
                ),
                OnRelease(() =>
                {
                    foreach (var binding in bindingByElement.Values)
                        binding.Dispose();
                })
            );
        }

        public static IDisposable EachRaw(this IObservableCollection collection, Action<object> onAdd)
            => collection.EachRaw(value => { onAdd(value); return Empty(); });

        public static IDisposable EachRaw(this IObservableCollection collection, Func<object, IDisposable> bind)
        {
            Dictionary<object, IDisposable> bindingByElement = new Dictionary<object, IDisposable>();
            return Compose(
                Observer(
                    args =>
                    {
                        if (args.initialize)
                        {
                            foreach (var element in collection)
                                bindingByElement.Add(element, bind(element));

                            return;
                        }

                        foreach (var change in args.changes)
                        {
                            if (change.changeType == ChangeType.Add)
                            {
                                bindingByElement.Add(
                                    change.collectionElement,
                                    bind(change.collectionElement)
                                );
                            }
                            else if (change.changeType == ChangeType.Remove)
                            {
                                var binding = bindingByElement[change.collectionElement];
                                bindingByElement.Remove(change.collectionElement);
                                binding.Dispose();
                            }
                        }
                    },
                    ObservationScope.Self,
                    collection
                ),
                OnRelease(() =>
                {
                    foreach (var binding in bindingByElement.Values)
                        binding.Dispose();
                })
            );
        }

        public static IDisposable BindText<T>(this TMPro.TextMeshProUGUI label, ObservablePrimitive<T> bindTo)
            => bindTo.OnChange(x => label.text = x?.ToString());

        public static IDisposable BindValue(this UnityEngine.UI.Slider slider, ObservablePrimitive<float> bindTo)
            => bindTo.OnChange(x => slider.value = x);

        public static IDisposable OnRaised(this UnityEvent bindTo, UnityAction listener)
        {
            bindTo.AddListener(listener);
            return OnRelease(() => bindTo.RemoveListener(listener));
        }

        public static IDisposable OnRaised<T0>(this UnityEvent<T0> bindTo, UnityAction<T0> listener)
        {
            bindTo.AddListener(listener);
            return OnRelease(() => bindTo.RemoveListener(listener));
        }

        public static IDisposable OnChange<T>(this ObservablePrimitive<T> primitive, Action<T> onChange)
            => primitive.OnChange(false, onChange);

        public static IDisposable OnChange<T>(this ObservablePrimitive<T> primitive, bool isDerived, Action<T> onChange)
        {
            return Observer(
                args =>
                {
                    if (args.initialize)
                    {
                        onChange(primitive.value);
                        return;
                    }

                    foreach (var change in args.changes)
                    {
                        if (change.changeType == ChangeType.Set)
                        {
                            onChange(primitive.value);
                            return;
                        }
                    }
                },
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = isDerived },
                primitive
            );
        }

        public static IDisposable OnChange(this IObservablePrimitive primitive, Action<object> onChange)
            => primitive.OnChange(false, onChange);

        public static IDisposable OnChange(this IObservablePrimitive primitive, bool isDerived, Action<object> onChange)
        {
            return Observer(
                args =>
                {
                    if (args.initialize || args.changes.Any(x => x.changeType == ChangeType.Set))
                        onChange(primitive.GetValue());
                },
                new ObserverParameters() { scope = ObservationScope.Self, isDerived = isDerived },
                primitive
            );
        }

        public static IDisposable Empty()
            => OnRelease(() => { });

        public delegate bool TryParseDelegate<T>(string input, out T result);

        private static IDisposable BindInput<T>(this TMPro.TMP_InputField inputField, ObservablePrimitive<T> bindTo, TryParseDelegate<T> tryParse)
        {
            bool applyingFromState = false;

            return Compose(
                bindTo.OnChange(
                    value =>
                    {
                        applyingFromState = true;
                        inputField.text = bindTo.value.ToString();
                        applyingFromState = false;
                    }
                ),
                inputField.onEndEdit.OnRaised(x =>
                {
                    if (applyingFromState)
                        return;

                    bool inputParsed = tryParse(x, out var result);

                    bindTo.context.ExecuteActionOrDelay(
                        bindTo,
                        new SetPrimitiveValueAction<T>(inputParsed ? result : default)
                    );
                })
            );
        }

        public static IDisposable BindInput(this TMPro.TMP_InputField inputField, ObservablePrimitive<double> bindTo)
            => inputField.BindInput(bindTo, double.TryParse);

        public static IDisposable BindInput(this TMPro.TMP_InputField inputField, ObservablePrimitive<float> bindTo)
            => inputField.BindInput(bindTo, float.TryParse);

        public static IDisposable BindInput(this TMPro.TMP_InputField inputField, ObservablePrimitive<int> bindTo)
            => inputField.BindInput(bindTo, int.TryParse);

        public static IDisposable BindInput(this TMPro.TMP_InputField inputField, ObservablePrimitive<string> bindTo)
        {
            bool applyingFromState = false;
            return Compose(
                bindTo.OnChange(
                    value =>
                    {
                        applyingFromState = true;
                        inputField.text = bindTo.value;
                        applyingFromState = false;
                    }
                ),
                inputField.onEndEdit.OnRaised(
                    x =>
                    {
                        if (applyingFromState)
                            return;

                        bindTo.context.ExecuteActionOrDelay(
                            bindTo,
                            new SetPrimitiveValueAction<string>(inputField.text)
                        );
                    }
                )
            );
        }

        public static IDisposable BindActive(this GameObject gameObject, ObservablePrimitive<bool> bindTo, bool invert = false)
            => bindTo.OnChange(x => gameObject.SetActive(invert ? !x : x));

        public static IDisposable BindBounds(this BoxCollider collider, ObservablePrimitive<Bounds> bindTo)
            => bindTo.OnChange(x =>
            {
                collider.center = x.center;
                collider.size = x.size;
            });

        public static IDisposable From<T, U>(this ObservablePrimitive<U> node, ObservablePrimitive<T> fromNode, Func<T, U> convert)
        {
            return node.Derive(
                args =>
                {
                    if (args.initialize || args.changes.Any(x => x.changeType == ChangeType.Set))
                        node.value = convert(fromNode.value);
                },
                ObservationScope.Self,
                fromNode
            );
        }

        public static IDisposable From<T>(this T node, T fromNode)
            where T : IObservableNode
        {
            return node.Derive(
                args =>
                {
                    if (args.initialize)
                    {
                        fromNode.CopyTo(node);
                        return;
                    }

                    foreach (var change in args.changes)
                    {
                        if (change.changeType == ChangeType.Dispose)
                            continue;

                        var changeTarget = node.GetChild(change.source.nodePath.Substring(fromNode.nodePath.Length));
                        changeTarget.ApplyChange(change);
                    }
                },
                ObservationScope.All,
                fromNode
            );
        }

        public static IDisposable From<T>(this ObservablePrimitive<T> primitive, Func<NodeChangeEventArgs, T> evaluate, ObservationScope scope, params IObservableNode[] nodes)
        {
            return primitive.Derive(
                args => primitive.value = evaluate(args),
                scope,
                nodes
            );
        }

        public static IDisposable BindTo<T>(this T downstream, T upstream) where T : IObservableNode
        {
            return downstream.BindTo(
                upstream,
                (downstream, args) =>
                {
                    if (args.initialize)
                    {
                        upstream.CopyTo(downstream);
                        return;
                    }

                    foreach (var change in args.changes)
                    {
                        if (change.changeType == ChangeType.Dispose)
                            continue;

                        downstream.GetChild(change.source.nodePath.Substring(upstream.nodePath.Length)).ApplyChange(change);
                    }
                },
                (upstream, args) =>
                {
                    if (args.initialize)
                        return;

                    foreach (var change in args.changes)
                    {
                        if (change.changeType == ChangeType.Dispose)
                            continue;

                        upstream.GetChild(change.source.nodePath.Substring(downstream.nodePath.Length)).ApplyChange(change);
                    }
                }
            );
        }

        public static IDisposable BindTo<TUp, TDown>(
            this TDown downstream,
            TUp upstream,
            Action<TDown, NodeChangeEventArgs> pushChangeDownstream,
            Action<TUp, NodeChangeEventArgs> pushChangeUpstream)
            where TUp : IObservableNode
            where TDown : IObservableNode
        {
            return Relationship(
                args => pushChangeDownstream(downstream, args), ObservationScope.All, new IObservableNode[] { upstream },
                args => pushChangeUpstream(upstream, args), ObservationScope.All, new IObservableNode[] { downstream }
            );
        }

        public static IDisposable BindContains<T>(this ObservableSet<T> collection, T value, ObservablePrimitive<bool> shouldContain)
        {
            return Relationship(
                args => shouldContain.value = collection.Contains(value),
                ObservationScope.All,
                new IObservableNode[] { collection },
                args =>
                {
                    if (shouldContain.value)
                    {
                        collection.Add(value);
                    }
                    else
                    {
                        collection.Remove(value);
                    }
                },
                ObservationScope.All,
                new IObservableNode[] { shouldContain }
            );
        }

        public static IDisposable Relationship(
            ObserverDelegate observer1, ObservationScope scope1, IObservableNode[] nodes1,
            ObserverDelegate observer2, ObservationScope scope2, IObservableNode[] nodes2
        ) => new RelationshipBinding(App.state.context, observer1, scope1, nodes1, observer2, scope2, nodes2);

        public static IDisposable BindTo<T, U>(this ObservablePrimitive<U> downstream, ObservablePrimitive<T> upstream, Func<T, U> toDownstream, Func<U, T> toUpstream)
        {
            return downstream.BindTo(
                upstream,
                (downstream, _) => downstream.value = toDownstream(upstream.value),
                (upstream, _) => upstream.value = toUpstream(downstream.value)
            );
        }

        public static IDisposable BindTo<T>(this ObservablePrimitive<string> downstream, ObservablePrimitive<T> upstream, TryParseDelegate<T> tryParseDelegate)
        {
            return downstream.BindTo(
                upstream,
                (downstream, _) => downstream.value = upstream.value.ToString(),
                (upstream, _) => upstream.value = tryParseDelegate(downstream.value, out var value) ? value : default
            );
        }

        public static IDisposable BindTo(this ObservablePrimitive<string> downstream, ObservablePrimitive<float> upstream)
            => downstream.BindTo(upstream, float.TryParse);

        public static IDisposable BindTo(this ObservablePrimitive<string> downstream, ObservablePrimitive<int> upstream)
            => downstream.BindTo(upstream, int.TryParse);

        public static IDisposable BindTo(this ObservablePrimitive<string> downstream, ObservablePrimitive<double> upstream)
            => downstream.BindTo(upstream, double.TryParse);

        public static IDisposable Observe<T>(this T source, ObserverDelegate onChange)
            where T : IObservableNode => Observer(onChange, ObservationScope.All, source);

        public static IDisposable Observe<T>(this T source, ObserverParameters parameters, ObserverDelegate onChange)
            where T : IObservableNode => Observer(onChange, parameters, source);

        public static IDisposable BindECEFTransform(ObservablePrimitive<double3> ecefPosition, ObservablePrimitive<Quaternion> ecefRotation, ObservablePrimitive<Vector3> localPosition, ObservablePrimitive<Quaternion> localRotation)
        {
            return Relationship(
                _ =>
                {
                    var transform = LocationUtilities.UnityFromEcef(ecefPosition.value, ecefRotation.value);
                    localPosition.value = transform.position;
                    localRotation.value = transform.rotation;
                },
                ObservationScope.Self,
                new IObservableNode[] { ecefPosition, ecefRotation, App.state.ecefToUnityWorldMatrix },
                _ =>
                {
                    var transform = LocationUtilities.EcefFromUnity(localPosition.value, localRotation.value);
                    ecefPosition.value = transform.position;
                    ecefRotation.value = transform.rotation;
                },
                ObservationScope.Self,
                new IObservableNode[] { localPosition, localRotation, App.state.unityWorldToEcefMatrix }
            );
        }

        public static IDisposable ToDisposable(this TaskHandle handle)
        {
            return OnRelease(handle.Cancel);
        }
    }
}