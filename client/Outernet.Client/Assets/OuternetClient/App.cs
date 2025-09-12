using UnityEngine;
using Outernet.Shared;
using Outernet.Client.Location;
using System;

using FofX.Stateful;
using ObservableCollections;

using R3;
using System.Collections.Generic;

namespace Outernet.Client
{
    public class App : FofX.AppBase<ClientState>
    {
        public static RoomRecord State_Old => ConnectionManager.State;
        public static Guid? ClientID => ConnectionManager.ClientID;
        public static string environmentURL;
        public static string environmentSchema;

        private static bool internetReachable = false;
        public static bool InternetReachable => internetReachable;

        protected override void InitializeState(ClientState state)
            => state.Initialize("root", new ObservableNodeContext(new ChannelLogger() { logGroup = LogGroup.Stateful }));

        private void Start()
        {
            Application.wantsToQuit += WantsToQuit;
            ConnectionManager.HubConnectionRequested.EnqueueSet(true);

            LocalizedReferenceFrame.onTransformMatriciesChanged += () =>
                ExecuteActionOrDelay(new SetEcefToLocalMatrixAction(LocalizedReferenceFrame.EcefToLocalTransform));

#if !AUTHORING_TOOLS_ENABLED
            MapManager.Enable();
            Localizer.Start();

            internetReachable = Application.internetReachability != NetworkReachability.NotReachable;

            if (!internetReachable)
            {
                Toast.ShowToast("No internet connection");
            }

            PropertyBinding(State_Old.settingsAnimateNodeIndicators, state.settings.animateNodeIndicators);
            SetBinding(State_Old.settingsVisibleLayers, state.settings.visibleLayers);

            ConnectionManager.RoomConnectionStatusStream.Subscribe(status =>
            {
                if (State_Old.users.Count == 1 && status == ConnectionManager.RoomConnectionStatus.Connected)
                    state.settings.visibleLayers.ExecuteSetOrDelay(new Guid[] { Guid.Empty });
            });

            ObserveEach(
                State_Old.nodes,
                kvp =>
                {
                    ExecuteAction(AddOrUpdateNodeAction.FromRecord(kvp.Key, kvp.Value));

                    var node = state.nodes[kvp.Key];
                    var transform = state.transforms[kvp.Key];

                    return Bindings.Compose(
                        PropertyBinding(kvp.Value.geoPose.ecefPosition, transform.position, x => x.ToMathematicsDouble3(), x => x.ToDouble3()),
                        PropertyBinding(kvp.Value.geoPose.ecefRotation, transform.rotation),
                        SetBinding(kvp.Value.hoveringUsers, node.hoveringUsers),
                        PropertyBinding(kvp.Value.interactingUser, node.interactingUser),
                        PropertyBinding(kvp.Value.exhibitGeoPose.ecefPosition, node.exhibitPosition, x => x.ToMathematicsDouble3(), x => x.ToDouble3()),
                        PropertyBinding(kvp.Value.exhibitGeoPose.ecefRotation, node.exhibitRotation),
                        PropertyBinding(kvp.Value.exhibitPanelDimensions, node.exhibitPanelDimensions),
                        PropertyBinding(kvp.Value.exhibitPanelScrollPosition, node.exhibitPanelScrollPosition),
                        PropertyBinding(kvp.Value.exhibitOpen, node.exhibitOpen),
                        PropertyBinding(kvp.Value.link, node.link),
                        PropertyBinding(kvp.Value.labelScale, node.labelScale),
                        PropertyBinding(kvp.Value.labelWidth, node.labelWidth),
                        PropertyBinding(kvp.Value.labelHeight, node.labelHeight),
                        PropertyBinding(kvp.Value.layer, node.layer),
                        PropertyBinding(kvp.Value.linkType, node.linkType),
                        PropertyBinding(kvp.Value.label, node.label),
                        PropertyBinding(kvp.Value.labelType, node.labelType),
                        Bindings.OnRelease(() => ExecuteAction(new DestroySceneObjectAction(kvp.Key)))
                    );
                }
            );
#endif
        }

