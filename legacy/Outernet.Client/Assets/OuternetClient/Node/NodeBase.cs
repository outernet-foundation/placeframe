using System;
using System.Threading;

using UnityEngine;

using FofX;
using FofX.Stateful;

using Cysharp.Threading.Tasks;

namespace Outernet.Client
{
    public class NodeProps : ObservableObject
    {
        public ObservablePrimitive<int> nodeID { get; private set; }
        public ObservablePrimitive<Guid> uuid { get; private set; }
        public ObservablePrimitive<string> link { get; private set; }
        public ObservablePrimitive<Shared.LinkType> linkType { get; private set; }
        public ObservablePrimitive<string> label { get; private set; }
        public ObservablePrimitive<Shared.LabelType> labelType { get; private set; }
        public ObservablePrimitive<float> labelScale { get; private set; }
        public ObservablePrimitive<Vector2> labelDimensions { get; private set; }
        public ObservablePrimitive<Vector3> position { get; set; }
        public ObservablePrimitive<Quaternion> rotation { get; set; }
        public ObservablePrimitive<bool> visible { get; private set; }

        public ObservablePrimitive<bool> hoveredLocally { get; private set; }
        public ObservablePrimitive<bool> hoveredRemotely { get; private set; }
        public ObservablePrimitive<bool> hovered { get; private set; }
        public ObservablePrimitive<bool> interacting { get; private set; }

        public ObservablePrimitive<bool> exhibitOpen { get; private set; }
        public ObservablePrimitive<Vector3> exhibitPosition { get; private set; }
        public ObservablePrimitive<Quaternion> exhibitRotation { get; private set; }
        public ObservablePrimitive<Vector2> exhibitPanelDimensions { get; private set; }
        public ObservablePrimitive<float> exhibitPanelScrollPosition { get; private set; }

        public NodeProps() : base() { }

        public NodeProps(
            int nodeID = default,
            Guid uuid = default,
            string link = default,
            Shared.LinkType linkType = default,
            string label = default,
            Shared.LabelType labelType = default,
            float labelScale = default,
            Vector2 labelDimensions = default,
            Vector3 position = default,
            Quaternion? rotation = default,
            bool visible = default,
            bool exhibitOpen = default,
            Vector3 exhibitPosition = default,
            Quaternion? exhibitRotation = default,
            Vector2 exhibitPanelDimensions = default,
            float exhibitPanelScrollPosition = default
        )
        {
            this.nodeID = new ObservablePrimitive<int>(nodeID);
            this.uuid = new ObservablePrimitive<Guid>(uuid);
            this.link = new ObservablePrimitive<string>(link);
            this.linkType = new ObservablePrimitive<Shared.LinkType>(linkType);
            this.label = new ObservablePrimitive<string>(label);
            this.labelType = new ObservablePrimitive<Shared.LabelType>(labelType);
            this.labelScale = new ObservablePrimitive<float>(labelScale);
            this.labelDimensions = new ObservablePrimitive<Vector2>(labelDimensions);
            this.position = new ObservablePrimitive<Vector3>(position);
            this.rotation = new ObservablePrimitive<Quaternion>(rotation ?? Quaternion.identity);
            this.visible = new ObservablePrimitive<bool>(visible);
            this.exhibitOpen = new ObservablePrimitive<bool>(exhibitOpen);
            this.exhibitPosition = new ObservablePrimitive<Vector3>(exhibitPosition);
            this.exhibitRotation = new ObservablePrimitive<Quaternion>(exhibitRotation ?? Quaternion.identity);
            this.exhibitPanelDimensions = new ObservablePrimitive<Vector2>(exhibitPanelDimensions);
            this.exhibitPanelScrollPosition = new ObservablePrimitive<float>(exhibitPanelScrollPosition);
        }

        protected override void PostInitializeInternal()
        {
            hovered.RegisterDerived(
                _ => hovered.value = hoveredLocally.value || hoveredRemotely.value,
                ObservationScope.Self,
                hoveredLocally,
                hoveredRemotely
            );
        }
    }

    [RequireComponent(typeof(BoxCollider))]
    public abstract class NodeBase : Control<NodeProps>
    {
        private const float scaleInterval = 1.5f;
        private BoxCollider _collider;
        protected GameObject _currentView;
        private Shared.LabelType? _currentViewLinkType;
        private TaskHandle _animateIn = TaskHandle.Complete;

        private void Awake()
        {
            _collider = GetComponent<BoxCollider>();
        }

        protected override void Bind()
        {
            AddBinding(
                props.position.OnChange(x => transform.position = x),
                props.rotation.OnChange(x => transform.rotation = x),
                props.labelType.OnChange(HandleLabelTypeChanged),
                Bindings.Observer(
                    _ =>
                    {
                        _collider.center = new Vector3(0, 0, -0.5f) * props.labelScale.value;
                        _collider.size = new Vector3(
                            props.labelDimensions.value.x,
                            props.labelDimensions.value.y,
                            1f
                        ) * props.labelScale.value;
                    },
                    new ObserverParameters() { scope = ObservationScope.Self },
                    props.labelScale,
                    props.labelDimensions
                ),
                gameObject.BindActive(props.visible)
            );
        }

