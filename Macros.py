from pynput import keyboard
from pynput.keyboard import KeyCode, Controller
import xml.etree.ElementTree as ET

class MacroClass():
    NewKeyFunc = None
    "Stores a function to receive unused keys when macros are off."

    UsedKeyFunc = None
    "Stores a function to receive used key indexes when macros are off, meant for error notification."

    MacroTyping = False
    "True when a macro is actively typing"

    MacrosOn = True
    "When on, macro playback is possible"

    key_c = Controller()
    "Sends virtual keystrokes"

    Macros = list()
    "The macros' contents"

    Hotkeys = list()
    "The macros' activation hotkeys"

    Names = list()
    "The macros' display names"

    def __init__(self, filename):
        # Setup the keyboard listener
        listener = keyboard.Listener(
            # Set the keypress handling function
            on_press = self.on_press
        )
        # Start the keyboard listener
        listener.start()

        # Add the inital macros
        self.filename = "Macros.xml"
        if filename:
            self.filename = filename
        self.KeysSet()

    def KeysSet(self):
        "Add all macros in file"
        try:
            tree = ET.parse(self.filename)
        except:
            print("Unable to read " + self.filename)
            return
        root = tree.getroot() # Root is <macros>
        for child in root: # Each child is <macro>
            newKey = None
            newMacro = None
            newName = None
            for element in child:
                tag = element.tag
                if tag == "text": # Macro content
                    newMacro = element.text
                elif tag == "name":
                    newName = element.text
                elif tag == "key":
                    # standard keys can be set directly
                    newKey = element.text
                    if element.attrib:
                        # Add handling to special keys
                        if element.attrib["type"]:
                            # e.g. <key type="s">home</key>
                            if(element.attrib["type"]) == 's':
                                newKey = keyboard.HotKey.parse("<"+newKey+">")[0]
                            # e.g. <key type="v">65437</key>
                            if(element.attrib["type"]) == 'v':
                                newKey = KeyCode.from_vk(int(newKey))

            # Any one parameter is sufficient since
            # macros can be edited later.
            if newKey is not None or newMacro is not None or newName is not None:
                self.AddKey(newKey, newMacro, newName)

    def SetKeyFunc(self, function):
        "Named function will receive unused keys when macros are off."
        self.NewKeyFunc = function

    def SetUsedFunc(self, function):
        "Named function will receive used key indexes when macros are off, meant for error notification."
        self.UsedKeyFunc = function

    def SetMacroListening(self, state):
        "Should macro playback be available?"
        self.MacrosOn = state

    def GetMacroListening(self):
        "Is macro playback available?"
        return self.MacrosOn and not self.MacroTyping

    # Called automatically by the keyboard listener
    def on_press(self, key):
        if self.GetMacroListening():
            pressed = self.KeySearch(key)
            if pressed is not None:
                self.MacroTyping = True
                self.key_c.type(self.Macros[pressed])
                self.MacroTyping = False
        else:
            if self.MacroTyping is False:
                pressed = self.KeySearch(key)
                if pressed is not None:
                    if self.UsedKeyFunc:
                        self.UsedKeyFunc(pressed)
                else:
                    if self.NewKeyFunc:
                        self.NewKeyFunc(key)

    def KeyName(self, index):
        "Returns the friendly name of the specified macro's hotkey."
        ret = f'{self.Hotkeys[index]}'
        # Apostrophes or "half qoutes" are removed later
        if ret == '\'':
            return '\''
        # Keypad 5 can only be expressed as VK
        if ret == "<65437>":
            ret = "KP_5"
        # Remove the two half-quotes (if present)
        # and return the name in CAPS.
        return ret.replace('\'', '', 2).upper()

    def KeySearch(self, key):
        "Return the index of the pressed hotkey | None"
        pressed = None
        if hasattr(key, 'vk'):
            for index, name in enumerate(self.Hotkeys):
                if key.vk == self.Hotkeys[index]:
                    pressed = index
        if hasattr(key, 'char'):
            for index, name in enumerate(self.Hotkeys):
                if key.char == self.Hotkeys[index]:
                    pressed = index
        for index, name in enumerate(self.Hotkeys):
            if key == self.Hotkeys[index]:
                pressed = index
        return pressed

    def AddKey(self, ky, macro='', name=''):
        "Adds a new macro. Returns the list's length."
        self.Hotkeys.append(ky)
        self.Macros.append(macro)
        self.Names.append(name)
        return len(self.Names)

if __name__ == "__main__":
    print("This script is not intended for direct execution.\n" +
          "Another script should reference the Macro class.")
