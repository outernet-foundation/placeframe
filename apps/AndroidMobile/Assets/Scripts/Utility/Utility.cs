using Nessle;
using ObserveThing;
using UnityEngine;

using static Nessle.UIBuilder;

using ImageType = UnityEngine.UI.Image.Type;
using ImageFillMethod = UnityEngine.UI.Image.FillMethod;
using System;
using System.Collections.Generic;

namespace Placeframe.Client
{
    public static class Utility
    {
        public static LayoutProps FillParentProps(LayoutProps props = default)
        {
            props.anchorMin = props.anchorMin ?? Props.Value(new Vector2(0, 0));
            props.anchorMax = props.anchorMax ?? Props.Value(new Vector2(1, 1));
            props.offsetMin = props.offsetMin ?? Props.Value(new Vector2(0, 0));
            props.offsetMax = props.offsetMax ?? Props.Value(new Vector2(0, 0));
            return props;
        }

        public static IDisposable SubscribeEach<T>(this ICollectionObservable<T> collection, Func<T, IDisposable> subscribe)
        {
            Dictionary<T, IDisposable> subscriptions = new Dictionary<T, IDisposable>();
            return collection.Subscribe(
                args =>
                {
                    if (args.operationType == OpType.Add)
                    {
                        subscriptions.Add(args.element, subscribe(args.element));
                    }
                    else if (args.operationType == OpType.Remove)
                    {
                        subscriptions[args.element].Dispose();
                        subscriptions.Remove(args.element);
                    }
                },
                onDispose: () =>
                {
                    foreach (var subscription in subscriptions)
                        subscription.Value.Dispose();

                    subscriptions.Clear();
                }
            );
        }

        public static IValueObservable<int> FollowIndexDynamic<T>(this IListObservable<T> list, int index)
            => new FollowIndexObservable<T>(list, index);

        public static void AddRange<T>(this ListObservable<T> list, params T[] elements)
        {
            list.AddRange(elements);
        }
    }
}