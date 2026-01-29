using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Outernet.Client
{
    [RequireComponent(typeof(Renderer))]
    public class CanvasAlphaAsMaterialProperty : UIBehaviour
    {
        public string colorProperty = "_BaseColor";
        public bool autoSwapMaterial;

        [ConditionalProperty(nameof(autoSwapMaterial), true)]
        public Material opaqueMaterial;

        [ConditionalProperty(nameof(autoSwapMaterial), true)]
        public Material transparentMaterial;

        private Renderer _renderer;

        protected override void Awake()
        {
            UpdatePropertyBlock();
        }

        protected override void OnTransformParentChanged()
        {
            UpdatePropertyBlock();
        }

        protected override void OnCanvasGroupChanged()
        {
            UpdatePropertyBlock();
        }

        private void UpdatePropertyBlock()
        {
            if (_renderer == null)
                _renderer = GetComponent<Renderer>();

            float alpha = this.TryGetComponentInParent<CanvasGroup>(out var group) ? group.alpha : 1f;

            if (autoSwapMaterial)
                _renderer.material = alpha == 1f ? opaqueMaterial : transparentMaterial;

            var color = _renderer.material.GetColor(colorProperty);
            color.a *= alpha;
            MaterialPropertyBlock propertyBlock = new MaterialPropertyBlock();
            propertyBlock.SetColor(colorProperty, color);
            _renderer.SetPropertyBlock(propertyBlock);
        }
    }
}