using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using UnityEngine.InputSystem;

using Cysharp.Threading.Tasks;

using FofX;
using FofX.Stateful;

using Placeframe.Core;
using TMPro;

namespace Outernet.Client.AuthoringTools
{
    public class AuthoringToolsUI : MonoBehaviour
    {
        public GameObject noLocationSetBlock;
        public Button addScanButton;
        public Button addNodeButton;
        public ScrollRect nodesScrollView;
        public Transform scansList;
        public LabelToggle tilesetToggleTemplate;
        public SetLocationDialog setLocationDialogPrefab;
        public AddScanDialog addScanDialogPrefab;
        public LoadingBarDialog loadDialogPrefab;
        public RectTransform inspectorContent;
        public GameObject nodeListRoot;
        public Transform carryIndicator;
        public TextMeshProUGUI carryIndicatorText;
        public TMP_Dropdown layersDropdown;

        private IDisposable _inspectorBinding = Bindings.Empty();
        private TaskHandle _uploadScan = TaskHandle.Complete;

        private Dictionary<Guid, Transform> _viewByID = new Dictionary<Guid, Transform>();
        private Dictionary<Transform, Guid> _idByView = new Dictionary<Transform, Guid>();

        private Dictionary<Guid, Foldout> _groupFoldouts = new Dictionary<Guid, Foldout>();

        private Guid _lastSelectedElement;

        private void Awake()
        {
            App.state.authoringTools.location.OnChange(x => noLocationSetBlock.SetActive(!x.HasValue));

            SystemMenu.AddMenuItem(
                "File/Set Location",
                () => OpenSetLocationDialog(allowCancel: true)
            );

            SystemMenu.AddMenuItem(
                "File/Quit",
                Application.Quit,
                priority: int.MaxValue
            );

            SystemMenu.AddMenuItem(
                "File/Settings",
                OpenUserSettings
            );

            // Restore when we have scan upload functionality in place
            // systemMenu.AddMenuItem(
            //     "File/Add Scan",
            //     OpenAddScanDialog
            // );

            SystemMenu.AddMenuItem(
                "Edit/Duplicate",
                () =>
                {
                    UndoRedoManager.RegisterUndo("Duplicate");
                    App.ExecuteAction(App.state.authoringTools.selectedObjects.Select(
                        x => new DuplicateSceneObjectAction(x)).ToArray()
                    );
                },
                validate: () =>
                    App.state.authoringTools.selectedObjects.count > 0 &&
                    App.state.authoringTools.selectedObjects.All(x =>
                        App.state.nodes.ContainsKey(x) ||
                        App.state.authoringTools.nodeGroups.ContainsKey(x)
                    ),
                commandKeys: new Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    Key.D
                }
            );

            SystemMenu.AddMenuItem(
                "Edit/Delete",
                () =>
                {
                    UndoRedoManager.RegisterUndo("Delete");
                    App.ExecuteAction(App.state.authoringTools.selectedObjects.Select(
                        x => new DestroySceneObjectAction(x)).ToArray()
                    );
                },
                validate: () =>
                    App.state.authoringTools.selectedObjects.count > 0,
                commandKeys: new Key[][]{
                    new Key[] { Key.Delete },
                    new Key[] { Key.Backspace }
                }
            );

            SystemMenu.AddMenuItem(
                "Create/Node",
                CreateNewNode,
                commandKeys: new Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    Key.N
                }
            );

