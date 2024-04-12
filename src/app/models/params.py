from enum import Enum
from pydantic import BaseModel, Field

### Request options #
class HttpParams(BaseModel):
    nbr: int = Field(default=None, ge=0)
    page_nbr: int = Field(default=None, ge=1)
    filters: dict = Field(default={}) # type: ignore


### OPERATOR ENUMS #
"""
https://www.mongodb.com/docs/manual/reference/operator/query/
$and: Joins query clauses with a logical AND returns all documents that match the conditions of both clauses.
$not: Inverts the effect of a query expression and returns documents that do not match the query expression.
$nor: Joins query clauses with a logical NOR returns all documents that fail to match both clauses.
$or: Joins query clauses with a logical OR returns all documents that match the conditions of either clause.

$regex: Selects documents where values match a specified regular expression.
$geoWithin: Selects geometries within a bounding GeoJSON geometry. The 2dsphere and 2d indexes support $geoWithin.
"""

class OP_FIELD(Enum):
    """
    Operators for single_filter
    """
    EQ = "$eq"
    NE = "$ne"
    CONTAIN = "$regex"
    IN = "$in"
    NOT_IN = "$nin"
    GT = "$gt"
    GTE = "$gte"
    LT = "$lt"
    LTE = "$lte"
    NOT = "$not"

class OP(Enum):
    """
    Operators for combined_filter
    """
    AND = "$and"
    OR = "$or"
    NOR = "$nor"


class Filter():
    """
    Base filter for HttpParams.
    All params set to None by default.
    Some serve SingleFilter, others CombinedFilters.
    """
    def __init__(self, value=None, operator_field=None, field=None, filter_elements:list=None, operator=None):
        self.value = value
        self.operator_field = operator_field
        self.field = field
        self.filter_elements = filter_elements
        self.operator = operator

    def apply(self):
        raise NotImplementedError("Subclasses must implement apply() method")

    def make(self):
        l_request = {}
        if not self.filter_elements:
            # SingleFilter
            l_request = self.doBuildSingle()
        else:
            # CombinedFilter
            elements = [ self.doBuildSingle(single_filter) for single_filter in self.filter_elements ]
            self.doBuildCombined(elements)
        return l_request

    def doBuildSingle(self) -> dict:
        l_request = {}
        if self.operator_field == OP_FIELD.EQ.value:
            l_request[self.field] = self.value
        elif self.operator_field == OP_FIELD.NE.value:
            l_request[self.field] = {self.operator_field: self.value}
        elif self.operator_field == OP_FIELD.NOT.value: # value ex. {"$gt":5}
            l_request[self.field] = {self.operator_field: self.value}
        elif self.operator_field == OP_FIELD.CONTAIN.value:
            l_request[self.field] = {self.operator_field: f".*{self.value}.*", "$options": "i"}
        elif self.operator_field == OP_FIELD.IN.value or self.operator_field == OP_FIELD.NOT_IN.value:
            self.checkForList(self.value)
            l_request[self.field] = {self.operator_field: self.value}
        elif self.operator_field in [OP_FIELD.GT.value, OP_FIELD.GTE.value, OP_FIELD.LT.value, OP_FIELD.LTE.value]:
            self.checkForNum(self.value)
            l_request[self.field] = {self.operator_field: self.value}
        return l_request

    def doBuildCombined(self, elements) -> dict:
        l_request = {}
        if self.operator in [OP.AND.value, OP.OR.value, OP.NOR.value]:
            l_request[self.operator] = elements
        return l_request

    def checkForList(self, value):
        if not isinstance(self.value, list):
            raise ValueError("Value should be a list.")

    def checkForNum(self, value):
        if not isinstance(self.value, int) and not isinstance(self.value, float):
            raise ValueError("Value should be a number.")



class SingleFilter(Filter):
    """
    SINGLE_FILTER: { value, operator_field, field }
    params:
        value: Any
        operator_field: OP_FIELD()
        field: Collection_field
    """
    def __init__(self, value, operator_field: OP_FIELD, field: str): # type: ignore
        self.value = value
        self.operator_field = operator_field
        self.field = field

    def apply(self):
        for op in OP_FIELD:
            if self.operator_field == op.value:
                 return True
            else:
                # raise ValueError("unsupported operator_field")
                return False


class CombinedFilter(Filter):
    """
    COMBINED_FILTER: { filter_elements: list[SingleFilter], operator}
        param:
            filter_elements: list of SingleFilter()
            operator: OP()
    """
    def __init__(self, filter_elements: list[SingleFilter], operator: OP): # type: ignore
        self.filter_elements = filter_elements
        self.operator = operator

    def apply(self):
        for op in OP:
            if self.operator == op.value:
                return True
            else:
                return False
