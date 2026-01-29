using UnityEngine;
using UnityEngine.EventSystems;

public class Scrim : MonoBehaviour, IPointerClickHandler
{
    public bool destroyOnClickAway;

    public void OnPointerClick(PointerEventData eventData)
    {
        if (destroyOnClickAway && eventData.rawPointerPress == gameObject)
            Destroy(gameObject);
    }
}