            SystemMenu.AddMenuItem(
                "Create/Group",
                CreateNewNodeGroup,
                commandKeys: new Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    Key.G
                }
            );

            SystemMenu.AddMenuItem(
                "Create/Map",
                OpenAddScanDialog,
                commandKeys: new Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    Key.M
                }
            );

            SystemMenu.AddMenuItem(
                "Help/About",
                OpenAboutWindow
            );

            SystemMenu.AddMenuItem(
                "Help/Report a Bug",
                OpenBugReportWindow
            );

            // Restore when we have scan upload functionality in place
            addScanButton.onClick.AddListener(OpenAddScanDialog);
            addNodeButton.onClick.AddListener(CreateNewNode);

            App.state.authoringTools.settings.loaded.OnChange(loaded =>
            {
                if (!loaded)
                    return;

                if (!App.state.authoringTools.settings.restoreLocationAutomatically.value ||
                    App.state.authoringTools.settings.lastLocation.value == null)
                {
                    OpenSetLocationDialog(allowCancel: false);
                }
            });

            foreach (var tileset in SceneReferences.Tilesets)
            {
                var instance = Instantiate(tilesetToggleTemplate, tilesetToggleTemplate.transform.parent);
                instance.label.text = tileset.name;
                instance.toggle.onValueChanged.AddListener(isOn => tileset.reference.SetActive(isOn));
                instance.toggle.isOn = tileset.reference.activeSelf;
            }

            tilesetToggleTemplate.gameObject.SetActive(false);
            carryIndicator.gameObject.SetActive(false);

            App.state.authoringTools.nodeGroups.Each(x => SetupGroupView(x.value));
            App.state.nodes.Each(x => SetupNodeView(x.value));
            App.state.authoringTools.maps.Each(x => SetupMapView(x.value));

            Bindings.Observer(
                _ =>
                {
                    _inspectorBinding.Dispose();
                    _inspectorBinding = App.state.authoringTools.selectedObjects.count == 1 ?
                        BindInspector(App.state.authoringTools.selectedObjects.First()) : Bindings.Empty();
                },
                ObservationScope.Self,
                App.state.authoringTools.selectedObjects
            );

            var nodesListEventTrigger = nodeListRoot.AddComponent<EventTrigger>();
            nodesListEventTrigger.AddListener(
                EventTriggerType.PointerClick,
                _ => AuthoringToolsApp.SetSelectedObjects()
            );

            var dropReceiver = nodeListRoot.AddComponent<DropReceiver>();
            dropReceiver.onDrop = _ => SetParentGroup(App.state.authoringTools.selectedObjects, null);

            App.state.authoringTools.selectedObjects.Observe(
                _ =>
                {
                    if (!App.state.authoringTools.selectedObjects.Contains(_lastSelectedElement))
                        _lastSelectedElement = Guid.Empty;

                    RevealSelectedObjects();
                }
            );

            layersDropdown.BindLayersDropdown(App.state.layers, App.state.settings.visibleLayers);
        }

        private void Update()
        {
            if (carryIndicator.gameObject.activeSelf)
            {
                carryIndicator.position = Mouse.current.position.value;

                if (!Mouse.current.leftButton.isPressed)
                    carryIndicator.gameObject.SetActive(false);
            }
        }

        private IDisposable SetupGroupView(NodeGroupState nodeGroup)
        {
            var view = UIBuilder.Foldout(nodeGroup.name)
                .WithDropReceiver(onDrop: _ =>
                {
                    SetParentGroup(
                        App.state.authoringTools.selectedObjects.Where(x => x != nodeGroup.id),
                        nodeGroup.id
                    );

                    RevealSelectedObjects();
                });

            foreach (var child in nodeGroup.childObjects)
            {
                if (_viewByID.TryGetValue(child, out var childView))
                    childView.SetParent(view.content, false);
            }

            _viewByID.Add(nodeGroup.id, view.transform);
            _idByView.Add(view.transform, nodeGroup.id);
            _groupFoldouts.Add(nodeGroup.id, view);

            var toHighlight = view.header.AddComponent<Image>();
            toHighlight.color = Color.clear;

            view.AddBinding(
                BindHierarchyElement(
                    nodeGroup.id,
                    view.gameObject,
                    toHighlight,
                    AuthoringToolsPrefabs.SelectedColor,
                    true
                ),
                nodeGroup.parentID.OnChange(x =>
                {
                    view.transform.SetParent(
                        x.HasValue &&
                        _groupFoldouts.TryGetValue(x.Value, out var parent) ?
                            parent.content : nodesScrollView.content,
                        false
                    );

                    if (App.state.authoringTools.selectedObjects.Contains(nodeGroup.id))
                        RevealSelectedObjects();
                }),
                nodeGroup.visible.OnChange(x => view.label.color = x ? Color.white : Color.grey),
                Bindings.OnRelease(() =>
                {
                    _viewByID.Remove(nodeGroup.id);
                    _idByView.Remove(view.transform);
                    _groupFoldouts.Remove(nodeGroup.id);
                    Destroy(view.gameObject);
                })
            );

            return view;
        }

        private IDisposable SetupNodeView(NodeState node)
        {
            var text = UIBuilder.Text(node.name);
            var view = UIBuilder.VerticalLayout(text);
            view.component.padding.left = 10;
            view.component.padding.top = 3;
            view.component.padding.bottom = 3;

            _viewByID.Add(node.id, view.transform);
            _idByView.Add(view.transform, node.id);

            var toHighlight = view.gameObject.AddComponent<Image>();
            toHighlight.color = Color.clear;

            view.AddBinding(
                BindHierarchyElement(
                    node.id,
                    view.gameObject,
                    toHighlight,
                    AuthoringToolsPrefabs.SelectedColor,
                    true
                ),
                node.parentID.OnChange(x =>
                {
                    view.transform.SetParent(
                        x.HasValue &&
                        _groupFoldouts.TryGetValue(x.Value, out var parent) ?
                            parent.content : nodesScrollView.content,
                        false
                    );

                    if (App.state.authoringTools.selectedObjects.Contains(node.id))
                        RevealSelectedObjects();
                }),
                node.visible.OnChange(x => text.component.color = x ? Color.white : Color.grey),
                Bindings.OnRelease(() =>
                {
                    _viewByID.Remove(node.id);
                    _idByView.Remove(view.transform);
                    Destroy(view.gameObject);
                })
            );

            return view;
        }

        private IDisposable SetupMapView(MapState mapState)
        {
            var view = UIBuilder.VerticalLayout(UIBuilder.Text(mapState.name));
            view.component.padding.left = 10;
            view.component.padding.top = 3;
            view.component.padding.bottom = 3;

            var toHighlight = view.gameObject.AddComponent<Image>();
            toHighlight.color = Color.clear;

            view.AddBinding(
                BindHierarchyElement(
                    mapState.uuid,
                    view.gameObject,
                    toHighlight,
                    AuthoringToolsPrefabs.SelectedColor,
                    false
                ),
                view.gameObject.DestroyOnRelease()
            );

            view.transform.SetParent(scansList, false);

            return view;
        }

        private bool CanReparent(Guid guid)
            => App.state.nodes.ContainsKey(guid) || App.state.authoringTools.nodeGroups.ContainsKey(guid);

        private void SetParentGroup(IEnumerable<Guid> toSet, Guid? newGroup)
        {
            UndoRedoManager.RegisterUndo("Reparent");
            App.ExecuteActionOrDelay(toSet
                .Where(CanReparent)
                .Select(x => new SetParentGroupAction(x, newGroup))
                .ToArray()
            );
        }

        private void RevealSelectedObjects()
        {
            foreach (var selectedObject in App.state.authoringTools.selectedObjects)
                RevealInHierarchy(selectedObject);

            LayoutRebuilder.ForceRebuildLayoutImmediate((RectTransform)nodesScrollView.transform);

            float viewportHeight = nodesScrollView.viewport.rect.height;
            float contentHeight = nodesScrollView.content.rect.height;

            if (contentHeight <= viewportHeight)
            {
                nodesScrollView.verticalNormalizedPosition = 0;
                return;
            }

            Transform topmostElement = null;
            Vector3 contentPosition = Vector3.zero;

            foreach (var selectedObject in App.state.authoringTools.selectedObjects)
            {
                if (!_viewByID.TryGetValue(selectedObject, out var transform))
                    continue;

                var localizedPosition = nodesScrollView.content.InverseTransformPoint(transform.position);

                if (topmostElement == null || contentPosition.y < localizedPosition.y)
                {
                    topmostElement = transform;
                    contentPosition = localizedPosition;
                }
            }

            if (topmostElement == null)
                return;

            if (nodesScrollView.viewport.rect.Contains(nodesScrollView.viewport.InverseTransformPoint(topmostElement.position)))
                return;

            float targetY = contentPosition.y + ((RectTransform)topmostElement).rect.yMax - nodesScrollView.content.rect.yMin;
            nodesScrollView.verticalNormalizedPosition = Mathf.Clamp01((targetY - viewportHeight) / (contentHeight - viewportHeight));
        }

        private void RevealInHierarchy(Guid obj)
        {
            if (App.state.authoringTools.TryGetParent(obj, out var parentID) &&
                _groupFoldouts.TryGetValue(parentID, out var foldout))
            {
                foldout.foldout.isOn = true;
                RevealInHierarchy(parentID);
            }
        }

        private void HandleCarryStarted()
        {
            carryIndicator.gameObject.SetActive(true);
            carryIndicatorText.text = string.Join(
                ", ",
                App.state.authoringTools.selectedObjects
                    .Where(CanReparent)
                    .Select(x => App.state.authoringTools.TryGetName(x, out var name) ? name.value : null)
            );
        }

        private void OpenSetLocationDialog(bool allowCancel)
        {
            var dialog = Instantiate(setLocationDialogPrefab);

            dialog.Setup(
                latitude: App.state.authoringTools.location.value?.x ?? 0,
                longitude: App.state.authoringTools.location.value?.y ?? 0,
                allowCancel: allowCancel
            );

            dialog.AddBinding(
                dialog.props.history.BindTo(App.state.authoringTools.settings.locationHistory),
                dialog.props.status.OnChange(x =>
                {
                    if (x == DialogStatus.Pending)
                        return;

                    if (x == DialogStatus.Complete)
                    {
                        App.ExecuteActionOrDelay(
                            new SetLocationAction(new Unity.Mathematics.double2(
                                dialog.props.latitude.value,
                                dialog.props.longitude.value
                            ))
                        );
                    }

                    Destroy(dialog.gameObject);
                })
            );

            Utility.DisplayDialog(dialog);
        }

        private void CreateNewNode()
        {
            UndoRedoManager.RegisterUndo("Create Node");

            var newNodeTransform = VisualPositioningSystem.UnityWorldToEcef(
                Camera.main.transform.position + (Camera.main.transform.forward * 3f),
                Camera.main.transform.rotation.Flatten()
            );

            App.ExecuteAction(new AddOrUpdateNodeAction(
                id: Guid.NewGuid(),
                name: "Node",
                position: newNodeTransform.position,
                rotation: newNodeTransform.rotation,
                link: "Label",
                linkType: Shared.LinkType.None,
                labelScale: 0.1f,
                labelWidth: 20,
                labelHeight: 10
            ));
        }

        private void CreateNewNodeGroup()
        {
            UndoRedoManager.RegisterUndo("Create Group");
            App.ExecuteAction(new AddOrUpdateNodeGroupAction(
                id: Guid.NewGuid(),
                name: "Group",
                children: App.state.authoringTools.selectedObjects.ToArray()
            ));
        }

        private IDisposable BindInspector(Guid sceneObjectID)
        {
            var binding = new Bindings.CompositeDisposable();

            foreach (var componentDict in App.state.authoringTools.componentDictionaries.Where(x => !x.HasAttribute<HideInInspectorUIAttribute>()))
            {
                if (componentDict.TryGetValue(sceneObjectID, out var component))
                {
                    var inspector = UIBuilder.NodeInspector(component.GetType().Name, component, LabelType.None);
                    inspector.transform.SetParent(inspectorContent, false);
                    binding.Add(inspector);
                    binding.Add(inspector.gameObject.DestroyOnRelease());
                }
            }

            return binding;
        }

        private IDisposable BindHierarchyElement(Guid id, GameObject viewRoot, Image toHighlight, Color highlightColor, bool enableCarry)
        {
            var binding = new Bindings.CompositeDisposable();
            Color defaultColor = toHighlight.color;

            binding.Add(App.state.authoringTools.selectedObjects.Observe(
                _ => toHighlight.color = App.state.authoringTools.selectedObjects.Contains(id) ?
                    highlightColor : defaultColor
            ));

            binding.Add(BindEventTrigger(
                viewRoot,
                EventTriggerType.PointerClick,
                _ =>
                {
                    if (Keyboard.current.shiftKey.isPressed &&
                        _lastSelectedElement != Guid.Empty)
                    {
                        SelectBetween(
                            _viewByID[_lastSelectedElement],
                            _viewByID[id]
                        );

                        return;
                    }

                    if (Keyboard.current.ctrlKey.isPressed)
                    {
                        if (App.state.authoringTools.selectedObjects.Contains(id))
                        {
                            AuthoringToolsApp.RemoveSelectedObject(id);
                        }
                        else
                        {
                            AuthoringToolsApp.AddSelectedObject(id);
                            _lastSelectedElement = id;
                        }

                        return;
                    }

                    AuthoringToolsApp.SetSelectedObjects(id);
                    _lastSelectedElement = id;
                }
            ));

            if (enableCarry)
            {
                binding.Add(BindEventTrigger(
                   viewRoot,
                   EventTriggerType.BeginDrag,
                   _ =>
                   {
                       if (Keyboard.current.shiftKey.isPressed)
                       {
                           AuthoringToolsApp.AddSelectedObject(id);
                       }
                       else if (!App.state.authoringTools.selectedObjects.Contains(id))
                       {
                           AuthoringToolsApp.SetSelectedObjects(id);
                           _lastSelectedElement = id;
                       }

                       HandleCarryStarted();
                   }
                ));
            }

            return binding;
        }

        private IDisposable BindEventTrigger(GameObject view, EventTriggerType triggerType, UnityEngine.Events.UnityAction<BaseEventData> listener)
        {
            var eventTrigger = view.GetOrAddComponent<EventTrigger>();
            eventTrigger.AddListener(triggerType, listener);
            return Bindings.OnRelease(() =>
            {
                if (eventTrigger == null)
                    return;

                eventTrigger.RemoveListener(triggerType, listener);
            });
        }

        private IEnumerable<Transform> VisibleHierarchyElements()
            => VisibleChildren(nodesScrollView.content);

        private IEnumerable<Transform> EnumerateChildren(Transform transform)
        {
            for (int i = 0; i < transform.childCount; i++)
                yield return transform.GetChild(i);
        }

        private IEnumerable<Transform> VisibleChildren(Transform transform)
        {
            foreach (var child in EnumerateChildren(transform))
            {
                yield return child;

                if (_idByView.TryGetValue(child, out var id) &&
                    App.state.authoringTools.nodeGroups.TryGetValue(id, out var group) &&
                    _groupFoldouts.TryGetValue(group.id, out var foldout) &&
                    foldout.foldout.isOn)
                {
                    foreach (var nestedChild in VisibleChildren(foldout.content))
                        yield return nestedChild;
                }
            }
        }

        private void SelectBetween(Transform element1, Transform element2)
        {
            if (element1 == element2)
            {
                AuthoringToolsApp.SetSelectedObjects(_idByView[element1]);
                return;
            }

            Transform lastElement = null;
            List<Transform> selected = new List<Transform>();

            foreach (var visibleElement in VisibleHierarchyElements())
            {
                if (lastElement == null)
                {
                    if (visibleElement == element1)
                    {
                        selected.Add(element1);
                        lastElement = element2;
                    }

                    if (visibleElement == element2)
                    {
                        selected.Add(element2);
                        lastElement = element1;
                    }

                    continue;
                }

                selected.Add(visibleElement);

                if (visibleElement == lastElement)
                    break;
            }

            AuthoringToolsApp.SetSelectedObjects(selected
                .Select(x => _idByView[x])
                .ToArray()
            );
        }

        private class AddScanDialogProps : Dialog.Props
        {
            public ObservablePrimitive<string> scanName { get; private set; }
            public ObservablePrimitive<string> error { get; private set; }

            public AddScanDialogProps(string scanName = default, string title = default, DialogStatus status = default, bool allowCancel = default, float minimumWidth = 500f)
                : base(title, status, allowCancel, minimumWidth)
            {
                this.scanName = new ObservablePrimitive<string>(scanName);
            }
        }

        private void OpenAddScanDialog()
        {
            Dialogs.Show(
                props: new AddScanDialogProps(title: "Add Scan", allowCancel: true),
                constructControls: props => UIBuilder.VerticalLayout(
                    UIBuilder.AdaptivePropertyLabel("Scan Name", UIBuilder.InputField(props.scanName)),
                    UIBuilder.Text(props.error).Color(Color.red).WithBinding(x => Bindings.Observer(
                        _ => x.gameObject.SetActive(!string.IsNullOrEmpty(props.error.value)),
                        ObservationScope.Self,
                        props.error
                    )),
                    UIBuilder.HorizontalLayout()
                        .Alignment(TextAnchor.LowerRight)
                        .WithChildren(
                            UIBuilder.Button("Cancel", () => props.status.ExecuteSet(DialogStatus.Canceled)),
                            UIBuilder.Button("Add Scan", async () =>
                            {
                                try
                                {
                                    await ImportScan(props.scanName.value);
                                    props.status.ScheduleSet(DialogStatus.Complete);
                                }
                                catch (Exception exc)
                                {
                                    props.error.ScheduleSet(exc.Message);
                                }
                            })
                            .WithBinding(x => Bindings.Observer(
                                _ => x.button.interactable = props.scanName.value != null,
                                ObservationScope.Self,
                                props.scanName
                            ))
                        )
                )
            );
        }

        public async UniTask ImportScan(string scanName)
        {
            var newMapTransform = VisualPositioningSystem.UnityWorldToEcef(
                Camera.main.transform.position + (Camera.main.transform.forward * 3f),
                Camera.main.transform.rotation.Flatten()
            );

            var reconstructions = await App.API.GetReconstructionsAsync(captureSessionName: scanName);

            if (reconstructions.Count == 0)
            {
                Debug.LogError($"{scanName} not found.");
                return;
            }

            var reconstruction = reconstructions[0];
            Guid exsistingMap = Guid.Empty;

            try
            {
                exsistingMap = await App.API.GetReconstructionLocalizationMapAsync(reconstruction.Id);
            }
            catch (System.Exception) { }

            if (exsistingMap != Guid.Empty || App.state.authoringTools.maps.Any(x => x.value.reconstructionID.value == reconstruction.Id))
                throw new Exception("Localization map already registered.");

            App.ExecuteActionOrDelay(new AddOrUpdateMapAction(
                Guid.NewGuid(),
                scanName,
                newMapTransform.position,
                newMapTransform.rotation,
                null,
                reconstruction.Id
            ));
        }

        private void OpenUserSettings()
        {
            Dialogs.Show(
                title: "Settings",
                constructControls: props => UIBuilder.VerticalLayout(
                    UIBuilder.AdaptivePropertyLabel("Content Radius", UIBuilder.FloatField(App.state.authoringTools.settings.nodeFetchRadius)),
                    UIBuilder.HorizontalLayout(
                        UIBuilder.Text("Layers"),
                        UIBuilder.FlexibleSpace(flexibleWidth: true),
                        UIBuilder.Button("Add", () => App.state.layers.ExecuteAction(
                            Guid.NewGuid(),
                            (key, layers) =>
                            {
                                var layer = layers.Add(key);
                                layer.layerName.value = "New Layer";
                            }
                        ))
                    ),
                    UIBuilder.ScrollRect()
                        .WithLayoutProperties(minHeight: 250)
                        .WithChildren(
                            UIBuilder.VerticalLayout()
                                .Padding(new RectOffset(5, 5, 0, 0))
                                .Spacing(5)
                                .WithBinding(scrollRect => App.state.layers.List(
                                    scrollRect.component.transform,
                                    kvp =>
                                    {
                                        if (kvp.key == Guid.Empty)
                                        {
                                            return UIBuilder.HorizontalLayout()
                                                .Spacing(15)
                                                .WithChildren(
                                                    UIBuilder.Text(kvp.value.layerName)
                                                        .Color(Color.grey)
                                                        .WithLayoutProperties(flexibleWidth: true),
                                                    UIBuilder.Button("Remove", interactable: false)
                                                );
                                        }

                                        return UIBuilder.HorizontalLayout()
                                            .Spacing(15)
                                            .WithChildren(
                                                UIBuilder.EditableLabel(kvp.value.layerName)
                                                    .WithLayoutProperties(flexibleWidth: true),
                                                UIBuilder.Button("Remove", () => App.ExecuteAction(new RemoveLayerAction(kvp.key)))
                                            );
                                    }
                                ))
                        ),
                    UIBuilder.HorizontalLayout()
                        .Alignment(TextAnchor.LowerRight)
                        .WithChildren(
                            UIBuilder.Button("Close", () => props.status.ExecuteSet(DialogStatus.Complete))
                        )
                )
            );
        }

        private void OpenBugReportWindow()
        {
            Dialogs.BugReportDialog(
                allowCancel: true,
                binding: props => props.status.OnChange(x =>
                {
                    if (x == DialogStatus.Complete)
                        Log.Info(LogGroup.BugReports, $"Reporter: {props.reporter.value}\nDescription: {props.bugDescription.value}");
                })
            );
        }

        private void OpenAboutWindow()
        {
            Dialogs.Show(
                title: "About",
                allowCancel: true,
                constructControls: props => UIBuilder.VerticalLayout(
                    UIBuilder.PropertyLabel("Channel", UIBuilder.Text("Beta", VerticalAlignmentOptions.Middle, HorizontalAlignmentOptions.Right)),
                    UIBuilder.PropertyLabel("Version", UIBuilder.Text(Application.version, VerticalAlignmentOptions.Middle, HorizontalAlignmentOptions.Right))
                )
            );
        }
    }
}