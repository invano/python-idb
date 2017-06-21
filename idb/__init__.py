import contextlib

import vstruct
from vstruct.primitives import v_uint8
from vstruct.primitives import v_uint16
from vstruct.primitives import v_uint32
from vstruct.primitives import v_bytes


class FileHeader(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.signature = v_bytes(size=0x4)  # IDA1
        self.unk04 = v_uint32()
        self.unk08 = v_uint32()
        self.unk0C = v_uint32()
        self.unk10 = v_uint32()
        self.unk14 = v_uint32()
        self.unk18 = v_uint16()
        self.sig2  = v_uint32()  # | DD CC BB AA |
        self.unk1E = v_uint16()

        # not exactly the file size
        # smaller than size2?
        self.size1 = v_uint32()
        self.unk24 = v_uint32()
        self.unk28 = v_uint32()
        self.unk2C = v_uint32()

        # not exactly the file size
        # larger than size1?
        self.size2 = v_uint32()
        self.unk34 = v_uint32()

        # changes upon each save
        self.csum1 = v_bytes(size=0x4)
        # does not change upon each save
        self.csum2 = v_bytes(size=0x8)

        self.unk44 = v_uint32()
        self.unk48 = v_uint32()
        self.unk4C = v_uint32()
        self.unk50 = v_uint32()
        self.unk54 = v_uint32()
        self.unk58 = v_uint32()
        self.unk5C = v_uint32()
        self.unk60 = v_bytes(size=0x10)
        self.unk70 = v_bytes(size=0x10)
        self.unk80 = v_bytes(size=0x10)
        self.unk90 = v_bytes(size=0x10)
        self.unkA0 = v_bytes(size=0x10)
        self.unkB0 = v_bytes(size=0x10)
        self.unkC0 = v_bytes(size=0x10)
        self.unkD0 = v_bytes(size=0x10)
        self.unkE0 = v_bytes(size=0x10)
        self.unkF0 = v_bytes(size=0x0D)

    def validate(self):
        if self.signature != b'IDA1':
            raise ValueError('bad signature')
        if self.sig2 != 0xAABBCCDD:
            raise ValueError('bad sig2')
        return True


class Section(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.length = v_uint32()
        self.unk4 = v_uint32()
        self.contents = v_bytes()

    def pcb_length(self):
        self['contents'].vsSetLength(self.length)

    def validate(self):
        if self.length == 0:
            raise ValueError('zero size')
        if self.length != len(self.contents):
            raise ValueError('bad size')
        return True


class ID0(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.unk00 = v_bytes(size=0x10)
        self.unk10 = v_bytes(size=0x03)
        self.signature = v_bytes(size=0x09)

    def validate(self):
        if self.signature != b'B-tree v2':
            raise ValueError('bad signature')
        return True


class ID1(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.signature = v_bytes(size=0x03)

    def validate(self):
        if self.signature != b'VA*':
            raise ValueError('bad signature')
        return True


class NAM(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.signature = v_bytes(size=0x03)

    def validate(self):
        if self.signature != b'VA*':
            raise ValueError('bad signature')
        return True


class TIL(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.signature = v_bytes(size=0x06)

    def validate(self):
        if self.signature != b'IDATIL':
            raise ValueError('bad signature')
        return True


class IDB(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.header = FileHeader()
        self.section_id0  = Section()
        # not padding, because it doesn't align the following section.
        self.unk1 = v_uint8()
        self.section_id1  = Section()
        self.unk2 = v_uint8()
        self.section_nam  = Section()
        self.unk3 = v_uint8()
        self.section_til = Section()

        self.id0 = None
        self.id1 = None
        self.nam = None
        self.til = None

    def pcb_section_til(self):
        id0 = ID0()
        id0.vsParse(self.section_id0.contents)
        # vivisect doesn't allow you to assign vstructs to fields,
        # so we need to override and use the default object behavior.
        object.__setattr__(self, 'id0', id0)

        id1 = ID1()
        id1.vsParse(self.section_id1.contents)
        object.__setattr__(self, 'id1', id1)

        nam = NAM()
        nam.vsParse(self.section_nam.contents)
        object.__setattr__(self, 'nam', nam)

        til = TIL()
        til.vsParse(self.section_til.contents)
        object.__setattr__(self, 'til', til)

    def validate(self):
        self.header.validate()
        self.section_id0.validate()
        self.section_id1.validate()
        self.section_nam.validate()
        self.section_til.validate()
        self.id0.validate()
        self.id1.validate()
        self.nam.validate()
        self.til.validate()
        return True


@contextlib.contextmanager
def from_file(path):
    with open(path, 'rb') as f:
        buf = f.read()
        db = IDB()
        db.vsParse(buf)
        yield db
