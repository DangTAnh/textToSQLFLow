"""Write a validated Flow model to a JSON file on disk.
"""

import json
import logging
from pathlib import Path

from text_to_sql_flow.types import Flow

logger = logging.getLogger(__name__)


def write_flow_json(flow: Flow, output_dir: Path) -> Path:
    """Write a Flow model to a pretty-printed JSON file.

    Creates the output directory if it does not exist.
    Names the file ``{flow_name}_flow.json`` (sanitized).

    Returns the absolute path to the written file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = flow.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    output_path = output_dir / f"{safe_name}_flow.json"

    data = flow.to_serializable_dict()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    resolved = output_path.resolve()
    logger.info("Flow written to %s", resolved)
    return resolved
