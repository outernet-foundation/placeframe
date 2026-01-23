using System;
using System.Linq;

using UnityEngine;
using UnityEngine.EventSystems;

using Cysharp.Threading.Tasks;

using FofX.Stateful;
using Plerion.Core;
using FofX;
using System.Collections.Generic;

using Unity.Mathematics;
using System.Threading;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsMap : Control<AuthoringToolsMap.Props>, IPointerClickHandler
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<Guid> sceneObjectID { get; private set; }
            public ObservablePrimitive<string> name { get; private set; }
            public ObservablePrimitive<Vector3> position { get; private set; }
            public ObservablePrimitive<Quaternion> rotation { get; private set; }
            public ObservablePrimitive<Guid> reconstructionID { get; private set; }

            public Props() : base() { }

            public Props(Guid sceneObjectID = default, string name = default, Vector3 position = default, Quaternion? rotation = default, Guid reconstructionID = default)
            {
                this.sceneObjectID = new ObservablePrimitive<Guid>(sceneObjectID);
                this.name = new ObservablePrimitive<string>(name);
                this.position = new ObservablePrimitive<Vector3>(position);
                this.rotation = new ObservablePrimitive<Quaternion>(rotation ?? Quaternion.identity);
                this.reconstructionID = new ObservablePrimitive<Guid>(reconstructionID);
            }
        }

        public LocalizationMap localizationMap;
        private TaskHandle _loadPointsTask = TaskHandle.Complete;

        private void Update()
        {
            if (props.position.value != transform.position)
                props.position.ExecuteSet(transform.position);

            if (props.rotation.value != transform.rotation)
                props.rotation.ExecuteSet(transform.rotation);
        }

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(Guid sceneObjectID = default, string name = default, Vector3 position = default, Quaternion? rotation = default, Guid reconstructionID = default)
            => InitializeAndBind(new Props(sceneObjectID, name, position, rotation, reconstructionID));

        protected override void Bind()
        {
            AddBinding(
                props.position.OnChange(x => transform.position = x),
                props.rotation.OnChange(x => transform.rotation = x),
                props.reconstructionID.OnChange(x =>
                {
                    _loadPointsTask.Cancel();

                    if (x == Guid.Empty)
                        return;

                    _loadPointsTask = TaskHandle.Execute(token => LoadReconstruction(x, token));
                })
            );
        }

        private async UniTask LoadReconstruction(Guid reconstructionID, CancellationToken cancellationToken)
        {
            (var pointPayload, var framePayload) = await UniTask.WhenAll(
                VisualPositioningSystem.GetReconstructionPoints(reconstructionID, cancellationToken),
                VisualPositioningSystem.GetReconstructionFramePoses(reconstructionID, cancellationToken)
            );

            await UniTask.SwitchToMainThread(cancellationToken);

            localizationMap.Load(pointPayload, framePayload);
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            AuthoringToolsApp.SetSelectedObjects(props.sceneObjectID.value);
        }

        public static AuthoringToolsMap Create(
            Guid sceneObjectID = default,
            string name = default,
            Vector3 position = default,
            Quaternion? rotation = default,
            Guid reconstructionID = default,
            Transform parent = default,
            Func<Props, IDisposable> bind = default)
        {
            AuthoringToolsMap instance = Instantiate(AuthoringToolsPrefabs.SceneMap, parent);
            instance.InitializeAndBind(new Props(
                sceneObjectID,
                name,
                position,
                rotation,
                reconstructionID
            ));

            instance.AddBinding(Bindings.OnRelease(() => PrefabSystem.Destroy(instance)));

            if (bind != null)
                instance.AddBinding(bind(instance.props));

            return instance;
        }
    }
}