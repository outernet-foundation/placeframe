using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

namespace Outernet.MapRegistrationTool
{
    public class AnimationEventHelper : MonoBehaviour
    {
        public UnityEvent<string> onAnimationEvent;

        public void HandleAnimationEvent(string eventType)
        {
            onAnimationEvent.Invoke(eventType);
        }
    }
}