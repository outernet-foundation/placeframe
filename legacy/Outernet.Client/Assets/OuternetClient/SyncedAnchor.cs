using Outernet.Client.Location;
using Outernet.Shared;
using Placeframe.Core;
using Unity.Mathematics;
using UnityEngine;

namespace Outernet.Client
{
    [RequireComponent(typeof(Anchor))]
    public class SyncedAnchor : MonoBehaviour
    {
        public enum SyncState
        {
            Synced,
            LocallyControlled,
            Animating,
        }

        private GeoPoseRecord anchorRecord;
        private Anchor anchor;

        public SyncState State { get; set; }

        private void Awake()
        {
            anchor = GetComponent<Anchor>();
        }

        public void Initialize(
            GeoPoseRecord anchorRecord,
            double3? initialPosition = null,
            Quaternion? initialRotation = null
        )
        {
            this.anchorRecord = anchorRecord;
            anchor.SetEcefTransform(
                initialPosition
                    ?? new double3(
                        anchorRecord.ecefPosition.Value.x,
                        anchorRecord.ecefPosition.Value.y,
                        anchorRecord.ecefPosition.Value.z
                    ),
                initialRotation ?? anchorRecord.ecefRotation.Value
            );
        }

        private void Update()
        {
            if (State == SyncState.Animating)
                return;

            if (State == SyncState.LocallyControlled)
            {
                anchorRecord.ecefPosition.EnqueueSet(
                    new Double3(anchor.ecefPosition.x, anchor.ecefPosition.y, anchor.ecefPosition.z)
                );
                anchorRecord.ecefRotation.EnqueueSet(anchor.ecefRotation);

                return;
            }

            // TODO EP: Optimize by stopping interpolation when we reach our destination
            anchor.SetEcefTransform(
                math.lerp(
                    anchor.ecefPosition,
                    new double3(
                        anchorRecord.ecefPosition.Value.x,
                        anchorRecord.ecefPosition.Value.y,
                        anchorRecord.ecefPosition.Value.z
                    ),
                    0.1f
                ),
                math.slerp(anchor.ecefRotation, anchorRecord.ecefRotation.Value, 0.25f)
            );
        }
    }
}
