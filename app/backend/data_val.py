from pydantic import BaseModel

class CodeSelection(BaseModel):
    code: str

    startLine: int
    startColumn: int

    endLine: int
    endColumn: int