from importlib.metadata import version
from pathlib import Path

pins = [
    f"numpy=={version('numpy')}",
    f"scipy=={version('scipy')}",
    f"scikit-learn=={version('scikit-learn')}",
    f"statsmodels=={version('statsmodels')}",
]
Path("requirements.lock").write_text("\n".join(pins) + "\n", encoding="utf-8")
print("\n".join(pins))
