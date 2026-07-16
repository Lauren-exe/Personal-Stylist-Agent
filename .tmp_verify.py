import builtins
import chat

builtins.input = lambda prompt='': 'y'
print(chat.resolve_location('Berkeley', None))
