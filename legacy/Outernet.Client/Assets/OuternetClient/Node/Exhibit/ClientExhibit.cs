using System;
using System.Collections.Generic;
using System.Linq;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.UI;

using FofX.Stateful;
using Outernet.Shared;
using FofX;
using R3;
using Unity.Collections.LowLevel.Unsafe;

namespace Outernet.Client
{
    public class SceneExhibitProps : ObservableObject
    {
        public ObservablePrimitive<Vector3> position { get; private set; }
        public ObservablePrimitive<Quaternion> rotation { get; private set; }
        public ObservablePrimitive<bool> interacting { get; private set; }
        public ObservablePrimitive<Vector2> panelDimensions { get; private set; }
        public ObservablePrimitive<float> panelScrollPosition { get; private set; }
        public ObservablePrimitive<LinkType> linkType { get; private set; }
        public ObservablePrimitive<string> link { get; private set; }
        public ObservablePrimitive<bool> closeSelected { get; private set; }

        public SceneExhibitProps() : base() { }

        public SceneExhibitProps(
            Vector3 position = default,
            Quaternion? rotation = default,
            bool interacting = default,
            Vector2 panelDimensions = default,
            float panelScrollPosition = default,
            LinkType linkType = default,
            string link = default,
            bool closeSelected = default
        ) : base()
        {
            this.position = new ObservablePrimitive<Vector3>(position);
            this.rotation = new ObservablePrimitive<Quaternion>(rotation ?? Quaternion.identity);
            this.interacting = new ObservablePrimitive<bool>(interacting);
            this.panelDimensions = new ObservablePrimitive<Vector2>(panelDimensions);
            this.panelScrollPosition = new ObservablePrimitive<float>(panelScrollPosition);
            this.linkType = new ObservablePrimitive<LinkType>(linkType);
            this.link = new ObservablePrimitive<string>(link);
            this.closeSelected = new ObservablePrimitive<bool>(closeSelected);
        }
    }

    public class ClientExhibit : Control<SceneExhibitProps>
    {
        public Chrome chrome;
        public ContinuousScrollRect contentListScrollView;
        public CitationListView citationListView;

        private DragHelper _dragHelper;
        private ISmoother<Vector3> _positionSmoother;
        private ISmoother<Quaternion> _rotationSmoother;
        private ISmoother<Vector2> _panelDimensionSmoother;
        private ISmoother<float> _scrollSmoother;

        static readonly Vector3 vector3ZeroWidthHeight = new Vector3(0, 0, 0.25f);
        private const float backOffset = 2f;
        private bool _animating => !_animationHandle.complete;
        private TaskHandle _animationHandle = TaskHandle.Complete;

        private void Awake()
        {
            _dragHelper = contentListScrollView.gameObject.AddComponent<DragHelper>();
            _dragHelper.onDragStarted += () =>
            {
                if (isSetup)
                    props.interacting.ExecuteSet(true);
            };

            _positionSmoother = Smooth.SmoothDampVector3(x =>
            {
                if (_animating)
                    return;

                transform.position = x;
            });

            _rotationSmoother = Smooth.MoveTowardsQuaternion(x =>
            {
                if (_animating)
                    return;

                transform.rotation = x;
            });

            _panelDimensionSmoother = Smooth.MoveTowardsVector2(x => chrome.dimensions = x);
            _scrollSmoother = Smooth.SmoothDampFloat(x => contentListScrollView.verticalNormalizedPosition = x);
        }

        public override void Dispose() => citationListView.Terminate();

        private void Update()
        {
            if (_animating || !props.interacting.value)
                return;

            if (props.position.value != transform.position)
                props.position.ExecuteSet(transform.position, logLevel: FofX.LogLevel.None);

            if (props.rotation.value != transform.rotation)
                props.rotation.ExecuteSet(transform.rotation, logLevel: FofX.LogLevel.None);
        }

