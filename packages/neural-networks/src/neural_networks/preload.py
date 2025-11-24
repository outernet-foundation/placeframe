from .dir import load_DIR
from .lightglue import load_lightglue
from .superpoint import load_superpoint

_ = load_DIR("cpu")
_ = load_superpoint("indoor", 2500, "cpu")
_ = load_superpoint("outdoor", 2500, "cpu")
_ = load_lightglue("cpu")
