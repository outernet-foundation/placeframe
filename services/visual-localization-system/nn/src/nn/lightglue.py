from lightglue import LightGlue


def load_lightglue(device: str):
    # TODO: add comment about why width_confidence and depth_confidence are set to -1
    return LightGlue(features="superpoint", width_confidence=-1, depth_confidence=-1).eval().to(device)
