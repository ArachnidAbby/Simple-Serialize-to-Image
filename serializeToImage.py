#                 Simple Serialize-to-Image                    #
# ============================================================ #
# author: Spidertyler2005                                      #
# github: github.com/spidertyler2005/Simple-Serialize-to-Image #
# License: MIT                                                 #
# py-version: 3.11.*                                           #
# ------------------------------------------------------------ #

from pathlib import Path
from types import GenericAlias

from typing import Protocol, Self, runtime_checkable


pxl = tuple[int, int, int]
position = tuple[int, int]

I32MAX = 2147483647
U32MAX = 4294967295

I64MAX = 9223372036854775807
U64MAX = 18446744073709551615


class ImgSurface(Protocol):
    '''A Protocol all surfaces must follow to be used
    by this simple module. This works by default with the pygame Surface
    class'''
    def get_at(self, pos: position) -> pxl:
        pass

    def set_at(self, pos: position, pixel: pxl):
        pass

    def get_width(self) -> int:
        pass

    def get_height(self) -> int:
        pass


@runtime_checkable
class ImgSerializable(Protocol):
    '''Custom Serializable objects must follow this protocol
    otherwise the package cannot properly serialize the data'''
    def img_serialize(self, handler: 'ImgHandler'):
        pass
    
    @staticmethod
    def img_deserialize(handler: 'ImgHandler') -> Self:
        pass


class ImgHandler:
    '''Handles reading and writing to a surface.
    surface must be an `ImgSurface`. Pygame surfaces work
    by default'''
    __sots__ = ("surface", "next_byte", "w", "h")

    def __init__(self, surf: ImgSurface):
        self.surface = surf
        self.next_byte = 0
        self.w = surf.get_width()
        self.h = surf.get_height()
    
    @property
    def width(self) -> int:
        return self.w

    @property
    def height(self) -> int:
        return self.h

    def write_next_byte(self, b: int) -> Self:
        b_pos = self.next_byte % 3
        y = self.next_byte // 3 // self.w
        x = self.next_byte // 3 % self.w

        color = self.surface.get_at((x, y))
        color[b_pos] = b

        self.surface.set_at((x, y), color)

        self.next_byte += 1
        return self

    def write_next_i32(self, val: int) -> Self:
        for byte_pos in range(4):
            mask = 255
            byte = (val >> ((3-byte_pos) * 8)) & mask
            self.write_next_byte(byte)

        return self
    
    def write_next_i64(self, val: int) -> Self:
        for byte_pos in range(8):
            mask = 255
            byte = (val >> ((7-byte_pos) * 8)) & mask
            self.write_next_byte(byte)

        return self

    def write_next_string(self, val: str) -> Self:
        self.write_next_i64(len(val))

        for char in val:
            byte = ord(char)
            self.write_next_byte(byte)

        return self

    def write_next_object(self, cls: ImgSerializable) -> Self:
        cls.img_serialize(self)
        return self
    
    def write_next(self, val: int|str|ImgSerializable) -> Self:
        '''Ints default to i64 for maximum percision'''
        if isinstance(val, int):
            self.write_next_i64(val)
        elif isinstance(val, str):
            self.write_next_string(val)
        elif isinstance(val, list):
            self.write_next_list(val)
        else:
            self.write_next_object(val)
        return self
    
    def write_next_list(self, val: list) -> Self:
        self.write_next_i64(len(val))

        for item in val:
            self.write_next(item)

        return self
    
    def read_next_byte(self) -> int:
        b_pos = self.next_byte % 3
        y = self.next_byte // 3 // self.w
        x = self.next_byte // 3 % self.w

        color = self.surface.get_at((x, y))
        self.next_byte += 1
        return color[b_pos]

    def read_next_bytes(self, size: int) -> int:
        for _ in range(size):
            yield self.read_next_byte()
    
    def read_next_i32(self) -> int:
        '''read 4 byte integer'''
        output = 0
        for byte in self.read_next_bytes(4):
            output = output << 8
            output += byte
        
        return output - ((output >= I32MAX) * (U32MAX + 1))
    
    def read_next_i64(self) -> int:
        '''read 8 byte integer'''
        output = 0
        for byte in self.read_next_bytes(8):
            output = output << 8
            output += byte

        return output - ((output >= I64MAX) * (U64MAX + 1))
    
    def read_next_string(self):
        size = self.read_next_i64()

        output = ""
        for ord in self.read_next_bytes(size):
            output += chr(ord)
        
        return output
    
    def read_next_object(self, cls: ImgSerializable.__class__) -> ImgSerializable:
        return cls.img_deserialize(self)
    
    def read_next(self, typ: type) -> int|str|ImgSerializable|list:
        if typ == int:
            return self.read_next_i64()
        if typ == str:
            return self.read_next_string()
        if isinstance(typ, GenericAlias): # lists
            return self.read_next_list(typ.__args__[0]) # get the inner member type from list[]
        else:
            return self.read_next_object(typ)
        
    def read_next_list(self, inner_typ: type) -> list:
        size = self.read_next_i64()

        output = []
        for _ in range(size):
            item = self.read_next(inner_typ)
            output.append(item)
        
        return output
    
    def save_file(self, file: str | Path) -> Self:
        import pygame
        pygame.image.save(self.surface, file)
        return self


