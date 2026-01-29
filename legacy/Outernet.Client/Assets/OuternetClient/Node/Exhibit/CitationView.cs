using System;
using System.Collections.Generic;
using System.Linq;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Outernet.Client
{
    [RequireComponent(typeof(RectTransform))]
    public class CitationView : MonoBehaviour
    {
        public class Citation
        {
            public string title;
            public string author;
            public string year;
            public string page;
            public string pageSpan;
            public string addressMention;
            public string quote;
            public IEnumerable<DocumentPage> pages;
        }

        public Action onRebuildLayout;

        public TextMeshProUGUI title;
        public TextMeshProUGUI author;
        public TextMeshProUGUI year;
        public TextMeshProUGUI page;
        public TextMeshProUGUI pageSpan;
        public TextMeshProUGUI addressMention;
        public TextMeshProUGUI quote;
        public ImageListView imageListView;

        // public void Initialize(Citation citation)
        // {
        //     var document = citation.document;

        //     title.SetText(document.title == null || document.title == "" ? "Unknown" : document.title);
        //     author.SetText(document.author == null || document.author == "" ? "Unknown" : document.author);
        //     year.SetText(document.year_raw);
        //     page.SetText(citation.target_page.ToString());
        //     quote.SetText(citation.document_span.document_span_annotation.First().annotation);

        //     var first_page = citation.target_page - citation.previous_pages;
        //     var last_page = citation.target_page + citation.next_pages;

        //     if (first_page == last_page)
        //     {
        //         pageSpan.SetText(first_page.ToString());
        //     }
        //     else
        //     {
        //         pageSpan.SetText($"{first_page}-{last_page}");
        //     }

        //     addressMention.SetText(citation.address_mention);

        //     imageListView.Initialize(citation.document_span.document_span_page.Select(spanPage => spanPage.document_page).ToArray());
        //     imageListView.onRebuildLayout += () =>
        //     {
        //         if (onRebuildLayout != null)
        //         {
        //             onRebuildLayout();
        //         }
        //         else
        //         {
        //             LayoutRebuilder.ForceRebuildLayoutImmediate((RectTransform)transform);
        //         }
        //     };
        // }

        public void Initialize(Citation citation)
        {
            title.SetText(citation.title == null || citation.title == "" ? "Unknown" : citation.title);
            author.SetText(citation.author == null || citation.author == "" ? "Unknown" : citation.author);
            year.SetText(citation.year);
            page.SetText(citation.page);
            pageSpan.SetText(citation.pageSpan);
            addressMention.SetText(citation.addressMention);
            quote.SetText(citation.quote);

            imageListView.Initialize(citation.pages
                .OrderBy(page => page.page_num)
                .Select(page => page.page_image_uri)
                .ToArray());

            imageListView.onRebuildLayout += () =>
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

        public void Terminate()
        {
            imageListView.Terminate();
        }
    }
}