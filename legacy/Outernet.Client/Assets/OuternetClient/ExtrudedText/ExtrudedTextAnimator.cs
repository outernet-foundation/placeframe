using System;
using System.Linq;
using TMPro;
using UnityEngine;

namespace Outernet.Client
{
    public class Sample_TMP3D_Animation : MonoBehaviour
    {
        static readonly Vector2 m_minMax = new Vector2(0.8f, 2f);
        const float m_offset = 1f;
        const float m_speed = 1.5f;

        [SerializeField]
        ExtrudedTextMeshPro m_tmp3DHandler;

        const float transitionDuration = 0.2f;
        float transitionTime = transitionDuration;

        public bool animate = false;

        void Update()
        {
            if (!animate)
            {
                if (transitionTime == transitionDuration) return;

                transitionTime += Time.deltaTime;
                if (transitionTime > transitionDuration)
                {
                    transitionTime = transitionDuration;
                }
            }
            else
            {
                transitionTime -= Time.deltaTime;
                if (transitionTime < 0)
                {
                    transitionTime = 0;
                }
            }

            var min = Mathf.Lerp(m_minMax.x, m_minMax.y, transitionTime / transitionDuration);

            float time = Time.time;

            var tmp = m_tmp3DHandler.GetComponent<TextMeshPro>();
            m_tmp3DHandler.SetDepthData(Enumerable
                .Range(0, tmp.textInfo.characterCount)
                .Select(i =>
                {
                    var depth = Mathf.Lerp(min, m_minMax.y, Mathf.Sin((i * m_offset) - time * Mathf.PI * m_speed) * 0.5f + 0.5f);
                    return new Vector3(depth, 0, depth / m_minMax.y);
                })
                .ToArray());
        }
    }
}