if __name__ == "__main__":
    from random import randint
    import pygame
    
    pygame.init()

    class Player_Example:
        __slots__ = ("x", "y", "health", "name")

        def __init__(self):
            self.x = 0
            self.y = 0
            self.health = 100
            self.name = "Jonny Razer"

        def __str__(self) -> str:
            return f"PLAYER[{repr(self.name)}](x: {self.x}, y: {self.y}, health: {self.health})"

        def __repr__(self) -> str:
            return f"<{self.__str__()}>"

        # Image Serialization
        def img_serialize(self, handler: ImgHandler):
            handler.write_next_i32(self.x)\
                .write_next_i32(self.y)\
                .write_next_i32(self.health)\
                .write_next_string(self.name)
        
        @staticmethod
        def img_deserialize(handle) -> Self:
            inst = Player_Example()

            inst.x = handle.read_next_i32()
            inst.y = handle.read_next_i32()
            inst.health = handle.read_next_i32()
            inst.name = handle.read_next_string()

            return inst

    win = pygame.display.set_mode((50, 50))
    win.fill((0,0,0))

    handle = ImgHandler(win)
    simple_player = Player_Example()

    simple_player.name = "Mega man"
    simple_player.x = 600
    simple_player.y = 784
    simple_player.health = 48

    default_player = Player_Example()

    big_num = 9223372036854775807
    small_num = -9223372036854775808

    handle.write_next_string("Gaming Towners")\
        .write_next_i64(22)\
        .write_next_string("My Very Eager Mother Just Made Us Nachos")\
        .write_next_i32(9925)\
        .write_next_object(simple_player)\
        .write_next_object(default_player)\
        .write_next_list([0, 255, 512, 1024, 2048, -1])\
        .write_next_list([default_player, simple_player])\
        .write_next_list([randint(small_num, big_num) for _ in range(500)])\
        .save_file("test.png")
        # .write_next_list([(i//3%50) * 3 * (i%3) for i in range(150)])\

    img = pygame.image.load("test.png")
    img_handle = ImgHandler(img)

    print(img_handle.width)
    print(img_handle.height)
    print()
    print(img_handle.read_next_string())
    print(img_handle.read_next_i64())
    print(img_handle.read_next_string())
    print(img_handle.read_next_i32())
    print(img_handle.read_next_object(Player_Example))
    print(img_handle.read_next_object(Player_Example))
    print(img_handle.read_next(list[int]))
    print(img_handle.read_next(list[Player_Example]))
    print(img_handle.read_next(list[int])[0:30])
    pygame.quit()
