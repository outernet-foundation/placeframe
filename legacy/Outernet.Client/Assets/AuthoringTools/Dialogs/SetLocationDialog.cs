using System;
using FofX.Stateful;
using UnityEngine.UI;
using TMPro;
using Unity.Mathematics;

namespace Outernet.Client.AuthoringTools
{
    public enum DialogStatus
    {
        Pending,
        Complete,
        Canceled
    }

    public class SetLocationDialog : Control<SetLocationDialog.Props>
    {
        public class Props : ObservableObject
        {
            public ObservablePrimitive<DialogStatus> status { get; private set; }
            public ObservablePrimitive<string> locationName { get; private set; }
            public ObservablePrimitive<double> latitude { get; private set; }
            public ObservablePrimitive<double> longitude { get; private set; }
            public ObservablePrimitive<bool> allowCancel { get; private set; }
            public ObservableList<LocationHistoryData> history { get; private set; }

            public Props() : base() { }

            public Props(DialogStatus status = default, string locationName = default, double latitude = default, double longitude = default, bool allowCancel = default, params LocationHistoryData[] history)
            {
                this.status = new ObservablePrimitive<DialogStatus>(status);
                this.locationName = new ObservablePrimitive<string>(locationName);
                this.latitude = new ObservablePrimitive<double>(latitude);
                this.longitude = new ObservablePrimitive<double>(longitude);
                this.allowCancel = new ObservablePrimitive<bool>(allowCancel);
                this.history = new ObservableList<LocationHistoryData>(history);
            }
        }

        public LabelButton locationHistoryElement;
        public TMP_InputField locationNameInputField;
        public TMP_InputField latitudeInputField;
        public TMP_InputField longitudeInputField;
        public Button completeButton;
        public Button cancelButton;
        public Button clearHistoryButton;

        private void Awake()
        {
            completeButton.onClick.AddListener(() => props.ExecuteAction(x =>
            {
                var newHistoryElement = x.history.Add();
                newHistoryElement.name.value = x.locationName.value;
                newHistoryElement.location.value = new double2(x.latitude.value, x.longitude.value);
                x.status.value = DialogStatus.Complete;
            }));

            cancelButton.onClick.AddListener(() => props.status.ExecuteSet(DialogStatus.Canceled));
            clearHistoryButton.onClick.AddListener(() => props.history.ExecuteAction(x => x.Clear()));

            locationHistoryElement.gameObject.SetActive(false);
        }

        public override void Setup()
            => InitializeAndBind(new Props());

        public void Setup(DialogStatus status = default, string locationName = default, double latitude = default, double longitude = default, bool allowCancel = default, params LocationHistoryData[] history)
            => InitializeAndBind(new Props(status, locationName, latitude, longitude, allowCancel, history));

        protected override void Bind()
        {
            AddBinding(
                locationNameInputField.BindInput(props.locationName),
                latitudeInputField.BindInput(props.latitude),
                longitudeInputField.BindInput(props.longitude),
                cancelButton.gameObject.BindActive(props.allowCancel),
                props.history.Each(element =>
                {
                    var view = Instantiate(
                        locationHistoryElement,
                        locationHistoryElement.transform.parent
                    );

                    view.gameObject.SetActive(true);

                    return Bindings.Compose(
                        Bindings.Observer(
                            _ =>
                            {
                                view.label.text = string.IsNullOrEmpty(element.name.value) ?
                                    $"({element.location.value.x}, {element.location.value.y})" :
                                    $"{element.name.value} <color=#808080>({element.location.value.x}, {element.location.value.y})";
                            },
                            ObservationScope.Self,
                            element.name,
                            element.location
                        ),
                        view.button.onClick.OnRaised(() => props.ExecuteAction(x =>
                        {
                            x.latitude.value = element.location.value.x;
                            x.longitude.value = element.location.value.y;
                            x.locationName.value = element.name.value;
                            x.status.value = DialogStatus.Complete;
                        })),
                        Bindings.OnRelease(() => Destroy(view.gameObject))
                    );
                })
            );
        }
    }
}