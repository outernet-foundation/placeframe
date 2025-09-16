using System;
using System.Collections.Generic;
using ObservableCollections;
using R3;

using UnityEngine;

using FofX.Stateful;

using Outernet.Client.Location;
using System.Linq;

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
            LocalizedReferenceFrame.onTransformMatriciesChanged += () =>
                App.ExecuteActionOrDelay(new SetEcefToLocalMatrixAction(LocalizedReferenceFrame.EcefToLocalTransform));

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

                App.state.exhibits.Each(kvp => SetupExhibit(kvp.value))
            );
        }

        static private IDisposable SetupExhibit(ExhibitState exhibit)
        {
            var node = App.state.nodes[exhibit.id];
            var instance = ClientNode.Create(
                uuid: exhibit.id,
                localPosition: node.localPosition.value,
                localRotation: node.localRotation.value,
                bind: props => Bindings.Compose(
                    props.bounds.From(node.localBounds),
                    props.link.From(exhibit.link),
                    props.linkType.From(exhibit.linkType),
                    props.label.From(exhibit.label),
                    props.labelType.From(exhibit.labelType),
                    props.labelScale.From(exhibit.labelScale),
                    props.labelDimensions.Derive(
                        _ => props.labelDimensions.value = new Vector2(
                            exhibit.labelWidth.value,
                            exhibit.labelHeight.value
                        ),
                        ObservationScope.Self,
                        exhibit.labelWidth,
                        exhibit.labelHeight
                    ),
                    props.visible.From(node.visible),
                    props.exhibitOpen.BindTo(exhibit.exhibitOpen),
                    props.exhibitLocalPosition.BindTo(exhibit.exhibitLocalPosition),
                    props.exhibitLocalRotation.BindTo(exhibit.exhibitLocalRotation),
                    props.exhibitPanelDimensions.BindTo(exhibit.exhibitPanelDimensions),
                    props.exhibitPanelScrollPosition.BindTo(exhibit.exhibitPanelScrollPosition),
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
                    Bindings.OnRelease(() => _nodes.Remove(exhibit.id))
                )
            );

            _nodes.Add(exhibit.id, instance);
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