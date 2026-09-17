using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Placeframe.Core;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Placeframe.MapRegistrationTool
{
    [RequireComponent(typeof(LocalizationMapVisualizer))]
    public class SceneMap : Control<SceneMap.Props>, IPointerClickHandler
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<Guid> sceneObjectID { get; private set; }
            public ObservablePrimitive<string> name { get; private set; }
            public ObservablePrimitive<Vector3> position { get; private set; }
            public ObservablePrimitive<Quaternion> rotation { get; private set; }
            public ObservablePrimitive<Guid> reconstructionId { get; private set; }

            public Props()
                : base() { }

            public Props(
                Guid sceneObjectID = default,
                string name = default,
                Vector3 position = default,
                Quaternion? rotation = default,
                Guid reconstructionId = default
            )
            {
                this.sceneObjectID = new ObservablePrimitive<Guid>(sceneObjectID);
                this.name = new ObservablePrimitive<string>(name);
                this.position = new ObservablePrimitive<Vector3>(position);
                this.rotation = new ObservablePrimitive<Quaternion>(rotation ?? Quaternion.identity);
                this.reconstructionId = new ObservablePrimitive<Guid>(reconstructionId);
            }
        }

        private LocalizationMapVisualizer _localizationMapVisualizer;
        private CancellationTokenSource _loadReconstructionTokenSource;

        private void Awake()
        {
            _localizationMapVisualizer = GetComponent<LocalizationMapVisualizer>();
        }

        private void Update()
        {
            if (props.position.value != transform.position)
                props.position.ExecuteSet(transform.position);

            if (props.rotation.value != transform.rotation)
                props.rotation.ExecuteSet(transform.rotation);
        }

        public override void Setup() => InitializeAndBind(new Props());

        public void Setup(
            Guid sceneObjectID = default,
            string name = default,
            Vector3 position = default,
            Quaternion? rotation = default
        ) => InitializeAndBind(new Props(sceneObjectID, name, position, rotation));

        protected override void Bind()
        {
            AddBinding(
                props.position.OnChange(x => transform.position = x),
                props.rotation.OnChange(x => transform.rotation = x),
                props.reconstructionId.OnChange(x => LoadReconstruction(x))
            );
        }

        private void LoadReconstruction(Guid reconstructionID)
        {
            _loadReconstructionTokenSource?.Cancel();
            _loadReconstructionTokenSource?.Dispose();
            _loadReconstructionTokenSource = new CancellationTokenSource();

            if (reconstructionID != Guid.Empty)
                LoadReconstructionAndPopulate(reconstructionID, _loadReconstructionTokenSource.Token).Forget();
        }

        private async UniTask LoadReconstructionAndPopulate(Guid reconstructionID, CancellationToken cancellationToken = default)
        {
            (var pointPayload, var framePayload) = await UniTask.WhenAll(
                VisualPositioningSystem.GetReconstructionPoints(reconstructionID),
                VisualPositioningSystem.GetReconstructionFramePoses(reconstructionID)
            );

            await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);

            _localizationMapVisualizer.Load(pointPayload, framePayload);
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            App.SetSelectedObjects(props.sceneObjectID.value);
        }

        public static SceneMap Create(
            Guid sceneObjectID = default,
            string name = default,
            Vector3 position = default,
            Quaternion? rotation = default,
            Guid reconstructionId = default,
            Transform parent = default,
            Func<Props, IDisposable> bind = default
        )
        {
            SceneMap instance = Instantiate(Prefabs.Map, parent);
            instance.InitializeAndBind(new Props(sceneObjectID, name, position, rotation, reconstructionId));

            instance.AddBinding(Bindings.OnRelease(() => Destroy(instance.gameObject)));

            if (bind != null)
                instance.AddBinding(bind(instance.props));

            return instance;
        }
    }
}
