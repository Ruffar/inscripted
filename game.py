from __future__ import annotations
import json

def BoolToSign(x: bool) -> int:
    return -1+2*int(x)

def Clamp(x: int, lowerBound: int, upperBound: int) -> int:
    return max(lowerBound,min(upperBound, x))



class Match:
    def __init__(self):
        self._turn = False #False = Plr 1, True = Plr 2
        self._players = [Player(), Player()]

    def GetScale(self) -> int:
        #Higher means player 2 is losing
        return 5-self._players[0]+self._players[1]


class Player:
    def __init__(self):
        self._scaleTeeth = 0 #Higher teeth means you are losing
        
        self._board = Board()
        self._hand = CardCollection(20) #Stores cards in hand
        self._deck = CardCollection(40)

        self._bones = 0

    def Damage(self, amount: int) -> None:
        self._scaleTeeth += amount

    def AddBones(self, amount: int) -> None:
        self._bones += amount

    def RemoveBones(self, amount: int) -> None:
        self._bones = max(self._bones-amount, 0)

    def GetBoard(self) -> CardCollection:
        return self._board

    def GetHand(self) -> CardCollection:
        return self._hand

    def GetDeck(self) -> CardCollection:
        return self._deck



class CardCollection:
    def __init__(self, maxCards: int):
        self._max = maxCards
        self._cards = []

    def GetCard(self, cardNo: int) -> CardFactory._Card:
        return self._cards[cardNo]

    def AddCard(self, newCard: CardFactory._Card) -> bool: #Returns true if added successfully
        if not isinstance(newCard, CardFactory._Card):
            raise TypeError("Invalid Card")
        if not self.IsFull():
            self._cards.append(newCard)
            return True
        return False

    def RemoveCard(self, cardNo: int) -> None:
        self._cards.pop(cardNo)

    def IsFull(self) -> bool:
        return len(self._cards) >= self._max


class Board(CardCollection):
    def __init__(self):
        super.__init__(self, 4)
        self._cards = [None, None, None, None]

    def AddCard(self, newCard: CardFactory._Card, cardNo: int) -> bool:
        if not isinstance(newCard, CardFactory._Card):
            raise TypeError("Invalid Card")
        self._cards[cardNo] = newCard
        return True

    def RemoveCard(self, cardNo: int) -> None:
        self._cards[cardNo] = None

    def IsFull(self) -> bool:
        for c in self._cards:
            if c == None:
                return False
        return True


## Match Stuff ##
class MatchEvent:
    def __init__(self, owner: Player, enemy: Player):
        self._owner = owner
        self._enemy = enemy

    def Process(self) -> None:
        pass

class CardEvent(MatchEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player):
        super.__init__(self, owner, enemy)
        self._cardPos = cardPos
        
class CardPlay(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player):
        super.__init__(self, cardPos, owner, enemy)


class Combat(MatchEvent):
    def __init__(self, owner: Player, enemy: Player):
        super.__init__(self, owner, enemy)

    def Process(self) -> None:
        ownerBoard = self._owner.GetBoard()
        for i in range(4):
            card = ownerBoard.GetCard()
            if card != None and isinstance(card, CardFactory._Card):
                attackEvent = Attack(i, self._owner, self._enemy)
                for sigil in card.GetSigils():
                    sigil.OnAttack(attackEvent)
                attackEvent.Process()

        
class Attack(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player):
        super.__init__(self, cardPos, owner, enemy)
        self._targets = [StrikeData(cardPos, self.GetAttacker().GetPower(), False)] #Array of positions going to be attacked

    def GetStrikeData(self) -> list[StrikeData]:
        return self._targets

    def GetAttacker(self) -> CardFactory._Card:
        return self._owner.GetBoard().GetCard(self._cardPos)
        
    def Process(self) -> None:
        attacker = self.GetAttacker()
        for target in self._targets:
            hurtEvent = Hurt(self._cardPos, self._enemy, self._owner, target)
            targetCard = hurtEvent.GetTarget()
            for sigil in targetCard.GetSigils():
                sigil.OnHurt(hurtEvent)
            hurtEvent.Process()
        

class Hurt(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player, strikeData: StrikeData):
        super.__init__(self, cardPos, owner, enemy)
        self._strikeData = strikeData

    def GetStrikeData(self) -> StrikeData:
        return self._strikeData

    def GetAttacker(self) -> CardFactory._Card:
        return self._enemy.GetBoard().GetCard(self._cardPos)

    def GetTarget(self) -> CardFactory._Card:
        return self._owner.GetBoard().GetCard(self._cardPos)

    def Process(self) -> None:
        if self._strikeData.attacksDirectly:
            self._owner.Damage(self._strikeData.power)
        else:
            self.GetTarget().Damage(self._strikeData.power)
        

