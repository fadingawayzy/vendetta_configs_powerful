from aiogram.fsm.state import State, StatesGroup

class CustomSubFlow(StatesGroup):
    waiting_limit = State()