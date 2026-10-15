# panorama

Spherical capture support, kept free of API and server dependencies:

- `panorama.projection` — view layouts (tetrahedron, cube), equirectangular →
  view remapping, and the exact camera parameters of each rendered view.
  numpy only, so the reconstructor can render views without OpenCV.
- `panorama.video` — is this mp4 spherical (the `sv3d`/`equi` boxes), how big,
  how many frames, and frame extraction. Decoding needs the `video` extra.
- `panorama.insv` — Insta360's native `.insv` (checked on an X4): two fisheye
  tracks, stitched here into equirectangular frames with the camera's factory
  lens calibration (read from the file's trailer) and a per-file fit of the turn
  between the lenses from matches across the seam. `panorama.video` dispatches to
  it, so an `.insv` imports like any equirectangular mp4. Needs the `video` extra
  (PyAV decodes the second lens track, which OpenCV cannot).
