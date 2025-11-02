using System.Linq;
using UnityEngine;

namespace Plerion.VPS
{
    [RequireComponent(typeof(ParticleSystem))]
    public class ParticleSystemLocalizationMapRenderer : LocalizationMapRenderer
    {
        private ParticleSystem _particleSystem;
        private Color _color = Color.white;

        private void Awake()
        {
            _particleSystem = GetComponent<ParticleSystem>();
        }

        public override void SetColor(Color color)
        {
            var m = _particleSystem.main;
            m.startColor = color;
        }

        protected override void LoadPointsInternal(Point[] points)
        {
            var m = _particleSystem.main;
            _particleSystem.SetParticles(points.Select(x => new ParticleSystem.Particle()
            {
                position = x.position,
                startLifetime = Mathf.Infinity,
                startSize = 10000, // Make this huge and cap the particle size in the renderer, so they are always a constant size on screen
                startColor = x.color
            }).ToArray());
            _particleSystem.Play();
        }
    }
}