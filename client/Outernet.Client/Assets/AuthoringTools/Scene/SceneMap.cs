using System;

using Outernet.Client.Location;
using Outernet.Shared;

using UnityEngine;
using UnityEngine.EventSystems;

using Cysharp.Threading.Tasks;

using FofX.Stateful;

namespace Outernet.Client.AuthoringTools
{
    [RequireComponent(typeof(MapRenderer))]
    public class SceneMap : Control<SceneMap.Props>, IPointerClickHandler
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<Guid> sceneObjectID { get; private set; }
            public ObservablePrimitive<string> name { get; private set; }
            public ObservablePrimitive<Vector3> localPosition { get; private set; }
            public ObservablePrimitive<Quaternion> localRotation { get; private set; }
            public ObservablePrimitive<Bounds> bounds { get; private set; }
            public ObservablePrimitive<Guid> mapID { get; private set; }
            public ObservablePrimitive<long> color { get; private set; }
            public ObservablePrimitiveArray<Vector3> localInputImagePositions { get; private set; }

            public Props() : base() { }

            public Props(Guid sceneObjectID = default, string name = default, Vector3 localPosition = default, Quaternion? localRotation = default, Bounds bounds = default, Guid mapID = default, long color = default, params Vector3[] localInputImagePositions)
            {
                this.sceneObjectID = new ObservablePrimitive<Guid>(sceneObjectID);
                this.name = new ObservablePrimitive<string>(name);
                this.localPosition = new ObservablePrimitive<Vector3>(localPosition);
                this.localRotation = new ObservablePrimitive<Quaternion>(localRotation ?? Quaternion.identity);
                this.bounds = new ObservablePrimitive<Bounds>(bounds);
                this.mapID = new ObservablePrimitive<Guid>(mapID);
                this.color = new ObservablePrimitive<long>(color);
                this.localInputImagePositions = new ObservablePrimitiveArray<Vector3>(localInputImagePositions);
            }
        }

        private MapRenderer _mapRenderer;

        private void Awake()
        {
            _mapRenderer = GetComponent<MapRenderer>();
        }

        private void Update()
        {
            if (props.localPosition.value != transform.localPosition)
                props.localPosition.ExecuteSet(transform.localPosition);

            if (props.localRotation.value != transform.localRotation)
                props.localRotation.ExecuteSet(transform.localRotation);

            for (int i = 0; i < props.localInputImagePositions.count - 1; i++)
            {
                RuntimeGizmos.DrawLine(
                    transform.TransformPoint(props.localInputImagePositions[i]),
                    transform.TransformPoint(props.localInputImagePositions[i + 1]),
                    0.01f,
                    Color.white
                );
            }
        }

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(Guid sceneObjectID = default, string name = default, Vector3 localPosition = default, Quaternion? localRotation = default, Bounds bounds = default, Guid mapID = default, long color = default, params Vector3[] localInputImagePositions)
            => InitializeAndBind(new Props(sceneObjectID, name, localPosition, localRotation, bounds, mapID, color, localInputImagePositions));

        protected override void Bind()
        {
            AddBinding(
                props.localPosition.OnChange(x => transform.localPosition = x),
                props.localRotation.OnChange(x => transform.localRotation = x),
                props.mapID.OnChange(x =>
                {
                    if (x != Guid.Empty)
                        _mapRenderer.Load(x, props.name.value).Forget();
                }),
                props.color.OnChange(x =>
                {
                    var color = ColorExtensions.ToColor(x);
                    color.a = 1f;
                    _mapRenderer.SetColor(color);
                })
            );
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            AuthoringToolsApp.SetSelectedObjects(props.sceneObjectID.value);
        }
    }
}