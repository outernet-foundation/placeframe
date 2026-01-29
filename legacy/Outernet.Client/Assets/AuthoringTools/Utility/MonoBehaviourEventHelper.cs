using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;

public class MonoBehaviourEventHelper : UIBehaviour
{
    public UnityEvent<GameObject> onDestroyed = new UnityEvent<GameObject>();
    public UnityEvent<GameObject> onRectTransformDimesionsChanged = new UnityEvent<GameObject>();

    protected override void OnDestroy()
    {
        onDestroyed.Invoke(gameObject);
    }

    protected override void OnRectTransformDimensionsChange()
    {
        onRectTransformDimesionsChanged.Invoke(gameObject);
    }
}