        protected override void Bind()
        {
            _positionSmoother.JumpToTarget(props.position.value);
            _rotationSmoother.JumpToTarget(props.rotation.value);
            _panelDimensionSmoother.JumpToTarget(props.panelDimensions.value);
            _scrollSmoother.JumpToTarget(props.panelScrollPosition.value);

            AddBinding(
                props.position.OnChange(x =>
                {
                    if (_animating)
                    {
                        _positionSmoother.JumpToTarget(x);
                        return;
                    }

                    _positionSmoother.targetValue = x;
                }),
                props.rotation.OnChange(x =>
                {
                    if (_animating)
                    {
                        _rotationSmoother.JumpToTarget(x);
                        return;
                    }

                    _rotationSmoother.targetValue = x;
                }),
                props.panelDimensions.OnChange(x => _panelDimensionSmoother.targetValue = x),
                props.panelScrollPosition.OnChange(x => _scrollSmoother.targetValue = x),
                props.interacting.OnChange(interacting =>
                {
                    contentListScrollView.inertia = interacting;
                    contentListScrollView.StopMovement();
                    contentListScrollView.movementType = interacting ?
                        ScrollRect.MovementType.Elastic :
                        ScrollRect.MovementType.Unrestricted;

                    _positionSmoother.speed = interacting ? 0f : 16f;
                    _rotationSmoother.speed = interacting ? 0f : 16f;
                    _panelDimensionSmoother.speed = interacting ? 0f : 16f;
                    _scrollSmoother.speed = interacting ? 0f : 16f;
                }),
                Bindings.DynamicBind(
                    _ =>
                    {
                        citationListView.Terminate();

                        return TaskHandle.Execute(_ => GetCitations(props.linkType.value, props.link.value)
                            .ContinueWith(citationListView.Initialize))
                            .ToDisposable();
                    },
                    ObservationScope.Self,
                    props.linkType,
                    props.link
                ),
                contentListScrollView.onValueChanged.OnRaised(x =>
                {
                    if (!props.interacting.value)
                        return;

                    props.panelScrollPosition.ExecuteSetOrDelay(x.y, logLevel: FofX.LogLevel.None);
                }),
                chrome.dimensionsSubject.Subscribe(x =>
                {
                    if (props.panelDimensions.value == x || !props.interacting.value)
                        return; //hack- panel dimensions are set every frame

                    props.panelDimensions.ExecuteSetOrDelay(x, logLevel: FofX.LogLevel.None);
                }),
                chrome.onResizeStarted.OnRaised(() => props.interacting.ExecuteSetOrDelay(true)),
                chrome.onResizeEnded.OnRaised(() => props.interacting.ExecuteSetOrDelay(false)),
                chrome.onCarryStarted.OnRaised(() => props.interacting.ExecuteSetOrDelay(true)),
                chrome.onCarryEnded.OnRaised(() => props.interacting.ExecuteSetOrDelay(false)),
                chrome.onCloseSelected.OnRaised(() => props.closeSelected.ExecuteSet(true))
            );
        }