class StrikeData:
    def __init__(self, cardPos: int, power: int, attacksDirectly: bool):
        self.cardPos = cardPos
        self.power = power
        self.attacksDirectly = attacksDirectly



## Cards ##
class CardFactory:
    class _CardBase: #abstract
        def __init__(self, name: str, image: str, health: int, sigils: list[Sigil], tribes: list[TribeFactory._Tribe]):
            self._name = name
            self._image = image
            self._health = health

            if sigils == None:
                self._sigils = []
            elif isinstance(sigils, Sigil):
                self._sigils = [sigils]
            else:
                self._sigils = sigils

        def GetName(self) -> str:
            return self._name

        def GetImage(self) -> str:
            return self._image

        def GetHealth(self) -> int:
            return self._health

        def GetSigils(self) -> list[Sigil]:
            return self._sigils.copy()


    class _UnitCardBase(_CardBase):
        def __init__(self, name: str, image: str, health: int, sigils: list[Sigil], power: int, costType: int, costAmount: int):
            super.__init__(self, name, image, health, sigils)
            
            self._power = power
            
            if not isinstance(costType, int) or not (0 <= costType <= 2):
                raise TypeError("Cost must be 0, 1, or 2")
            self._costType = costType # 0=Nothing, 1=Blood, 2=Bone
            
            self._costAmount = costAmount

        def GetPower(self) -> int:
            return self._power

        def GetCostType(self) -> int:
            return self._costType

        def GetCostAmount(self) -> int:
            if self._costType == 0:
                return 0
            else:
                return self._costAmount


    class _TerrainCardBase(_CardBase):
        def __init__(self, name: str, image: str, health: int, sigils: list[Sigil]):
            super.__init__(self, name, image, health, sigils)
        


    class _Card: #abstract
        def __init__(self, base: CardFactory._CardBase):
            self._base = base
            self._health = self._base.GetHealth()
            self._buffs = [] #List of buffs

        def GetBase(self) -> CardFactory._CardBase:
            return self._base

        def GetHealth(self) -> int:
            return self._health

        def IsDamaged(self) -> bool:
            return self._health < self._base.GetHealth()

        def Damage(self, amount: int) -> None:
            self._health = max(self._health-amount, 0)

        def GetSigils(self) -> list[Sigil]:
            return self._base.GetSigils()


    class _UnitCard(_Card):
        def __init__(self, base: CardFactory._UnitCardBase):
            super.__init__(self, base)
            self._power = self._base.GetPower()

        def GetPower(self) -> int:
            return self._power

    class _TerrainCard(_Card):
        def __init__(self, base: CardFactory._TerrainCardBase):
            super.__init__(self, base)


    # Get cards from card.json #


### Tribes ###
class TribeFactory:
    _tribes = {}

    class _Tribe:
        def __init__(self, name: str):
            self._name = name

        def GetName(self) -> str:
            return self._name

    # Get tribes from tribe.json #
    with open("tribes.json","r") as f:
        tribeData = json.load(f)
        for name in tribeData["tribes"]:
            upperName = name.upper()
            _tribes[upperName] = (_Tribe(upperName))

    @staticmethod
    def GetTribe(name: str) -> TribeFactory._Tribe:
        return CardFactory._tribes[name]



### Sigils ###
class Sigil: #abstract
    def __init__(self, name: str, image: str):
        self._name = name
        self._image = image

        """
        To create a sigil, create a subclass and in order to implement functionality
        Create methods with these specific names and they will trigger during events:
        MethodName(paramType1, paramType2, ...)

        OnPlay(card, board, player, player) #current player, enemy player
        OnAttack(card, board, player, player)
        """

    def GetName(self) -> str:
        return self._name

    def GetImage(self) -> str:
        return self._image

    def OnPlay(self, cardPlay: CardPlay) -> None:
        pass

    def OnAttack(self, attack: Attack) -> None:
        pass

    def OnHurt(self, hurt: Hurt) -> None:
        pass


class AirborneSigil(Sigil):
    def __init__(self):
        super.__init__(self, "AIRBORNE", "airborne.png")

    def OnAttack(self, attack: Attack) -> None:
        for sd in attack.GetStrikeData():
            sd.attacksDirectly = True

class MightyLeapSigil(Sigil):
    def __init__(self):
        super.__init__(self, "MIGHTYLEAP", "mightyleap.png")

    def OnHurt(self, hurt: Hurt) -> None:
        hurt.GetStrikeData().attacksDirectly = False
