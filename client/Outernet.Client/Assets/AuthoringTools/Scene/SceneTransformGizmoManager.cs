using System;
using System.Collections.Generic;
using System.Linq;

using UnityEngine;
using UnityEngine.InputSystem;

using Outernet.Client.Location;
using FofX.Stateful;
using Plerion.Core;

namespace Outernet.Client.AuthoringTools
{
    public class SceneTransformGizmoManager : Control<SceneTransformGizmoManager.Props>
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<TransformToolMode> mode { get; private set; }
            public ObservablePrimitive<Vector3> position { get; private set; }
            public ObservablePrimitive<Quaternion> rotation { get; private set; }
            public ObservablePrimitive<int> selectedHandle { get; private set; }
        }

        public enum TransformToolMode
        {
            Translate,
            Rotate
        }

        private IDisposable _controlBinding = Bindings.Empty();
        private bool _settingPropsTransform = false;

        private void Awake()
        {
            SystemMenu.AddMenuItem(
                "Edit/Translate Tool",
                () => props.ExecuteAction(x =>
                {
                    x.mode.value = TransformToolMode.Translate;
                    x.selectedHandle.value = 0;
                }),
                commandKeys: new Key[] { Key.W }
            );

            SystemMenu.AddMenuItem(
                "Edit/Rotate Tool",
                () => props.ExecuteAction(x =>
                {
                    x.mode.value = TransformToolMode.Rotate;
                    x.selectedHandle.value = 0;
                }),
                commandKeys: new Key[] { Key.E }
            );

            Setup();
        }

        private void LateUpdate()
        {
            Vector3 position = Vector3.zero;
            Quaternion rotation = Quaternion.identity;

            if (App.state.authoringTools.HasSelectedTransforms())
                Utility.CalcSelectedGroupTransform(out position, out rotation);

            if (props.position.value != position || props.rotation.value != rotation)
            {
                _settingPropsTransform = true;
                props.ExecuteAction(
                    (position, rotation),
                    (values, x) =>
                    {
                        x.position.value = values.position;
                        x.rotation.value = values.rotation;
                    },
                    FofX.LogLevel.None
                );
                _settingPropsTransform = false;
            }
        }

        public override void Setup()
            => InitializeAndBind(new Props());

        protected override void Bind()
        {
            AddBinding(
                Bindings.Observer(
                    args =>
                    {
                        _controlBinding.Dispose();

                        if (!App.state.authoringTools.HasSelectedTransforms())
                            return;

                        if (props.mode.value == TransformToolMode.Rotate)
                            _controlBinding = SetupRotateTool();

                        if (props.mode.value == TransformToolMode.Translate)
                            _controlBinding = SetupTranslateTool();
                    },
                    ObservationScope.Self,
                    props.mode,
                    App.state.authoringTools.selectedObjects
                ),
                Bindings.Observer(
                    args =>
                    {
                        if (_settingPropsTransform || !App.state.authoringTools.HasSelectedTransforms())
                            return;

                        var prevRotation = GetPreviousValue(props.rotation, args.changes);

                        var prevMatrix = Matrix4x4.TRS(
                            GetPreviousValue(props.position, args.changes),
                            prevRotation,
                            Vector3.one
                        );

                        var curMatrix = Matrix4x4.TRS(
                            props.position.value,
                            props.rotation.value,
                            Vector3.one
                        );

                        App.ExecuteActionOrDelay(
                            logLevel: FofX.LogLevel.Trace,
                            App.state.authoringTools.SelectedTransforms().Select(transform =>
                            {
                                var objTransform = VisualPositioningSystem.EcefToUnityWorld(
                                    transform.position.value,
                                    transform.rotation.value
                                );

                                objTransform.position = prevMatrix.inverse.MultiplyPoint(objTransform.position);
                                objTransform.rotation = Quaternion.Inverse(prevRotation) * objTransform.rotation;

                                objTransform.position = curMatrix.MultiplyPoint(objTransform.position);
                                objTransform.rotation = props.rotation.value * objTransform.rotation;

                                var ecefTransform = VisualPositioningSystem.UnityWorldToEcef(objTransform.position, objTransform.rotation);

                                return new SetSceneObjectTransformAction(transform.id, ecefTransform.position, ecefTransform.rotation);
                            }
                        ).ToArray());
                    },
                    ObservationScope.All,
                    props.rotation,
                    props.position
                )
            );
        }

        private T GetPreviousValue<T>(ObservablePrimitive<T> primitive, IEnumerable<NodeChangeData> changes)
        {
            if (changes == null)
                return primitive.value;

            T result = primitive.value;

            foreach (var change in changes)
            {
                if (change.source == primitive && change.changeType == ChangeType.Set)
                {
                    result = (T)change.previousValue;
                    break;
                }
            }

            return result;
        }

        private IDisposable SetupTranslateTool()
        {
            return Bindings.Compose(
                RuntimeHandles.SliderHandle(
                    length: 1.333f,
                    direction: Vector3.right,
                    color: Color.red,
                    binding: handleProps => Bindings.Compose(
                        handleProps.position.BindTo(props.position),
                        handleProps.rotation.From(props.rotation),
                        BindGroupedHandle(handleProps, 1)
                    )
                ),
                RuntimeHandles.SliderHandle(
                    length: 1.333f,
                    direction: Vector3.up,
                    color: Color.green,
                    binding: handleProps => Bindings.Compose(
                        handleProps.position.BindTo(props.position),
                        handleProps.rotation.From(props.rotation),
                        BindGroupedHandle(handleProps, 2)
                    )
                ),
                RuntimeHandles.SliderHandle(
                    length: 1.333f,
                    direction: Vector3.forward,
                    color: Color.blue,
                    binding: handleProps => Bindings.Compose(
                        handleProps.position.BindTo(props.position),
                        handleProps.rotation.From(props.rotation),
                        BindGroupedHandle(handleProps, 3)
                    )
                ),
                RuntimeHandles.PlaneHandle(
                    rect: new Rect(Vector2.zero, Vector2.one * 0.33325f),
                    color: Color.red,
                    binding: handleProps => Bindings.Compose(
                        handleProps.position.BindTo(props.position),
                        handleProps.rotation.From(props.rotation, x => x * Quaternion.AngleAxis(-90f, Vector3.up)),
                        BindGroupedHandle(handleProps, 4)
                    )
                ),
                RuntimeHandles.PlaneHandle(
                    rect: new Rect(Vector2.zero, Vector2.one * 0.33325f),
                    color: Color.green,
                    binding: handleProps => Bindings.Compose(
                        handleProps.position.BindTo(props.position),
                        handleProps.rotation.From(props.rotation, x => x * Quaternion.AngleAxis(90f, Vector3.right)),
                        BindGroupedHandle(handleProps, 5)
                    )
                ),
                RuntimeHandles.PlaneHandle(
                    rect: new Rect(Vector2.zero, Vector2.one * 0.33325f),
                    color: Color.blue,
                    binding: handleProps => Bindings.Compose(
                        handleProps.position.BindTo(props.position),
                        handleProps.rotation.From(props.rotation),
                        BindGroupedHandle(handleProps, 6)
                    )
                )
            );
        }

        private IDisposable SetupRotateTool()
        {
            return Bindings.Compose(
                RuntimeHandles.RotateHandle(
                    radius: 1.333f,
                    normal: Vector3.right,
                    color: Color.red,
                    binding: handleProps => Bindings.Compose(
                        handleProps.rotation.BindTo(props.rotation),
                        handleProps.position.From(props.position),
                        BindGroupedHandle(handleProps, 1)
                    )
                ),
                RuntimeHandles.RotateHandle(
                    radius: 1.333f,
                    normal: Vector3.up,
                    color: Color.green,
                    binding: handleProps => Bindings.Compose(
                        handleProps.rotation.BindTo(props.rotation),
                        handleProps.position.From(props.position),
                        BindGroupedHandle(handleProps, 2)
                    )
                ),
                RuntimeHandles.RotateHandle(
                    radius: 1.333f,
                    normal: Vector3.forward,
                    color: Color.blue,
                    binding: handleProps => Bindings.Compose(
                        handleProps.rotation.BindTo(props.rotation),
                        handleProps.position.From(props.position),
                        BindGroupedHandle(handleProps, 3)
                    )
                )
            );
        }

        private IDisposable BindGroupedHandle(RuntimeHandleProps handleProps, int id)
        {
            return Bindings.Compose(
                handleProps.disabled.From(props.selectedHandle, x => x != 0 && x != id),
                handleProps.isPressed.OnChange(handlePressed =>
                {
                    if (handlePressed)
                    {
                        props.selectedHandle.ExecuteSetOrDelay(id);
                        return;
                    }

                    if (props.selectedHandle.value == id)
                        props.selectedHandle.ExecuteSetOrDelay(0);
                })
            );
        }
    }
}