        private async UniTask<IEnumerable<CitationView.Citation>> GetCitations(LinkType linkType, string link)
        {
            switch (linkType)
            {
                case LinkType.Address:
                    {
                        var address = await OuternetAPI.GetAddressDataByName(link);
                        var addressMentions = await OuternetAPI.GetDocumentSpanAddressMentions(address.id);

                        return addressMentions.Select(mention =>
                        {
                            var first_page = mention.target_page - mention.previous_pages;
                            var last_page = mention.target_page + mention.next_pages;

                            return new CitationView.Citation
                            {
                                title = mention.document.title,
                                author = mention.document.author,
                                year = mention.document.year_raw,
                                page = mention.target_page.ToString(),
                                quote = mention.document_span.document_span_annotation.Where(annotation => annotation.type == "quote").First().annotation,
                                pageSpan = first_page == last_page ? first_page.ToString() : $"{first_page}-{last_page}",
                                addressMention = mention.address_mention,
                                pages = mention.document_span.document_span_page.Select(spanPage => spanPage.document_page)
                            };
                        });
                    }
                case LinkType.Annotation:
                    {
                        var annotation = await OuternetAPI.GetAnnotation(link);

                        var first_page = annotation.target_page - annotation.previous_pages;
                        var last_page = annotation.target_page + annotation.next_pages;

                        return new List<CitationView.Citation>
                        {
                            new CitationView.Citation
                            {
                                title = annotation.document.title,
                                author = annotation.document.author,
                                year = annotation.document.year_raw,
                                page = annotation.target_page.ToString(),
                                quote = annotation.annotation,
                                pageSpan = first_page == last_page ? first_page.ToString() : $"{first_page}-{last_page}",
                                addressMention = annotation.document_span.document_span_address_mention.First().address_mention,
                                pages = annotation.document_span.document_span_page.Select(spanPage => spanPage.document_page)
                            }
                        };
                    }
                case LinkType.ImageList:
                    {
                        var githubUrl = GithubAPI.ParseFolderUrl(link);
                        var imageList = await GithubAPI.GetFolderContents(githubUrl.apiUrl);
                        return new List<CitationView.Citation>
                        {
                            new CitationView.Citation
                            {
                                title = githubUrl.folderName,
                                author = githubUrl.author,
                                year = "N/A",
                                page = "N/A",
                                quote = "N/A",
                                pageSpan = "N/A",
                                addressMention = "N/A",
                                pages = imageList
                                    .OrderBy(file => file)
                                    .Select((file, index) => new DocumentPage
                                    {
                                        id = file,
                                        page_num = index,
                                        document_id = githubUrl.folderName,
                                        page_image_uri = file,
                                        document_key = githubUrl.folderName
                                    })
                            }
                        };
                    }
                default:
                    return new List<CitationView.Citation>();
            }

        }

        public void Open()
        {
            CancelAnimation();
            transform.position = props.position.value;
            transform.rotation = props.rotation.value;
        }

        public UniTask Open(Vector3 startPosition, Quaternion startRotation, float duration = 1f)
        {
            CancelAnimation();
            _animationHandle = TaskHandle.Execute(token => Interpolation.Run(0f, 1f, duration, t =>
            {
                var offset = props.rotation.value * Vector3.back * backOffset;
                var animationControlPoint = props.position.value + offset;

                transform.localScale = Vector3.Lerp(vector3ZeroWidthHeight, Vector3.one, t * t);
                transform.rotation = Quaternion.Slerp(startRotation, props.rotation.value, t);
                transform.position = Vector3.Lerp(
                    Vector3.Lerp(startPosition, animationControlPoint, t),
                    Vector3.Lerp(animationControlPoint, props.position.value, t),
                    t
                );

            }, token));

            return _animationHandle.completionTask;
        }

        public UniTask Close(Vector3 endPosition, Quaternion endRotation, float duration = 1f)
        {
            CancelAnimation();
            _animationHandle = TaskHandle.Execute(token => Interpolation.Run(0f, 1f, duration, t =>
            {
                var offset = props.rotation.value * Vector3.back * backOffset;
                var animationControlPoint = props.position.value + offset;

                transform.localScale = Vector3.Lerp(Vector3.one, vector3ZeroWidthHeight, t * t);
                transform.rotation = Quaternion.Slerp(props.rotation.value, endRotation, t);
                transform.position = Vector3.Lerp(
                    Vector3.Lerp(props.position.value, animationControlPoint, t),
                    Vector3.Lerp(animationControlPoint, endPosition, t),
                    t
                );

            }, token));

            return _animationHandle.completionTask;
        }

        public void CancelAnimation()
        {
            _animationHandle.Cancel();
        }

        public static ClientExhibit Create(
            Vector3 position = default,
            Quaternion? rotation = default,
            bool interacting = default,
            Vector2 panelDimensions = default,
            float panelScrollPosition = default,
            LinkType linkType = default,
            string link = default,
            bool closeSelected = default,
            Transform parent = default,
            Func<SceneExhibitProps, IDisposable> bind = default
        )
        {
            var instance = PrefabSystem.Create(PrefabSystem.clientExhibit, parent);
            instance.InitializeAndBind(new SceneExhibitProps(position, rotation, interacting, panelDimensions, panelScrollPosition, linkType, link, closeSelected));

            instance.AddBinding(Bindings.OnRelease(() => PrefabSystem.Destroy(instance)));

            if (bind != null)
                instance.AddBinding(bind(instance.props));

            return instance;
        }
    }
}