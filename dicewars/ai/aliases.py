from typing import Union

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand


Name = int

Command = Union[BattleCommand, TransferCommand, EndTurnCommand]