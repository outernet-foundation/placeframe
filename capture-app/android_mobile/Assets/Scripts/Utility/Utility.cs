using Nessle;
using ObserveThing;
using UnityEngine;

using static Nessle.UIBuilder;

using ImageType = UnityEngine.UI.Image.Type;
using ImageFillMethod = UnityEngine.UI.Image.FillMethod;
using System;
using System.Collections.Generic;

namespace PlerionClient.Client
{
    public static class Utility
    {
        public static void SingleChild(this IControl control, IValueObservable<IControl> child)
        {
            control.AddBinding(child.Subscribe(x =>
            {
                x.previousValue?.Dispose();
                x.currentValue?.parent.From(control);
            }));
        }

        public static void From(this ImageProps imageProps, IValueObservable<ImageProps> source)
        {
            imageProps.sprite.From(source.SelectDynamic<ImageProps, Sprite>(x => x.sprite));
            imageProps.color.From(source.SelectDynamic<ImageProps, Color>(x => x.color));
            imageProps.imageType.From(source.SelectDynamic<ImageProps, ImageType>(x => x.imageType));
            imageProps.fillCenter.From(source.SelectDynamic<ImageProps, bool>(x => x.fillCenter));
            imageProps.pixelsPerUnitMultiplier.From(source.SelectDynamic<ImageProps, float>(x => x.pixelsPerUnitMultiplier));
            imageProps.raycastTarget.From(source.SelectDynamic<ImageProps, bool>(x => x.raycastTarget));
            imageProps.raycastPadding.From(source.SelectDynamic<ImageProps, Vector4>(x => x.raycastPadding));
            imageProps.useSpriteMesh.From(source.SelectDynamic<ImageProps, bool>(x => x.useSpriteMesh));
            imageProps.preserveAspect.From(source.SelectDynamic<ImageProps, bool>(x => x.preserveAspect));
            imageProps.fillOrigin.From(source.SelectDynamic<ImageProps, int>(x => x.fillOrigin));
            imageProps.fillMethod.From(source.SelectDynamic<ImageProps, ImageFillMethod>(x => x.fillMethod));
            imageProps.fillAmount.From(source.SelectDynamic<ImageProps, float>(x => x.fillAmount));
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
    }
}