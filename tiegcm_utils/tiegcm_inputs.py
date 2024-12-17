from pydantic import BaseModel
from typing import Tuple, List, Union, Optional

def surround_with_quotes(item):
    return f"'{str(item)}'"

""" The input used to generate the job file """
class TGCMInput(BaseModel):
    AURORA: int
    CALC_HELIUM: int
    CALENDAR_ADVANCE: int
    COLFAC: float
    CURRENT_KQ: int
    CURRENT_PG: int
    DYNAMO: int
    KP: float
    F107: float
    F107A: float
    GSWM_MI_DI_NCFILE: str
    GSWM_MI_SDI_NCFILE: str
    HIST: Tuple[int, int, int]
    LABEL: str
    MXHIST_PRIM: int
    MXHIST_SECH: int
    SOURCE: Optional[str]
    SOURCE_START: Optional[Tuple[int, int, int]]
    OUTPUT: Optional[Union[str, List[str]]]
    POTENTIAL_MODEL: str
    SECFLDS: List[str]
    SECHIST: Tuple[int, int, int]
    SECOUT: Optional[Union[str, List[str]]]
    SECSTART: Tuple[int, int, int]
    SECSTOP: Tuple[int, int, int]
    START: Tuple[int, int, int]
    START_DAY: int
    START_YEAR: int
    STEP: int
    STOP: Tuple[int, int, int]

    def write_to_file(self, file_path: str):
        with open(file_path, 'w') as f:
            # Write the header
            f.write("&TGCM_INPUT\n")
            # Iterate through the class attributes and write each one
            for field, value in self.dict().items():
                # Special formatting for list and tuple fields
                if value == None:
                    continue
                elif isinstance(value, list):
                    # assuming all lists are strings
                    value_str = ', '.join(map(surround_with_quotes, value))
                elif isinstance(value, tuple):
                    # assuming all tuples are numbers
                    value_str = ', '.join(map(str, value))
                elif isinstance(value, str):
                    value_str = surround_with_quotes(value)
                else:
                    value_str = str(value)

                f.write(f"    {field.upper()} = {value_str}\n")

            # Write the footer
            f.write("/\n")

