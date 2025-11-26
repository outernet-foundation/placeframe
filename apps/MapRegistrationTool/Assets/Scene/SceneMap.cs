using System;
using System.Linq;

using UnityEngine;
using UnityEngine.EventSystems;

using Cysharp.Threading.Tasks;

using FofX.Stateful;
using FofX;
using System.Collections.Generic;

using Unity.Mathematics;

namespace Outernet.MapRegistrationTool
{
    public class SceneMap : Control<SceneMap.Props>, IPointerClickHandler
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

        private static readonly float3x3 basisUnity = float3x3.identity;

        private static readonly float3x3 basisOpenCV = new float3x3(
            1f, 0f, 0f,
            0f, -1f, 0f,
            0f, 0f, 1f
        );

        private static readonly float3x3 basisChangeUnityFromOpenCV = math.mul(math.transpose(basisUnity), basisOpenCV);
        private static readonly float3x3 basisChangeOpenCVFromUnity = math.transpose(basisChangeUnityFromOpenCV);

        // public LocalizationMapRenderer mapRenderer;
        private TaskHandle _loadPointsTask = TaskHandle.Complete;
        private List<Vector3> _localInputPositions = new List<Vector3>();

        private void Update()
        {
            if (props.position.value != transform.position)
                props.position.ExecuteSet(transform.position);

            if (props.rotation.value != transform.rotation)
                props.rotation.ExecuteSet(transform.rotation);

            for (int i = 0; i < _localInputPositions.Count - 1; i++)
            {
                RuntimeGizmos.DrawLine(
                    transform.TransformPoint(_localInputPositions[i]),
                    transform.TransformPoint(_localInputPositions[i + 1]),
                    0.01f,
                    Color.white
                );
            }
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

                    _loadPointsTask = TaskHandle.Execute(async token =>
                    {
                        List<PlerionApiClient.Model.PointCloudPoint> points = default;
                        List<PlerionApiClient.Model.Transform> localInputPositions = default;

                        await UniTask.WhenAll(
                            App.API.GetReconstructionPointsAsync(x, token).AsUniTask().ContinueWith(x => points = x),
                            App.API.GetReconstructionImagePosesAsync(x, token).AsUniTask().ContinueWith(x => localInputPositions = x)
                        );

                        await UniTask.SwitchToMainThread(cancellationToken: token);

                        _localInputPositions.AddRange(localInputPositions.Select(x =>
                        {
                            var unityBasis = ChangeBasisOpenCVToUnity(
                                new float3x3(quaternion.identity),
                                new float3((float)x.Position.X, (float)x.Position.Y, (float)x.Position.Z)
                            );

                            return new Vector3(unityBasis.Item2.x, unityBasis.Item2.y, unityBasis.Item2.z);
                        }));

                        // mapRenderer.Load(points.Select(x =>
                        // {
                        //     var unityBasis = ChangeBasisOpenCVToUnity(new float3x3(quaternion.identity), x.Position.ToFloat3());
                        //     return new Point()
                        //     {
                        //         position = unityBasis.Item2.ToVector3(),
                        //         color = x.Color.ToUnityColor()
                        //     };
                        // }).ToArray());
                    });
                })
            );
        }

        private static (float3x3, float3) ChangeBasisOpenCVToUnity(float3x3 rotation, float3 translation)
            => (math.mul(basisChangeUnityFromOpenCV, math.mul(rotation, basisChangeOpenCVFromUnity)), math.mul(basisChangeUnityFromOpenCV, translation));

        public void OnPointerClick(PointerEventData eventData)
        {
            App.SetSelectedObjects(props.sceneObjectID.value);
        }

        public static SceneMap Create(
            Guid sceneObjectID = default,
            string name = default,
            Vector3 position = default,
            Quaternion? rotation = default,
            Guid reconstructionID = default,
            Transform parent = default,
            Func<Props, IDisposable> bind = default)
        {
            SceneMap instance = Instantiate(Prefabs.Map, parent);
            instance.InitializeAndBind(new Props(
                sceneObjectID,
                name,
                position,
                rotation,
                reconstructionID
            ));

            instance.AddBinding(Bindings.OnRelease(() => Destroy(instance)));

            if (bind != null)
                instance.AddBinding(bind(instance.props));

            return instance;
        }
    }
}