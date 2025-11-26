using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

using TMPro;

namespace Outernet.MapRegistrationTool
{
    public class DropdownMenu : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
    {
        public bool openOnHover;
        public TextMeshProUGUI label;
        public Button button;
        public GameObject dropdown;
        public DropdownMenuItem menuItemPrefab;
        public DropdownMenu subMenuPrefab;

        private class ElementData
        {
            public DropdownMenuItem menuItem;
            public DropdownMenu subMenu;
            public Func<string> getName;
            public Func<bool> validate;
            public int priority;
            public int addOrder;
        }

        private Dictionary<string, ElementData> _elements = new Dictionary<string, ElementData>();
        private int _nextAddOrder = 0;

        private void Awake()
        {
            button.onClick.AddListener(OpenDropdown);
        }

        private void Update()
        {
            if (dropdown.activeSelf &&
                (EventSystem.current.currentSelectedGameObject == null ||
                !EventSystem.current.currentSelectedGameObject.transform.IsChildOf(transform)))
            {
                dropdown.gameObject.SetActive(false);
            }
        }

        public void AddMenuItem(string path, Action onSelected, Func<string> getName = null, Func<bool> validate = null)
            => AddMenuItem(path, null, onSelected, getName, validate);

        public void AddMenuItem(string path, string keyCommandString, Action onSelected, Func<string> getName = null, Func<bool> validate = null, int priority = 0)
        {
            string elementName = path.Contains('/') ? path.Substring(0, path.IndexOf('/')) : path;
            bool isNestedMenu = path.Length > elementName.Length;

            if (isNestedMenu)
            {
                if (!_elements.TryGetValue(elementName, out var submenuElement))
                {
                    submenuElement = new ElementData();
                    submenuElement.subMenu = Instantiate(subMenuPrefab, dropdown.transform);
                    submenuElement.subMenu.label.text = elementName;
                    _elements.Add(elementName, submenuElement);
                }

                submenuElement.subMenu.AddMenuItem(path.Substring(elementName.Length + 1), keyCommandString, onSelected, getName, validate, priority);
                return;
            }

            if (_elements.ContainsKey(elementName))
                throw new Exception($"Menu item named {path} already exists.");

            var menuItemElement = new ElementData();
            menuItemElement.validate = validate;
            menuItemElement.getName = getName;
            menuItemElement.menuItem = Instantiate(menuItemPrefab, dropdown.transform);
            menuItemElement.menuItem.keyCommand.text = keyCommandString;
            menuItemElement.priority = priority;
            menuItemElement.addOrder = _nextAddOrder;
            menuItemElement.menuItem.button.onClick.AddListener(() =>
            {
                EventSystem.current.SetSelectedGameObject(null);
                onSelected();
            });

            _nextAddOrder++;
            _elements.Add(path, menuItemElement);

            foreach (var element in _elements.Values.OrderBy(x => x.priority).ThenBy(x => x.addOrder))
                element.menuItem.transform.SetAsLastSibling();
        }

        public void OnPointerEnter(PointerEventData eventData)
        {
            if (openOnHover)
            {
                EventSystem.current.SetSelectedGameObject(gameObject);
                OpenDropdown();
            }
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            if (openOnHover && EventSystem.current.currentSelectedGameObject == gameObject)
            {
                EventSystem.current.SetSelectedGameObject(null);
                dropdown.SetActive(false);
            }
        }

        private void OpenDropdown()
        {
            dropdown.SetActive(true);

            foreach (var element in _elements)
            {
                if (element.Value.menuItem == null)
                    continue;

                element.Value.menuItem.button.interactable = element.Value.validate?.Invoke() ?? true;
                element.Value.menuItem.label.text = element.Value.getName?.Invoke() ?? element.Key;
            }
        }
    }
}