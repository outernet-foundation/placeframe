using UnityEngine;
using UnityEngine.UI;

[ExecuteAlways]
[SelectionBase]
public class PanelView : MonoBehaviour, ILayoutIgnorer
{
    public Transform center;

    public Vector2 dimensions
    {
        get => _dimensions;
        set
        {
            _dimensions = value;
            HandlePanelChanged();
        }
    }

    public float depth
    {
        get => _depth;
        set
        {
            _depth = value;
            HandlePanelChanged();
        }
    }

    public float depthOffset
    {
        get => _depthOffset;
        set
        {
            _depthOffset = value;
            HandlePanelChanged();
        }
    }

    public bool ignoreLayout => true;

    [SerializeField]
    private Vector2 _dimensions;

    [SerializeField, Min(0)]
    private float _depth;

    [SerializeField, Min(0)]
    private float _depthOffset;

    private void Update()
    {
        if (Application.isPlaying)
            return;

        if (center == null)
        {
            return;
        }

        HandlePanelChanged();
    }

    public void HandlePanelChanged()
    {
        center.localScale = new Vector3(
            dimensions.x,
            dimensions.y,
            depth
        );

        center.localPosition = new Vector3(
            0,
            0,
            -((depth * 0.5f) + depthOffset)
        );

        center.localRotation = Quaternion.identity;
    }
}
