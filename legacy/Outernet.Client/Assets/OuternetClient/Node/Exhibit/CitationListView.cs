using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Outernet.Client
{
    [RequireComponent(typeof(RectTransform))]
    [RequireComponent(typeof(VerticalLayoutGroup))]
    public class CitationListView : MonoBehaviour
    {
        private List<CitationView> citationViews = new();

        public void Initialize(IEnumerable<CitationView.Citation> citations)
        {
            foreach (var citationView in citationViews)
            {
                citationView.Terminate();
                PrefabSystem.Destroy(citationView);
            }

            citationViews.Clear();

            foreach (var citation in citations)
            {
                var citationView = PrefabSystem.Create(PrefabSystem.citationView);
                citationViews.Add(citationView);

                citationView.transform.SetParent(transform, false);
                citationView.Initialize(citation);

                citationView.onRebuildLayout += () =>
                    LayoutRebuilder.ForceRebuildLayoutImmediate((RectTransform)transform);
            }
        }

        public void Terminate()
        {
            foreach (var citationView in citationViews)
            {
                citationView.Terminate();
                PrefabSystem.Destroy(citationView);
            }

            citationViews.Clear();
        }
    }
}