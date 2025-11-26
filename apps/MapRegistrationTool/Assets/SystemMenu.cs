using System;
using System.Linq;
using System.Collections.Generic;

using UnityEngine;
using UnityEngine.InputSystem;

namespace Outernet.MapRegistrationTool
{
    public class SystemMenu : MonoBehaviour
    {
        private static readonly float COMMAND_REPEAT_DELAY = 0.2f;

        public DropdownMenu template;

        private static SystemMenu _instance;
        private static Dictionary<string, DropdownMenu> _menus = new Dictionary<string, DropdownMenu>();
        private static List<KeyCommand> _keyCommands = new List<KeyCommand>();

        private KeyCommand _lastCommand = null;
        private float _timeRemainingToRepeat = 0;

        private class KeyCommand
        {
            public bool hasCommandKey { get; private set; }
            public Key[] keyCombination { get; private set; }
            public Action action { get; private set; }
            public Func<bool> validate { get; private set; }

            public KeyCommand(Key[] keyCombination, Action action, Func<bool> validate)
            {
                this.keyCombination = keyCombination;
                this.action = action;
                this.validate = validate;
                hasCommandKey = keyCombination.Contains(Utility.GetPlatformCommandKey());
            }
        }

        private void Awake()
        {
            if (_instance != null)
            {
                Destroy(this);
                throw new Exception($"Only one instance of {nameof(SystemMenu)} allowed in the scene at a time. Destroying.");
            }

            _instance = this;

            template.gameObject.SetActive(false);
        }

        private void Update()
        {
            if (TryGetCurrentCommand(out var command))
            {
                if (command == _lastCommand)
                {
                    _timeRemainingToRepeat -= Time.deltaTime;
                    if (_timeRemainingToRepeat <= 0)
                    {
                        command.action.Invoke();
                        _timeRemainingToRepeat = COMMAND_REPEAT_DELAY;
                    }
                }
                else
                {
                    command.action.Invoke();
                    _lastCommand = command;
                    _timeRemainingToRepeat = COMMAND_REPEAT_DELAY;
                }
            }
            else
            {
                _lastCommand = null;
            }
        }

        private bool TryGetCurrentCommand(out KeyCommand command)
        {
            var needsCommandKey = Utility.KeyboardIsFocused();
            var pressedKeys = Keyboard.current.allKeys.Where(x => x != null && x.isPressed).Select(x => x.keyCode).ToArray();

            foreach (var keyCommand in _keyCommands)
            {
                if (needsCommandKey && !keyCommand.hasCommandKey)
                    continue;

                if (!KeyCombinationsMatch(keyCommand.keyCombination, pressedKeys))
                    continue;

                if (keyCommand.validate != null && !keyCommand.validate())
                    continue;

                command = keyCommand;
                return true;
            }

            command = default;
            return false;
        }

        private bool KeyCombinationsMatch(Key[] combination1, Key[] combination2)
        {
            return combination1.Length == combination2.Length &&
                combination1.All(x => ContainsKeyOrAlias(combination2, x));
        }

        private bool ContainsKeyOrAlias(Key[] keyCombination, Key key)
        {
            switch (key)
            {
                case Key.LeftCtrl:
                case Key.RightCtrl:
                    return ContainsAny(keyCombination, Key.LeftCtrl, Key.RightCtrl);
                case Key.RightAlt:
                case Key.LeftAlt:
                    return ContainsAny(keyCombination, Key.RightAlt, Key.LeftAlt);
                case Key.RightMeta:
                case Key.LeftMeta:
                    return ContainsAny(keyCombination, Key.RightMeta, Key.LeftMeta);
                case Key.RightShift:
                case Key.LeftShift:
                    return ContainsAny(keyCombination, Key.RightShift, Key.LeftShift);
                default:
                    return keyCombination.Contains(key);
            }
        }

        private bool ContainsAny(Key[] keys, params Key[] values)
        {
            foreach (var key in keys)
            {
                if (values.Contains(key))
                    return true;
            }

            return false;
        }

        public static void AddMenuItem(string path, Action onSelect, Func<string> getName = default, Func<bool> validate = default, int priority = default)
            => AddMenuItem(path, onSelect, getName, validate, priority, default(Key[][]));

        public static void AddMenuItem(string path, Action onSelect, Func<string> getName = default, Func<bool> validate = default, int priority = default, params Key[] commandKeys)
            => AddMenuItem(path, onSelect, getName, validate, priority, new Key[][] { commandKeys });

        public static void AddMenuItem(string path, Action onSelect, Func<string> getName = default, Func<bool> validate = default, int priority = default, params Key[][] commandKeys)
        {
            if (!path.Contains('/'))
                throw new Exception("Menu items must indicate a parent menu using '/'");

            if (commandKeys != null && commandKeys.Length > 0)
            {
                foreach (var command in commandKeys)
                    _keyCommands.Add(new KeyCommand(command, onSelect, validate));

                _keyCommands.Sort((x, y) => -x.keyCombination.Length.CompareTo(y.keyCombination.Length));
            }

            var topLevelMenu = path.Substring(0, path.IndexOf('/'));

            if (!_menus.TryGetValue(topLevelMenu, out var menu))
            {
                menu = Instantiate(_instance.template, _instance.template.transform.parent);
                menu.gameObject.SetActive(true);
                menu.label.text = topLevelMenu;
                _menus.Add(topLevelMenu, menu);
            }

            string keyCommandString = commandKeys == null ? null : string.Join("+", commandKeys[0].Select(GetKeyName));
            menu.AddMenuItem(path.Substring(topLevelMenu.Length + 1), keyCommandString, onSelect, getName, validate, priority);
        }

        private bool ValidateKey(Key key)
        {
            switch (key)
            {
                case Key.LeftCtrl:
                case Key.RightCtrl:
                    return AnyKeyValid(Key.LeftCtrl, Key.RightCtrl);
                case Key.RightAlt:
                case Key.LeftAlt:
                    return AnyKeyValid(Key.RightAlt, Key.LeftAlt);
                case Key.RightMeta:
                case Key.LeftMeta:
                    return AnyKeyValid(Key.RightMeta, Key.LeftMeta);
                case Key.RightShift:
                case Key.LeftShift:
                    return AnyKeyValid(Key.RightShift, Key.LeftShift);
                default:
                    return Keyboard.current[key].isPressed;
            }
        }

        private bool AnyKeyValid(params Key[] keys)
        {
            return keys.Any(x => Keyboard.current[x].isPressed);
        }

        private static string GetKeyName(Key key)
        {
            switch (key)
            {
                case Key.LeftCtrl:
                case Key.RightCtrl:
                    return "Ctrl";
                case Key.RightAlt:
                case Key.LeftAlt:
                    return "Alt";
                case Key.RightMeta:
                case Key.LeftMeta:
                    return Application.platform == RuntimePlatform.OSXPlayer ||
                        Application.platform == RuntimePlatform.OSXEditor ? "Cmd" : "Win";
                case Key.RightShift:
                case Key.LeftShift:
                    return "Shift";
                default:
                    return key.ToString();
            }
        }
    }
}