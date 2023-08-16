# Simple Serialize-to-Image

This is a simple way to serialize data to an image and vice-versa.
It generates images like this:

<br>
<img src="test.png" width=300>

*some upscaling artifactions - sorry*

This examples contains a lot of randomized data.

## What can be serialized

* ints (I32 or I64. I64 is default)
* strings (size is encoded with the data)
* lists (size is encoded, but not type info)
* custom objects (must follow included `ImgSerializable` protocol. Does not need to subclass)

## Usage

This is a simple module you can add to any project.

Authorship information is included at the top of the module, I would like it if
you didn't remove it. It is of course completely fine to remove it, you won't be violating
the license or anything, I just appreciate being credited for my work.

### Protocols

All protocol classes are included at the top of
the module with included doc-comments. These should explain their function.

### Type aliases

this module uses 2 type aliases:

* `pxl = tuple[int, int, int]`
* `position = tuple[int, int]`

### `ImgSurface`

This protocol is what must be followed in order for this module to do it's magic. It was modeled around the `Surface` class in pygame. That means pygame surfaces work auto-magically.

#### Important
ensure all your surfaces have adequate space to store your data!

**Required methods**

* `get_at(self, pos: position) -> pxl`
* `get_at(self, pos: position, pixel: pxl)`
* `get_width(self) -> int`
* `get_height(self) -> int`


### `ImgSerializable`

This protocol is to be followed by objects that way to be serialized or deserialized.

**Required methods**

* `img_serialize(self, handle: ImgHandler)`

**Static methods**

Uses `@staticmethod`

* `img_deserialize(handle: ImgHandler) -> Self`

### `ImgHandler`

This is the juicy bit that does all the proper serialization and deserialization.

**Instantiation**

```py
import serializeToImage

surface = ... # assuming I load an image via pygame
my_handler = serializeToImage.ImgHandler(surface)
```

**Write Methods**

All of these methods return `self`. That means fun method chaining.

* `write_next(self, val: int|str|list|ImgSerializable)-> Self`
* `write_next_byte(self, val: int) -> Self`
* `write_next_i32(self, val: int) -> Self`
* `write_next_i64(self, val: int) -> Self`
* `write_next_str(self, val: str) -> Self`
* `write_next_list(self, val: list) -> Self`

**Read Methods**

* `read_next(self, typ: type|GenericAlias) -> Any`
* `read_next_byte(self) -> int`
* `read_next_bytes(self, count: int) -> int` (generator)
* `read_next_i32(self) -> int`
* `read_next_i64(self) -> int`
* `read_next_str(self) -> str`
* `read_next_list(self, inner_typ: type|GenericAlias) -> list`

*Example of GenericAlias*

```py
list[int]
```

**Save Method**

This is pygame dependent!
This handler is writing and reading from the original surface, use whatever save-method is needed for your platform.

If you want, you can modify this method to allow for the same ease-of-use despite not using pygame.

* `save_file(self, path: Path|str) -> Self`

## Example Usage

An example with classes can be found at the very bottom of the module. Here is that example:


```py
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

handle.write_next_string("Gaming Town")\
    .write_next_i64(22)\
    .write_next_string("My Very Eager Mother Just Made Us Nachos")\
    .write_next_i32(9925)\
    .write_next_object(simple_player)\
    .write_next_object(default_player)\
    .write_next_list([0, 255, 512, 1024, 2048, -1])\
    .write_next_list([default_player, simple_player])\
    .write_next_list([randint(small_num, big_num) for _ in range(500)])\
    .save_file("test.png")

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
print()
print(img_handle.read_next(list[int]))
print(img_handle.read_next(list[Player_Example]))
print(img_handle.read_next(list[int])[0:30])
pygame.quit()
```
