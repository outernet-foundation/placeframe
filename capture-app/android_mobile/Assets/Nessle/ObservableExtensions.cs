using ObserveThing;
using TMPro;
using UnityEngine;

using static Nessle.UIBuilder;

namespace Nessle
{
    public static class ObservableExtensions
    {
        public static void From<T>(this ValueObservable<string> observable, IValueObservable<T> source)
            => observable.From(source.SelectDynamic(x => x.ToString()));

        public static void AlphaFrom<T>(this ValueObservable<Color> observable, float alpha)
            => observable.From(observable.value.Alpha(alpha));

        public static void AlphaFrom<T>(this ValueObservable<Color> observable, IValueObservable<float> alpha)
            => observable.From(alpha.SelectDynamic(x => observable.value.Alpha(x)));
    }
}

