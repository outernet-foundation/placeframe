using UnityEngine;

namespace Outernet.Client
{
  public class PanoramicImageView : MonoBehaviour
  {
    public Material panoramaMaterial;
    public Texture2D panoramaTexture;
    public float heading = 0f;
    public float pitch = 0f;
    public float fov = 60f;

    void Start()
    {
      panoramaMaterial.SetTexture("_MainTex", panoramaTexture);
    }

    public void UpdatePanorama(Vector2 mouseDelta)
    {
      heading -= mouseDelta.x / Screen.width * fov;
      pitch -= mouseDelta.y / Screen.height * fov;

      pitch = Mathf.Clamp(pitch, -1.5708f, 1.5708f);
      heading = Mathf.Repeat(heading, 360f);

      panoramaMaterial.SetFloat("_AdjustedHeading", heading * fov);
      panoramaMaterial.SetFloat("_AdjustedPitch", pitch * fov);
    }
  }
}