        private void HandleLabelTypeChanged(Shared.LabelType labelType)
        {
            if (labelType == _currentViewLinkType)
                return;

            bool labelTypeIsText = LabelIsText(labelType);

            if (labelTypeIsText &&
                _currentViewLinkType.HasValue &&
                LabelIsText(_currentViewLinkType.Value))
            {
                _currentViewLinkType = labelType;
                return;
            }

            _currentViewLinkType = labelType;
            _animateIn.Cancel();

            PrefabSystem.Destroy(_currentView);

            if (labelTypeIsText)
            {
                _currentView = SetupTextNode();
            }
            else
            {
                _currentView = SetupImageNode();
            }

            _animateIn = TaskHandle.Execute(token => Interpolation.Run01(
                scaleInterval,
                x => _currentView.transform.localScale = Vector3.one * props.labelScale.value * x,
                token
            ));
        }

        private GameObject SetupTextNode()
        {
            var view = PrefabSystem.Create(PrefabSystem.nodeTextView, transform);

            view.AddBinding(
                props.labelScale.OnChange(x => view.transform.localScale = Vector3.one * x),
                props.labelDimensions.OnChange(x => ((RectTransform)view.transform).sizeDelta = x),
                props.exhibitOpen.DynamicBind(open => open ? SetupExhibit() : null),
                Bindings.DynamicBind(
                    args => TaskHandle.Execute(
                        token => FetchLabel(
                            props.labelType.value,
                            props.label.value,
                            props.linkType.value,
                            props.link.value,
                            token
                        ).ContinueWith(label => view.text.text = label)
                    ).ToDisposable(),
                    ObservationScope.Self,
                    props.label,
                    props.labelType,
                    props.link,
                    props.linkType
                )
            );

            return view.gameObject;
        }

        private GameObject SetupImageNode()
        {
            var view = PrefabSystem.Create(PrefabSystem.nodeImageView, transform);

            view.AddBinding(
                props.labelScale.OnChange(x => view.transform.localScale = Vector3.one * x),
                props.labelDimensions.OnChange(x => view.SetMaxDimensions(x * 100f)),
                props.exhibitOpen.DynamicBind(open => open ? SetupExhibit() : null),
                props.label.DynamicBind(label => ContentManager
                    .LoadTexture(label)
                    .OnComplete(view.SetImage)
                )
            );

            return view.gameObject;
        }

        private bool LabelIsText(Shared.LabelType linkType)
        {
            return
                linkType == Shared.LabelType.Text ||
                linkType == Shared.LabelType.Automatic;
        }

        private async UniTask<string> FetchLabel(
            Shared.LabelType labelType,
            string label,
            Shared.LinkType linkType,
            string link,
            CancellationToken cancellationToken = default)
        {
            string result;

            if (labelType != Shared.LabelType.Automatic)
            {
                result = label;
                cancellationToken.ThrowIfCancellationRequested();
                return result;
            }

            switch (linkType)
            {
                case Shared.LinkType.Annotation:
                    var annotation = await OuternetAPI.GetAnnotation(link);
                    result = annotation != null ? annotation.annotation : "Failed to fetch annotation";
                    break;

                case Shared.LinkType.Address:
                    var address = await OuternetAPI.GetAddressDataByName(link);
                    result = address != null ? address.address_name : "Failed to fetch address";
                    break;

                case Shared.LinkType.None:
                    result = link;
                    break;

                case Shared.LinkType.ImageList:
                    result = GithubAPI.ParseFolderUrl(link).folderName;
                    break;

                default:
                    result = "Link Missing";
                    break;
            }

            cancellationToken.ThrowIfCancellationRequested();
            return result;
        }

        private IDisposable SetupExhibit()
        {
            var exhibit = ClientExhibit.Create(
                position: props.exhibitPosition.value,
                rotation: props.exhibitRotation.value,
                panelDimensions: props.exhibitPanelDimensions.value,
                panelScrollPosition: props.exhibitPanelScrollPosition.value,
                bind: exhibitProps => Bindings.Compose(
                    exhibitProps.position.BindTo(props.exhibitPosition),
                    exhibitProps.rotation.BindTo(props.exhibitRotation),
                    exhibitProps.panelScrollPosition.BindTo(props.exhibitPanelScrollPosition),
                    exhibitProps.panelDimensions.BindTo(props.exhibitPanelDimensions),
                    exhibitProps.interacting.BindTo(props.interacting),
                    exhibitProps.linkType.From(props.linkType),
                    exhibitProps.link.From(props.link),
                    exhibitProps.closeSelected.OnChange(close =>
                    {
                        if (close)
                            props.exhibitOpen.ExecuteSetOrDelay(false);
                    })
                )
            );

            exhibit.Open(props.position.value, props.rotation.value);

            return Bindings.OnRelease(() => exhibit
                .Close(props.position.value, props.rotation.value)
                .ContinueWith(() =>
                {
                    exhibit.Dispose();
                    Destroy(exhibit.gameObject);
                }).Forget()
            );
        }
    }
}