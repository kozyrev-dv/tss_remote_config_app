import enum

@enum.unique
class SnmpCommandCode(enum.IntEnum):
    GET = 1
    WALK = 3
    SET = 2

@enum.unique
class ScriptRunStatusesEnum(enum.IntEnum):
    OK = 0x00_00_00_00
    UNKNOWN_ERROR = 0xff_ff_ff_ff
    UNKNOWN_MIB_OBJECT = 0xff_00_00_01
    
    IP_INVALID = 0x00_00_00_01
    DESTINATION_UNREACHABLE = 0x00_00_00_02
    CONNECTION_LOSS = 0x00_00_00_03
    SYNC_TIMEOUT = 0x00_00_01_00

    ## Remote Config Specific
    COEF_COHERENCY_LOSS = 0x00_01_00_01