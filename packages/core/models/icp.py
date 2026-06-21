from pydantic import BaseModel, Field


class ICPConfig(BaseModel):
    id: str = "default"
    name: str = "Default ICP"
    size_range: tuple[int, int] = (50, 500)  # employee count
    arr_range: tuple[int, int] = (5_000_000, 50_000_000)  # USD
    tech_stack: list[str] = Field(default_factory=lambda: [
        "HubSpot", "Salesforce", "Pipeline", "RevOps"
    ])
    keywords: list[str] = Field(default_factory=lambda: [
        "RevOps", "Revenue Operations", "Sales Engineer",
        "HubSpot", "Salesforce", "pipeline visibility",
        "attribution", "Series A", "Series B", "manual data entry"
    ])
    target_industries: list[str] = Field(default_factory=list)
    exclude_industries: list[str] = Field(default_factory=list)
    active: bool = True
