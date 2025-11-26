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

using TMPro;

namespace Outernet.MapRegistrationTool
{
    public class MapRegistrationToolUI : MonoBehaviour
    {
        public GameObject noLocationSetBlock;
        public Button addScanButton;
        public Transform scansList;
        public LabelToggle tilesetToggleTemplate;
        public SetLocationDialog setLocationDialogPrefab;
        public RectTransform inspectorContent;

        private IDisposable _inspectorBinding = Bindings.Empty();

        private Dictionary<Guid, Transform> _viewByID = new Dictionary<Guid, Transform>();
        private Dictionary<Transform, Guid> _idByView = new Dictionary<Transform, Guid>();

        private Guid _lastSelectedElement;

        private void Awake()
        {
            App.state.location.OnChange(x => noLocationSetBlock.SetActive(!x.HasValue));

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
                "Edit/Delete",
                () =>
                {
                    UndoRedoManager.RegisterUndo("Delete");
                    App.ExecuteAction(App.state.selectedObjects.Select(
                        x => new DestroySceneObjectAction(x)).ToArray()
                    );
                },
                validate: () =>
                    App.state.selectedObjects.count > 0,
                commandKeys: new Key[][]{
                    new Key[] { Key.Delete },
                    new Key[] { Key.Backspace }
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

            App.state.settings.loaded.OnChange(loaded =>
            {
                if (!loaded)
                    return;

                if (!App.state.settings.restoreLocationAutomatically.value ||
                    App.state.settings.lastLocation.value == null)
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
            App.state.maps.Each(x => SetupMapView(x.value));

            Bindings.Observer(
                _ =>
                {
                    _inspectorBinding.Dispose();
                    _inspectorBinding = App.state.selectedObjects.count == 1 ?
                        BindInspector(App.state.selectedObjects.First()) : Bindings.Empty();
                },
                ObservationScope.Self,
                App.state.selectedObjects
            );

            var scanListEventTrigger = scansList.gameObject.AddComponent<EventTrigger>();
            scanListEventTrigger.AddListener(
                EventTriggerType.PointerClick,
                _ => App.SetSelectedObjects()
            );

            App.state.selectedObjects.Observe(
                _ =>
                {
                    if (!App.state.selectedObjects.Contains(_lastSelectedElement))
                        _lastSelectedElement = Guid.Empty;
                }
            );
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
                    Prefabs.SelectedColor
                ),
                view.gameObject.DestroyOnRelease()
            );

            view.transform.SetParent(scansList, false);

            return view;
        }

        private void OpenSetLocationDialog(bool allowCancel)
        {
            var dialog = Instantiate(setLocationDialogPrefab);

            dialog.Setup(
                latitude: App.state.location.value?.x ?? 0,
                longitude: App.state.location.value?.y ?? 0,
                allowCancel: allowCancel
            );

            dialog.AddBinding(
                dialog.props.history.BindTo(App.state.settings.locationHistory),
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

        private IDisposable BindInspector(Guid sceneObjectID)
        {
            var binding = new Bindings.CompositeDisposable();

            foreach (var componentDict in App.state.componentDictionaries.Where(x => !x.HasAttribute<HideInInspectorUIAttribute>()))
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

        private IDisposable BindHierarchyElement(Guid id, GameObject viewRoot, Image toHighlight, Color highlightColor)
        {
            var binding = new Bindings.CompositeDisposable();
            Color defaultColor = toHighlight.color;

            binding.Add(App.state.selectedObjects.Observe(
                _ => toHighlight.color = App.state.selectedObjects.Contains(id) ?
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
                        if (App.state.selectedObjects.Contains(id))
                        {
                            App.RemoveSelectedObject(id);
                        }
                        else
                        {
                            App.AddSelectedObject(id);
                            _lastSelectedElement = id;
                        }

                        return;
                    }

                    App.SetSelectedObjects(id);
                    _lastSelectedElement = id;
                }
            ));

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

        private void SelectBetween(Transform element1, Transform element2)
        {
            if (element1 == element2)
            {
                App.SetSelectedObjects(_idByView[element1]);
                return;
            }

            Transform lastElement = null;
            List<Transform> selected = new List<Transform>();

            foreach (var visibleElement in EnumerateChildren(scansList))
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

            App.SetSelectedObjects(selected
                .Select(x => _idByView[x])
                .ToArray()
            );
        }

        private IEnumerable<Transform> EnumerateChildren(Transform transform)
        {
            for (int i = 0; i < transform.childCount; i++)
                yield return transform.GetChild(i);
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
            var newMapTransform = LocationUtilities.UnityWorldToEcef(
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

            if (exsistingMap != Guid.Empty || App.state.maps.Any(x => x.value.reconstructionID.value == reconstruction.Id))
                throw new Exception("Localization map already registered.");

            App.ExecuteActionOrDelay(new AddOrUpdateMapAction(
                Guid.NewGuid(),
                scanName,
                newMapTransform.position,
                newMapTransform.rotation,
                Lighting.Day,
                reconstruction.Id
            ));
        }

        private void OpenUserSettings()
        {
            Dialogs.Show(
                title: "Settings",
                constructControls: props => UIBuilder.VerticalLayout(
                    UIBuilder.AdaptivePropertyLabel("Content Radius", UIBuilder.FloatField(App.state.settings.nodeFetchRadius)),
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