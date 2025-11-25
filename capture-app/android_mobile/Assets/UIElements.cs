using UnityEngine;
using Nessle;

using static Nessle.UIBuilder;
using ObserveThing;
using System;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using Cysharp.Threading.Tasks;
using TMPro;

namespace PlerionClient.Client
{
    public static partial class UIElements
    {
        public static UIElementSet elements;

        public static IControl<LayoutProps> Row(string identifier = "row", LayoutProps props = default, HorizontalLayoutGroup prefab = default, Action<IControl<LayoutProps>> setup = default)
        {
            var control = HorizontalLayout(identifier, props, prefab);
            control.props.childControlWidth.From(true);
            control.props.childControlHeight.From(true);
            control.props.childAlignment.From(TextAnchor.MiddleLeft);
            control.props.spacing.From(10);
            return control;
        }

        public static Control SafeArea(string identifier = "safeArea")
            => new Control(identifier, typeof(SafeArea));

        public class EditableLabelProps : IDisposable
        {
            public InputFieldProps inputField { get; } = new InputFieldProps();
            public TextProps label { get; } = new TextProps();
            public ValueObservable<bool> inputFieldActive { get; } = new ValueObservable<bool>();

            public void Dispose()
            {
                inputField.Dispose();
                label.Dispose();
            }
        }

        public static Control<EditableLabelProps> EditableLabel(string identifier = "editableLabel", EditableLabelProps props = default)
        {
            props = props ?? new EditableLabelProps();
            var control = Control(identifier, props);

            control.Setup(editableLabel =>
            {
                editableLabel.OnPointerClick(x =>
                {
                    var eventSystem = EventSystem.current;
                    var target = x.pointerPress;

                    eventSystem.SetSelectedGameObject(target);

                    UniTask.WaitForSeconds(0.5f).ContinueWith(() =>
                    {
                        if (eventSystem.currentSelectedGameObject != target)
                            return;

                        props.inputFieldActive.From(true);
                    }).Forget();
                });

                editableLabel.Children(
                    InputField("inputField", props: control.props.inputField).Setup(inputField =>
                    {
                        inputField.FillParent();
                        inputField.Active(control.props.inputFieldActive);
                        inputField.Selected(control.props.inputFieldActive);
                        inputField.OnDeselect(_ => control.props.inputFieldActive.From(false));
                        inputField.props.onEndEdit.From(input => control.props.inputFieldActive.From(false));
                    }),
                    Text("label", props: control.props.label).Setup(label =>
                    {
                        label.FillParent();
                        label.Active(control.props.inputFieldActive.SelectDynamic(x => !x));
                        label.props.text.From(
                            Observables.Combine(
                                control.props.inputField.inputText.text,
                                control.props.inputField.placeholderText.text,
                                (input, placeholder) => string.IsNullOrEmpty(input) ? placeholder : input
                            )
                        );
                    })
                );
            });

            return control;
        }

        public static T OnChanged<T>(this T control, Action<float> onChange)
            where T : IControl<FloatFieldProps>
        {
            control.AddBinding(control.props.value.Subscribe(x => onChange(x.currentValue)));
            return control;
        }

        public static IControl PropertyLabel(string indentifer, IControl<TextProps> label, IControl control)
        {
            control.FlexibleWidth(true);

            return HorizontalLayout(indentifer).Setup(propertyLabel =>
            {
                propertyLabel.props.childScaleHeight.From(true);
                propertyLabel.props.childControlWidth.From(true);
                propertyLabel.props.childForceExpandHeight.From(true);
                propertyLabel.props.spacing.From(10);
                propertyLabel.Children(label, control);
            });
        }

        public static IControl<TextProps> Title(string identifier = "title", TextProps props = default, TextMeshProUGUI prefab = default)
        {
            return Text(identifier, props, prefab).Setup(text =>
            {
                text.props.style.horizontalAlignment.From(HorizontalAlignmentOptions.Center);
                text.props.style.verticalAlignment.From(VerticalAlignmentOptions.Capline);
                text.props.style.fontSize.From(48);
            });
        }

        public static IControl<LayoutProps> TightRowsWideColumns(string identifier = "verticalLayout.layout", LayoutProps props = default, VerticalLayoutGroup prefab = default)
        {
            return VerticalLayout(identifier, props, prefab).Setup(layout =>
            {
                layout.props.childControlWidth.From(true);
                layout.props.childControlHeight.From(true);
                layout.props.childForceExpandWidth.From(true);
                layout.props.spacing.From(30);
            });
        }

        public class Vector3Props
        {
            public ValueObservable<Vector3> value { get; } = new ValueObservable<Vector3>();

            public TextProps xLabel { get; } = new TextProps();
            public FloatFieldProps xField { get; } = new FloatFieldProps();

            public TextProps yLabel { get; } = new TextProps();
            public FloatFieldProps yField { get; } = new FloatFieldProps();

            public TextProps zLabel { get; } = new TextProps();
            public FloatFieldProps zField { get; } = new FloatFieldProps();
        }