        private IDisposable SetBinding<T, U>(SyncedSet<T> remote, ObservableSet<U> local, Func<T, U> toLocal, Func<U, T> toRemote)
        {
            bool applyingRemote = false;

            return Bindings.Compose(
                remote.ObserveAdd().Subscribe(x =>
                {
                    applyingRemote = true;
                    local.ExecuteAdd(toLocal(x.Value));
                    applyingRemote = false;
                }),
                remote.ObserveRemove().Subscribe(x =>
                {
                    applyingRemote = true;
                    local.ExecuteRemove(toLocal(x.Value));
                    applyingRemote = false;
                }),
                local.Each(x =>
                {
                    if (!applyingRemote)
                        remote.EnqueueAdd(toRemote(x));

                    return Bindings.OnRelease(() =>
                    {
                        if (!applyingRemote)
                            remote.EnqueueRemove(toRemote(x));
                    });
                })
            );
        }

        private IDisposable SetBinding<T>(SyncedSet<T> remote, ObservableSet<T> local)
        {
            bool applyingRemote = false;

            return Bindings.Compose(
                remote.ObserveAdd().Subscribe(x =>
                {
                    applyingRemote = true;
                    local.ExecuteAdd(x.Value);
                    applyingRemote = false;
                }),
                remote.ObserveRemove().Subscribe(x =>
                {
                    applyingRemote = true;
                    local.ExecuteRemove(x.Value);
                    applyingRemote = false;
                }),
                local.Each(x =>
                {
                    if (!applyingRemote)
                        remote.EnqueueAdd(x);

                    return Bindings.OnRelease(() =>
                    {
                        if (!applyingRemote)
                            remote.EnqueueRemove(x);
                    });
                })
            );
        }

        private IDisposable PropertyBinding<T>(SyncedProperty<T> remote, ObservablePrimitive<T> local)
        {
            bool applyingRemote = false;

            return Bindings.Compose(
                remote.Subscribe(x =>
                {
                    applyingRemote = true;
                    local.ExecuteSet(x.Value, logLevel: FofX.LogLevel.Trace);
                    applyingRemote = false;
                }),
                local.OnChange(x =>
                {
                    if (!applyingRemote)
                        remote.EnqueueSet(x);
                })
            );
        }

        private IDisposable PropertyBinding<T, U>(SyncedProperty<T> remote, ObservablePrimitive<U> local, Func<T, U> toLocal, Func<U, T> toRemote)
        {
            bool applyingRemote = false;

            return Bindings.Compose(
                remote.Subscribe(x =>
                {
                    applyingRemote = true;
                    local.ExecuteSet(toLocal(x.Value), logLevel: FofX.LogLevel.Trace);
                    applyingRemote = false;
                }),
                local.OnChange(x =>
                {
                    if (!applyingRemote)
                        remote.EnqueueSet(toRemote(x));
                })
            );
        }

        private IDisposable ObserveEach<TElement>(ObservableCollections.IObservableCollection<TElement> source, Func<TElement, IDisposable> observe)
        {
            Dictionary<TElement, IDisposable> observers = new Dictionary<TElement, IDisposable>();

            foreach (var element in source)
                observers.Add(element, observe(element));

            return Bindings.Compose(
                source.ObserveAdd().Subscribe(addEvent => observers.Add(addEvent.Value, observe(addEvent.Value))),
                source.ObserveRemove().Subscribe(removeEvent =>
                {
                    if (observers.TryGetValue(removeEvent.Value, out var observer))
                    {
                        observer.Dispose();
                        observers.Remove(removeEvent.Value);
                    }
                }),
                Bindings.OnRelease(() =>
                {
                    foreach (var observer in observers.Values)
                        observer.Dispose();
                })
            );
        }

        private void Update()
        {
            ConnectionManager.Update();
            PlaneDetector.Update();
            SceneViewManager.Update();
            Localizer.Update();
            LocalizedReferenceFrame.Update();

            UnityMainThreadDispatcher.Flush();

            var newInternetReachable = Application.internetReachability != NetworkReachability.NotReachable;

            if (newInternetReachable != internetReachable)
            {
                internetReachable = newInternetReachable;

                if (newInternetReachable)
                {
                    Toast.ShowToast("Internet connection restored");
                }
                else
                {
                    Toast.ShowToast("Internet connection lost");
                }
            }
        }

        private void OnApplicationPause(bool pause)
        {
            if (pause)
            {
                Localizer.StopCameraCapture();
            }
            else
            {
                Localizer.StartCameraCapture();
            }
        }

        private bool WantsToQuit()
        {
            ConnectionManager.Terminate(); // BUG, this is async
            SceneViewManager.Terminate();
            MapManager.Terminate();
            Logger.Terminate();

            return true;
        }
    }
}