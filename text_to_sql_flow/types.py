"""Pydantic models for Spark SQL ETL flow definitions.

These models match the JSON schema defined in sample.txt — the contract
between Flow → Steps → Output that the LLM generates and the parsers validate.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class CreatedDate(BaseModel):
    """Wraps the ``$date`` format used in sample.txt for timestamp fields.

    Pydantic v2 handles the alias transparently: pass ``{"$date": "..."}``
    directly to ``CreatedDate.model_validate()`` or construct via
    ``CreatedDate(date=datetime(...))``.
    """

    model_config = ConfigDict(populate_by_name=True)

    date: datetime = Field(alias="$date")


class StepOutput(BaseModel):
    """steps.output — stores execution result information.

    - **tempView**: spark temp view name holding the SQL result, data cached on storage
    - **table**: target parquet table on HDFS (empty string if not persisted)
    - **appendType**: write mode (REPLACE, APPEND, etc.)
    - **kafkaGroup**: Kafka consumer group (for streaming sources)
    """

    model_config = ConfigDict(populate_by_name=True)

    tempView: str
    table: str = ""
    appendType: str = "REPLACE"
    kafkaGroup: str = ""


class Diagram(BaseModel):
    """steps.diagram — display position on the flow diagram.

    The UI uses these coordinates to render the step node.
    Display size is 30x10 units, spacing is 20 units.
    """

    model_config = ConfigDict(populate_by_name=True)

    x: int
    y: int


class Step(BaseModel):
    """steps[] — a single step in the Spark SQL ETL flow.

    - **name**: unique identifier within the flow
    - **parents**: names of upstream steps whose temp views / tables this step reads
    - **order**: execution order (same order → parallel execution)
    - **sql**: the Spark SQL statement. Uses ``${table_var}`` for table variables
      and ``$[param_var]`` for parameter placeholders.
    - **output**: metadata about the output temp view / table
    - **description**: business description of what this step does
    - **diagram**: UI position on the flow diagram
    - **active**: whether this step is currently enabled
    - **createdDate**: timestamp of creation
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str
    parents: list[str] = Field(default_factory=list)
    order: int
    sql: str
    output: StepOutput
    description: str = ""
    diagram: Diagram
    active: bool = True
    createdDate: CreatedDate


class Flow(BaseModel):
    """Top-level flow model — a complete Spark SQL ETL flow.

    - **name**: flow identifier
    - **description**: business description of the flow
    - **steps**: ordered list of SQL execution steps
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str = ""
    steps: list[Step]

    def to_serializable_dict(self) -> dict:
        """Serialize to a dict suitable for JSON output.

        Handles the ``createdDate.$date`` alias so the output matches
        the sample.txt format exactly.
        """
        return self.model_dump(by_alias=True, mode="json")