        public static Control<Vector3Props> Vector3(string identifier = "vector3", Vector3Props props = default)
        {
            return Control(identifier, props ?? new Vector3Props(), typeof(HorizontalLayoutGroup)).Setup(vector3 =>
            {
                vector3.PreferredHeight(30);

                vector3.AddBinding(vector3.props.value.Subscribe(x =>
                {
                    vector3.props.xField.value.From(x.currentValue.x);
                    vector3.props.yField.value.From(x.currentValue.y);
                    vector3.props.zField.value.From(x.currentValue.z);
                }));

                vector3.Columns(
                    10,
                    PropertyLabel(
                        "xLabel",
                        Text("text", vector3.props.xLabel).Setup(x => x.props.text.From("X")),
                        FloatField("field", vector3.props.xField)
                            .OnChanged(x => vector3.props.value.From(new Vector3(x, vector3.props.value.value.y, vector3.props.value.value.z)))
                    ),
                    PropertyLabel(
                        "yLabel",
                        Text("text", vector3.props.yLabel).Setup(x => x.props.text.From("Y")),
                        FloatField("field", vector3.props.yField)
                            .OnChanged(x => vector3.props.value.From(new Vector3(vector3.props.value.value.x, x, vector3.props.value.value.z)))
                    ),
                    PropertyLabel(
                        "zLabel",
                        Text("text", vector3.props.zLabel).Setup(x => x.props.text.From("Z")),
                        FloatField("field", vector3.props.zField)
                            .OnChanged(x => vector3.props.value.From(new Vector3(vector3.props.value.value.x, vector3.props.value.value.y, x)))
                    )
                );
            });
        }

        public static IControl LabeledControl(IValueObservable<string> label, float labelWidth, IControl control)
        {
            return HorizontalLayout().Setup(layout =>
            {
                layout.props.childAlignment.From(TextAnchor.MiddleLeft);
                layout.props.childControlWidth.From(true);
                layout.props.childControlHeight.From(true);
                layout.Children(
                    Text().Setup(labelObj =>
                    {
                        labelObj.props.text.From(label);
                        labelObj.PreferredWidth(labelWidth);
                        labelObj.MinWidth(labelWidth);
                    }),
                    control.Setup(control => control.FlexibleWidth(true))
                );
            });
        }

        public static IControl LabeledControl(string label, float labelWidth, IControl control)
        {
            return HorizontalLayout("labeledControl").Setup(layout =>
            {
                layout.props.childAlignment.From(TextAnchor.MiddleLeft);
                layout.props.childControlWidth.From(true);
                layout.props.childControlHeight.From(true);
                layout.Children(
                    Text().Setup(labelObj =>
                    {
                        labelObj.props.style.verticalAlignment.From(TMPro.VerticalAlignmentOptions.Capline);
                        labelObj.props.text.From(label);
                        labelObj.PreferredWidth(labelWidth);
                        labelObj.MinWidth(labelWidth);
                    }),
                    control.Setup(control => control.FlexibleWidth(true))
                );
            });
        }

        public static IControl<LayoutProps> AdaptiveLabel(IControl label, IControl content)
        {
            return VerticalLayout().Setup(root =>
            {
                root.props.childControlWidth.From(true);
                root.props.childControlHeight.From(true);
                IControl narrowContentRegion = HorizontalLayout("narrowContent").Setup(narrowContentRegion =>
                {
                    narrowContentRegion.props.childControlWidth.From(true);
                    narrowContentRegion.props.childControlHeight.From(true);
                    narrowContentRegion.FlexibleWidth(true);
                    narrowContentRegion.FlexibleHeight(true);
                });

                IControl wideContentRegion = VerticalLayout("wideContent").Setup(wideContentRegion =>
                {
                    wideContentRegion.FlexibleWidth(true);
                    wideContentRegion.props.childControlWidth.From(true);
                    wideContentRegion.props.childControlHeight.From(true);
                });

                var contentIsWide = Observables.Combine(
                    content.rect, narrowContentRegion.rect,
                    (_, region) =>
                    {
                        var tooWide = LayoutUtility.GetPreferredWidth(content.transform) > region.width;
                        var tooTall = LayoutUtility.GetPreferredHeight(content.transform) > region.height;
                        return tooWide || tooTall;
                    }
                );

                wideContentRegion.Active(contentIsWide);
                narrowContentRegion.Active(contentIsWide.SelectDynamic(x => !x));
                content.parent.From(contentIsWide.SelectDynamic(x => x ? wideContentRegion : narrowContentRegion));

                root.Children(
                    Row().Setup(topRow => topRow.Children(label, narrowContentRegion)),
                    wideContentRegion
                );

                content.FillParent();
            });
        }

        public class ColumnsProps : IDisposable
        {
            public ValueObservable<float> spacing { get; } = new ValueObservable<float>();

            public void Dispose()
            {
                spacing.Dispose();
            }
        }

        public static IControl<ColumnsProps> Columns()
        {
            return Control("columns", new ColumnsProps()).Setup(columns =>
            {
                columns.AddBinding(
                    Observables.Any(columns.children, columns.props.spacing).Subscribe(_ =>
                    {
                        float step = 1f / columns.children.count;

                        for (int i = 0; i < columns.children.count; i++)
                        {
                            var child = columns.children[i];
                            child.transform.anchorMin = new Vector2(step * i, 0);
                            child.transform.anchorMax = new Vector2(step * (i + 1), 1);

                            child.transform.offsetMin = new Vector2(Mathf.Lerp(0f, columns.props.spacing.value, i * step), 0);
                            child.transform.offsetMax = new Vector2(Mathf.Lerp(-columns.props.spacing.value, 0f, (i + 1) * step), 0);
                        }
                    })
                );
            });
        }
    }
}