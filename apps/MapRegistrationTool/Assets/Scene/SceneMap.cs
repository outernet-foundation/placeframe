using System;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using Placeframe.Core;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.MapRegistrationTool
{
    [RequireComponent(typeof(LocalizationMap))]
    public class SceneMap : Control<SceneMap.Props>, IPointerClickHandler
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<Guid> sceneObjectID { get; private set; }
            public ObservablePrimitive<string> name { get; private set; }
            public ObservablePrimitive<Vector3> position { get; private set; }
            public ObservablePrimitive<Quaternion> rotation { get; private set; }

            public Props()
                : base() { }

            public Props(
                Guid sceneObjectID = default,
                string name = default,
                Vector3 position = default,
                Quaternion? rotation = default
            )
            {
                this.sceneObjectID = new ObservablePrimitive<Guid>(sceneObjectID);
                this.name = new ObservablePrimitive<string>(name);
                this.position = new ObservablePrimitive<Vector3>(position);
                this.rotation = new ObservablePrimitive<Quaternion>(rotation ?? Quaternion.identity);
            }
        }

        private LocalizationMap _localizationMapVisualizer;

        private void Awake()
        {
            _localizationMapVisualizer = GetComponent<LocalizationMap>();
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
                props.rotation.OnChange(x => transform.rotation = x)
            );
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
            Guid mapId = default,
            Transform parent = default,
            Func<Props, IDisposable> bind = default
        )
        {
            SceneMap instance = Instantiate(Prefabs.Map, parent);
            instance._localizationMapVisualizer.Initialize(mapId);
            instance.InitializeAndBind(new Props(sceneObjectID, name, position, rotation));

            instance.AddBinding(Bindings.OnRelease(() => Destroy(instance)));

            if (bind != null)
                instance.AddBinding(bind(instance.props));

            return instance;
        }
    }
}
