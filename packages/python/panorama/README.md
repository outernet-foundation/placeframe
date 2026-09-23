# panorama

Spherical capture support, kept free of API and server dependencies:

- `panorama.projection` — view layouts (tetrahedron, cube), equirectangular →
  view remapping, and the exact camera parameters of each rendered view.
  numpy only, so the reconstructor can render views without OpenCV.
- `panorama.video` — is this mp4 spherical (the `sv3d`/`equi` boxes), how big,
  how many frames, and frame extraction. Decoding needs the `video` extra.
