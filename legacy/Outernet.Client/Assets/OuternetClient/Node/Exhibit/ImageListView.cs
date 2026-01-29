using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Outernet.Client
{
    [RequireComponent(typeof(RectTransform))]
    [RequireComponent(typeof(VerticalLayoutGroup))]
    public class ImageListView : MonoBehaviour
    {
        public Action onRebuildLayout;

        private List<ImageView> imageContentViews = new();

        public void Initialize(IEnumerable<string> uris)
        {
            foreach (var uri in uris)
            {
                var imageContentView = PrefabSystem.Create(PrefabSystem.imageView);
                imageContentViews.Add(imageContentView);

                imageContentView.transform.SetParent(transform, false);
                imageContentView.Initialize(uri);

                imageContentView.onRebuildLayout += () =>
                {
                    if (onRebuildLayout != null)
                    {
                        onRebuildLayout();
                    }
                    else
                    {
                        LayoutRebuilder.ForceRebuildLayoutImmediate((RectTransform)transform);
                    }
                };
            }
        }

        public void Terminate()
        {
            foreach (var imageContentView in imageContentViews)
            {
                imageContentView.Terminate();
                PrefabSystem.Destroy(imageContentView);
            }
            imageContentViews.Clear();
        }
    }
}