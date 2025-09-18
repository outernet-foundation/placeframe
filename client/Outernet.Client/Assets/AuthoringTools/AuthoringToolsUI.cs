using System;
using System.Collections.Generic;
using System.Threading;
using System.Linq;

using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using UnityEngine.InputSystem;

using Cysharp.Threading.Tasks;

using FofX;
using FofX.Stateful;

using Outernet.Client.Location;

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

        private Dictionary<Guid, Foldout> _viewByID = new Dictionary<Guid, Foldout>();
        private Dictionary<Foldout, Guid> _idByView = new Dictionary<Foldout, Guid>();
        private Dictionary<Transform, Guid> _idByTransform = new Dictionary<Transform, Guid>();

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
                    App.state.authoringTools.selectedObjects.All(x => App.state.nodes.ContainsKey(x)),
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
                    App.state.authoringTools.selectedObjects.count > 0 &&
                    App.state.authoringTools.selectedObjects.All(CanReparent),
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
                "Create/Anchor",
                CreateNewAnchor,
                commandKeys: new Key[]
                {
                    Utility.GetPlatformCommandKey(),
                    Key.G
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
            // addScanButton.onClick.AddListener(OpenAddScanDialog);

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

        private IDisposable SetupNodeView(NodeState node)
        {
            var view = UIBuilder.Foldout(node.name)
                .WithDropReceiver(onDrop: _ =>
                {
                    SetParentGroup(
                        App.state.authoringTools.selectedObjects.Where(x => x != node.id),
                        node.id
                    );

                    RevealSelectedObjects();
                });

            foreach (var child in node.childNodes)
            {
                if (_viewByID.TryGetValue(child, out var childView))
                    childView.transform.SetParent(view.content, false);
            }

            _viewByID.Add(node.id, view);
            _idByView.Add(view, node.id);
            _idByTransform.Add(view.transform, node.id);

            var toHighlight = view.header.AddComponent<Image>();
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
                        _viewByID.TryGetValue(x.Value, out var parent) ?
                            parent.content : nodesScrollView.content,
                        false
                    );

                    if (App.state.authoringTools.selectedObjects.Contains(node.id))
                        RevealSelectedObjects();
                }),
                node.visible.OnChange(x => view.label.color = x ? Color.white : Color.grey),
                Bindings.OnRelease(() =>
                {
                    _viewByID.Remove(node.id);
                    _idByView.Remove(view);
                    _idByTransform.Remove(view.transform);
                    Destroy(view.gameObject);
                })
            );

            return view;
        }

        private IDisposable SetupMapView(MapState map)
        {
            var node = App.state.nodes[map.id];

            var view = UIBuilder.VerticalLayout(UIBuilder.Text(node.name));
            view.component.padding.left = 10;
            view.component.padding.top = 3;
            view.component.padding.bottom = 3;

            var toHighlight = view.gameObject.AddComponent<Image>();
            toHighlight.color = Color.clear;

            view.AddBinding(
                BindHierarchyElement(
                    map.id,
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
            => App.state.nodes.ContainsKey(guid);

        private void SetParentGroup(IEnumerable<Guid> toSet, Guid? newGroup)
        {
            UndoRedoManager.RegisterUndo("Reparent");
            App.ExecuteActionOrDelay(toSet
                .Where(CanReparent)
                .Select(x => new SetParentIDAction(x, newGroup))
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
                if (!_viewByID.TryGetValue(selectedObject, out var view))
                    continue;

                var localizedPosition = nodesScrollView.content.InverseTransformPoint(view.transform.position);

                if (topmostElement == null || contentPosition.y < localizedPosition.y)
                {
                    topmostElement = view.transform;
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
            if (App.state.nodes.TryGetValue(obj, out var nodeState) &&
                nodeState.parentID.value.HasValue &&
                _viewByID.TryGetValue(nodeState.parentID.value.Value, out var view))
            {
                view.foldout.isOn = true;
                RevealInHierarchy(nodeState.parentID.value.Value);
            }
        }

        private void HandleCarryStarted()
        {
            carryIndicator.gameObject.SetActive(true);
            carryIndicatorText.text = string.Join(
                ", ",
                App.state.authoringTools.selectedObjects
                    .Where(CanReparent)
                    .Select(x => App.state.nodes[x].name.value)
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

        private void OpenAddScanDialog()
        {
            var dialog = Instantiate(addScanDialogPrefab);
            dialog.Setup();
            dialog.onCanceled.AddListener(() => Destroy(dialog.gameObject));
            dialog.onComplete.AddListener((mapName, mapPath) =>
            {
                Destroy(dialog.gameObject);

                var loadDialog = Instantiate(loadDialogPrefab);
                loadDialog.Setup(allowCancel: true);

                loadDialog.onFinishSelected.AddListener(() => Destroy(loadDialog.gameObject));
                loadDialog.onCancelSelected.AddListener(() => _uploadScan.Cancel());

                var progress = Progress.Create<(string description, float progress)>(
                    progressUpdate => loadDialog.props.ScheduleAction(
                        progressUpdate,
                        (args, props) =>
                        {
                            props.description.value = args.description;
                            props.progress.value = args.progress;
                            props.isDone.value = args.progress == 1f;
                        }
                    )
                );

                _uploadScan = TaskHandle.Execute(
                    async _ =>
                    {
                        await UploadScan(mapName, mapPath, progress);
                        await UniTask.SwitchToMainThread();
                        Destroy(loadDialog.gameObject);
                    }
                );

                Utility.DisplayDialog(loadDialog);
            });

            Utility.DisplayDialog(dialog);
        }

        private async UniTask UploadScan(string scanName, string scanPath, IProgress<(string description, float progress)> progress, CancellationToken token = default)
        {
            progress.Report(new("Converting file", 0.1f));

            // TODO: actually process file here
            await UniTask.Delay(UnityEngine.Random.Range(100, 500));
            token.ThrowIfCancellationRequested();

            progress.Report(new("Uploading file", 0.3f));

            // TODO: actually upload here
            await UniTask.Delay(UnityEngine.Random.Range(500, 1300));
            token.ThrowIfCancellationRequested();

            progress.Report(new("Processing file", 0.7f));

            // TODO: actually await map here
            await UniTask.Delay(UnityEngine.Random.Range(800, 1500));
            token.ThrowIfCancellationRequested();

            progress.Report(new("Done!", 1f));
        }

        private void CreateNewNode()
        {
            UndoRedoManager.RegisterUndo("Create Node");

            App.ExecuteAction(new AddOrUpdateExhibitAction(
                id: Guid.NewGuid(),
                name: "Node",
                localPosition: Camera.main.transform.position + (Camera.main.transform.forward * 3f),
                localRotation: Camera.main.transform.rotation.Flatten(),
                link: "Label",
                linkType: Shared.LinkType.None,
                labelScale: 0.1f,
                labelWidth: 20,
                labelHeight: 10
            ));
        }

        private void CreateNewAnchor()
        {
            UndoRedoManager.RegisterUndo("Create Anchor");

            App.ExecuteAction(new AddOrUpdateNodeAction(
                id: Guid.NewGuid(),
                name: "Anchor",
                localPosition: Camera.main.transform.position + (Camera.main.transform.forward * 3f),
                localRotation: Camera.main.transform.rotation.Flatten()
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

            if (App.state.authoringTools.maps.TryGetValue(sceneObjectID, out var map))
            {
                var inspector = UIBuilder.NodeInspector(map.GetType().Name, map, LabelType.None);
                inspector.transform.SetParent(inspectorContent, false);
                binding.Add(inspector);
                binding.Add(inspector.gameObject.DestroyOnRelease());
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
                            _viewByID[_lastSelectedElement].transform,
                            _viewByID[id].transform
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

                if (_idByTransform.TryGetValue(child, out var id) &&
                    _viewByID.TryGetValue(id, out var view) &&
                    view.foldout.isOn)
                {
                    foreach (var nestedChild in VisibleChildren(view.content))
                        yield return nestedChild;
                }
            }
        }

        private void SelectBetween(Transform element1, Transform element2)
        {
            if (element1 == element2)
            {
                AuthoringToolsApp.SetSelectedObjects(_idByTransform[element1]);
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
                .Select(x => _idByTransform[x])
                .ToArray()
            );
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