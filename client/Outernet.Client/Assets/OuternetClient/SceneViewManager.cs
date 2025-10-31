using System;
using System.Collections.Generic;
using ObservableCollections;
using R3;

using UnityEngine;

using FofX.Stateful;

using Outernet.Client.Location;
using System.Linq;
using Plerion.VPS;

namespace Outernet.Client
{
    static public class SceneViewManager
    {
        static private LocalUser localUser;
        static Dictionary<Guid, RemoteUser> remoteUsers = new Dictionary<Guid, RemoteUser>();
        static Dictionary<Guid, ClientNode> _nodes = new Dictionary<Guid, ClientNode>();

        static IDisposable subscriptions;

        static public void Initialize()
        {
            VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated += () =>
                App.ExecuteActionOrDelay(new UpdateNodeLocationsAction(VisualPositioningSystem.UnityFromEcefTransformLeftHanded, _nodes.Values.Select(x => x.props).ToArray()));

            subscriptions = Disposable.Combine(
                App.State_Old.users.ObserveAdd().Subscribe(addEvent =>
                {
                    var userID = addEvent.Value.Key;

                    if (userID == App.ClientID)
                    {
                        localUser = PrefabSystem.Create(PrefabSystem.localUser);
                        localUser.Initialize(userID);
                        return;
                    }

                    var remoteUser = PrefabSystem.Create(PrefabSystem.remoteUser);

                    remoteUser.Initialize(userID);
                    remoteUsers.Add(userID, remoteUser);

                    if (ConnectionManager.RoomConnectionStatusStream.CurrentValue == ConnectionManager.RoomConnectionStatus.Connected)
                    {
                        Toast.ShowToast($"User {addEvent.Value.Value.userName.Value} joined");
                    }
                }),

                App.State_Old.users.ObserveRemove().Subscribe(removeEvent =>
                {
                    var userID = removeEvent.Value.Key;

                    if (userID == App.ClientID)
                    {
                        localUser.Terminate();
                        PrefabSystem.Destroy(localUser);
                        localUser = null;
                        return;
                    }

                    remoteUsers[userID].Terminate();
                    PrefabSystem.Destroy(remoteUsers[userID]);
                    remoteUsers.Remove(userID);

                    Toast.ShowToast($"User {removeEvent.Value.Value.userName.Value} left");
                }),

                App.state.nodes.Each(kvp => SetupNode(kvp.value))
            );
        }

        static private IDisposable SetupNode(NodeState node)
        {
            var transform = App.state.transforms[node.id];
            var localTransform = VisualPositioningSystem.EcefToUnityWorld(transform.position.value, transform.rotation.value);
            var instance = ClientNode.Create(
                uuid: node.id,
                position: localTransform.position,
                rotation: localTransform.rotation,
                bind: props => Bindings.Compose(
                    props.link.From(node.link),
                    props.linkType.From(node.linkType),
                    props.label.From(node.label),
                    props.labelType.From(node.labelType),
                    props.labelScale.From(node.labelScale),
                    props.labelDimensions.Derive(
                        _ => props.labelDimensions.value = new Vector2(
                            node.labelWidth.value,
                            node.labelHeight.value
                        ),
                        ObservationScope.Self,
                        node.labelWidth,
                        node.labelHeight
                    ),
                    props.visible.From(node.visible),
                    props.exhibitOpen.BindTo(node.exhibitOpen),
                    Bindings.BindECEFTransform(node.exhibitPosition, node.exhibitRotation, props.exhibitPosition, props.exhibitRotation),
                    props.exhibitPanelDimensions.BindTo(node.exhibitPanelDimensions),
                    props.exhibitPanelScrollPosition.BindTo(node.exhibitPanelScrollPosition),
                    props.hoveredRemotely.From(
                        x => node.hoveringUsers.count > 1 || (
                            App.ClientID.HasValue &&
                            node.hoveringUsers.count == 1 &&
                            !node.hoveringUsers.Contains(App.ClientID.Value)
                        ),
                        ObservationScope.Self,
                        node.hoveringUsers
                    ),
                    node.hoveringUsers.BindContains(App.ClientID.Value, props.hoveredLocally),
                    props.interacting.BindTo(
                        node.interactingUser,
                        interactingUser => interactingUser == App.ClientID.Value,
                        interactingLocally => interactingLocally ? App.ClientID.Value : node.interactingUser.value
                    ),
                    Bindings.OnRelease(() => _nodes.Remove(node.id))
                )
            );

            _nodes.Add(node.id, instance);
            return instance;
        }

        static public void Terminate()
        {
            foreach (var userView in remoteUsers.Values)
            {
                userView.Terminate();
                PrefabSystem.Destroy(userView);
            }

            subscriptions?.Dispose();
        }

        static public void Update()
        {
            if (localUser != null)
            {
                localUser.RealUpdate();
            }
        }
    }
}