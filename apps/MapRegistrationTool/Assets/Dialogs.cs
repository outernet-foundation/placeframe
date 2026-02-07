using UnityEngine;

using FofX.Stateful;
using System;

namespace Placeframe.MapRegistrationTool
{
    public static class Dialogs
    {
        public class BugReportProps : Dialog.Props
        {
            public ObservablePrimitive<string> reporter { get; private set; }
            public ObservablePrimitive<string> bugDescription { get; private set; }

            public BugReportProps() : base() { }

            public BugReportProps(string reporter = default, string bugDescription = default, string title = default, DialogStatus status = default, bool allowCancel = default)
                : base(title, status, allowCancel)
            {
                this.reporter = new ObservablePrimitive<string>(reporter);
                this.bugDescription = new ObservablePrimitive<string>(bugDescription);
            }
        }

        public static Dialog BugReportDialog(string reporter = default, string bugDescription = default, string title = "Bug Report", DialogStatus status = default, bool allowCancel = true, Func<BugReportProps, IDisposable> binding = null)
        {
            return Show(
                new BugReportProps(reporter, bugDescription, title, status, allowCancel),
                props => UIBuilder.VerticalLayout(
                    UIBuilder.PropertyLabel("Reporter", UIBuilder.InputField(props.reporter)),
                    UIBuilder.Header("Description", UIBuilder.InputRegion(props.bugDescription)),
                    UIBuilder.HorizontalLayout()
                        .Alignment(TextAnchor.MiddleRight)
                        .WithChildren(
                            UIBuilder.Button("Cancel", () => props.status.ExecuteSet(DialogStatus.Canceled)),
                            UIBuilder.Button("Send", () => props.status.ExecuteSet(DialogStatus.Complete))
                        )
                ),
                binding
            );
        }

        public class UnsavedChangesDialogProps : Dialog.Props
        {
            public ObservablePrimitive<string> text { get; private set; }
            public ObservablePrimitive<bool> saveRequested { get; private set; }

            public UnsavedChangesDialogProps() : base() { }
            public UnsavedChangesDialogProps(string text = default, bool saveRequested = default, string title = default, DialogStatus status = default, bool allowCancel = default)
                : base(title, status, allowCancel)
            {
                this.text = new ObservablePrimitive<string>(text);
                this.saveRequested = new ObservablePrimitive<bool>(saveRequested);
            }
        }

        public static Dialog UnsavedChangesDialog(string text = default, bool saveRequested = default, string title = default, DialogStatus status = default, bool allowCancel = default, Func<UnsavedChangesDialogProps, IDisposable> binding = null)
        {
            return Show(
                new UnsavedChangesDialogProps(text, saveRequested, title, status, allowCancel),
                constructControls: props =>
                {
                    var cancelButton = UIBuilder.Button("Cancel", () => props.status.ExecuteSet(DialogStatus.Canceled));
                    cancelButton.AddBinding(cancelButton.gameObject.BindActive(props.allowCancel));

                    return UIBuilder.VerticalLayout()
                        .Spacing(15)
                        .WithChildren(
                            UIBuilder.Text(props.text),
                            UIBuilder.HorizontalLayout()
                                .Alignment(TextAnchor.LowerRight)
                                .WithChildren(
                                    UIBuilder.Button("Save", () => props.ExecuteAction(x =>
                                    {
                                        x.status.value = DialogStatus.Complete;
                                        x.saveRequested.value = true;
                                    })),
                                    UIBuilder.Button("Don't Save", () => props.status.ExecuteSet(DialogStatus.Complete)),
                                    cancelButton
                                )
                        );
                },
                binding
            );
        }

        public static Dialog Show(string title = default, DialogStatus status = default, bool allowCancel = true, float minimumWidth = 500, Func<Dialog.Props, Component> constructControls = null, Func<Dialog.Props, IDisposable> binding = null)
            => Show(new Dialog.Props(title, status, allowCancel, minimumWidth), constructControls, binding);

        public static Dialog Show<T>(T props, Func<T, Component> constructControls = null, Func<T, IDisposable> binding = null)
            where T : Dialog.Props
        {
            var view = UnityEngine.Object.Instantiate(Prefabs.Dialog);
            view.Setup(props);

            if (constructControls != null)
            {
                var controls = constructControls(props);
                controls.transform.SetParent(view.content, false);
            }

            if (binding != null)
                view.AddBinding(binding(props));

            view.AddBinding(
                props.status.OnChange(x =>
                {
                    if (x == DialogStatus.Complete || x == DialogStatus.Canceled)
                        UnityEngine.Object.Destroy(view.gameObject);
                }),
                view.gameObject.DestroyOnRelease()
            );

            Utility.DisplayDialog(view);

            return view;
        }
    }
}
