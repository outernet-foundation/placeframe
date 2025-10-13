using UnityEngine;
using Nessle;
using TMPro;

using static Nessle.UIBuilder;
using ObserveThing;
using System;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using Cysharp.Threading.Tasks;

namespace PlerionClient.Client
{
    public static class UIPresets
    {
        public static IControl<LayoutProps> Row(string identifier = "row", LayoutProps props = default, HorizontalLayoutGroup prefab = default, Action<IControl<LayoutProps>> setup = default)
        {
            var control = HorizontalLayout(identifier, props, prefab);
            control.props.childControlWidth.From(true);
            control.props.childControlHeight.From(true);
            control.props.childAlignment.From(TextAnchor.MiddleLeft);
            control.props.spacing.From(10);
            return control;
        }

        public static Control SafeArea()
            => new Control("safeArea", typeof(SafeArea));

        public static Control<InputFieldProps> EditableLabel(string identifier = "editableLabel", InputFieldProps props = default)
        {
            props = props ?? new InputFieldProps();
            var control = Control(identifier, props);
            ValueObservable<bool> inputFieldActive = new ValueObservable<bool>();

            control.Setup(editableLabel =>
            {
                editableLabel.OnPointerClick(x =>
                {
                    var eventSystem = EventSystem.current;
                    var target = x.pointerPress;

                    eventSystem.SetSelectedGameObject(target);

                    UniTask.WaitForSeconds(0.5f).ContinueWith(() =>
                    {
                        if (eventSystem.currentSelectedGameObject == target)
                            inputFieldActive.From(true);
                    }).Forget();
                });

                editableLabel.Children(
                    InputField("inputField", props: control.props).Setup(inputField =>
                    {
                        inputField.FillParent();
                        inputField.Active(inputFieldActive);
                        inputField.Selected(inputFieldActive);
                        inputField.OnDeselect(_ => inputFieldActive.From(false));
                        inputField.props.onEndEdit.From(_ => inputFieldActive.From(false));
                    }),
                    Text("label").Setup(label =>
                    {
                        label.props.text.From(control.props.inputText);
                        label.FillParent();
                        label.Active(inputFieldActive.SelectDynamic(x => !x));
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

        public static IControl<LayoutProps> TightRowsWideColumns(string identifier = "verticalLayout.layout", LayoutProps props = default, VerticalLayoutGroup prefab = default, Action<IControl<LayoutProps>> setup = default)
        {
            return VerticalLayout(identifier, props, prefab).Setup(layout =>
            {
                layout.props.childControlWidth.From(true);
                layout.props.childControlHeight.From(true);
                layout.props.childForceExpandWidth.From(true);
                layout.props.spacing.From(10);
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

        // public class TabProps
        // {
        //     public ValueObservable<string> name { get; } = new ValueObservable<string>();
        //     public ImageProps icon { get; } = DefaultImageProps();
        //     public ImageProps selectedIcon { get; } = DefaultImageProps();
        //     public ValueObservable<IControl> content { get; } = new ValueObservable<IControl>();
        // }

        // public class TabbedMenuProps
        // {
        //     public ValueObservable<int> selectedTab { get; } = new ValueObservable<int>();
        //     public ListObservable<TabProps> tabs { get; } = new ListObservable<TabProps>();
        //     public TextStyleProps defaultLabelStyle { get; } = new TextStyleProps();
        //     public TextStyleProps selectedLabelStyle { get; } = new TextStyleProps();
        //     public ImageStyleProps background { get; } = new ImageStyleProps();
        //     public ImageStyleProps selectedBackground { get; } = new ImageStyleProps();
        // }

        // public static Control<TabbedMenuProps> TabbedMenu(TabbedMenuProps props = default)
        // {
        //     props = props ?? new TabbedMenuProps();
        //     var control = Control("Tabbed Menu", props, typeof(VerticalLayoutGroup));
        //     var layout = control.gameObject.GetComponent<VerticalLayoutGroup>();
        //     layout.childControlHeight = true;
        //     layout.childControlWidth = true;

        //     control.Children(
        //         HorizontalLayout().Style(x =>
        //         {
        //             x.childControlHeight.value = true;
        //             x.childControlWidth.value = true;
        //             x.childForceExpandWidth.value = true;
        //         }).Children(props.tabs.CreateDynamic(tabProps =>
        //         {
        //             var index = props.tabs.IndexOfDynamic(tabProps);

        //             var selected = Observables.Combine(
        //                 index,
        //                 props.selectedTab,
        //                 (index, selected) => index == selected
        //             );

        //             return Button()
        //                 .Background(selected.SelectDynamic(x => x ? props.background : props.selectedBackground))
        //                 .WithMetadata(index)
        //                 .Children(
        //                     Image().Style(selected.SelectDynamic(x => x ? tabProps.icon : tabProps.selectedIcon)),
        //                     Text().Style(selected.SelectDynamic(x => x ? props.defaultLabelStyle : props.selectedLabelStyle)).Value(tabProps.name)
        //                 );

        //         }).OrderByDynamic(x => x.metadata))
        //     );
        // }
    }
}