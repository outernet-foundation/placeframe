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
        public static IControl<LayoutProps> Row(string identifier = "row", LayoutProps props = default, HorizontalLayoutGroup prefab = default)
        {
            var control = HorizontalLayout(identifier, props, prefab);
            control.props.childControlWidth.value = true;
            control.props.childControlHeight.value = true;
            control.props.childAlignment.value = TextAnchor.MiddleLeft;
            control.props.spacing.value = 10;
            return control;
        }

        public static Control SafeArea()
            => new Control("safeArea", typeof(SafeArea));

        public static Control<InputFieldProps> EditableLabel(string identifier = "editableLabel", InputFieldProps props = default)
        {
            props = props ?? new InputFieldProps();
            var control = Control(identifier, props);
            ValueObservable<bool> inputFieldActive = new ValueObservable<bool>();

            control.Children(
                InputField("inputField", props: control.props)
                    .FillParent()
                    .Active(inputFieldActive)
                    .Selected(inputFieldActive)
                    .OnDeselect(_ => inputFieldActive.value = false)
                    .OnEndEdit(_ => inputFieldActive.value = false),
                Text("label")
                    .Value(control.props.inputText)
                    .FillParent()
                    .Active(inputFieldActive.SelectDynamic(x => !x))
                .OnPointerClick(x =>
                {
                    var eventSystem = EventSystem.current;
                    var target = x.pointerPress;

                    eventSystem.SetSelectedGameObject(target);

                    UniTask.WaitForSeconds(0.5f).ContinueWith(() =>
                    {
                        if (eventSystem.currentSelectedGameObject == target)
                            inputFieldActive.value = true;
                    }).Forget();
                })
            );

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
            return HorizontalLayout(indentifer).Style(x =>
            {
                x.childControlHeight.value = true;
                x.childControlWidth.value = true;
                x.childForceExpandHeight.value = true;
                x.spacing.value = 10;
            }).Children(label, control.FlexibleWidth(true));
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
            var control = Control(identifier, props ?? new Vector3Props(), typeof(HorizontalLayoutGroup));

            control
                .PreferredHeight(30)
                .Columns(
                    10,
                    PropertyLabel(
                        "xLabel",
                        Text("text", control.props.xLabel).Value("X"),
                        FloatField("field", control.props.xField)
                            .OnChanged(x => control.props.value.value = new Vector3(x, control.props.value.value.y, control.props.value.value.z))
                    ),
                    PropertyLabel(
                        "yLabel",
                        Text("text", control.props.yLabel).Value("Y"),
                        FloatField("field", control.props.yField)
                            .OnChanged(x => control.props.value.value = new Vector3(control.props.value.value.x, x, control.props.value.value.z))
                    ),
                    PropertyLabel(
                        "zLabel",
                        Text("text", control.props.zLabel).Value("Z"),
                        FloatField("field", control.props.zField)
                            .OnChanged(x => control.props.value.value = new Vector3(control.props.value.value.x, control.props.value.value.y, x))
                    )
                );

            control.AddBinding(
                control.props.value.Subscribe(x =>
                {
                    control.props.xField.value.value = x.currentValue.x;
                    control.props.yField.value.value = x.currentValue.y;
                    control.props.zField.value.value = x.currentValue.z;
                })
            );

            return control;
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