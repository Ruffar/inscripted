from __future__ import annotations
import json
import uuid
import random

def BoolToSign(x: bool) -> int:
    return -1+2*int(x)

def Clamp(x: int, lowerBound: int, upperBound: int) -> int:
    return max(lowerBound,min(upperBound, x))



class Match:
    def __init__(self, deck1: CardCollection, deck2: CardCollection):
        self._turn = False #False = Plr 1, True = Plr 2
        self._state = GameState.Normal
        self._chosenCard = -1 #becomes position of card in hand when sacrificing

        self._players = [Player(deck1), Player(deck2)]

        self.GameStart()

    def GetScale(self) -> int:
        #Higher means player 2 is losing
        return 5-self._players[0].GetTeeth()+self._players[1].GetTeeth()

    def GetTurn(self) -> bool:
        return self._turn #Returns true if it's second player's turn

    def GetState(self) -> int:
        return self._state

    def GetChosenCard(self) -> int:
        return self._chosenCard

    def GetPlayer(self, plrNo: int) -> Player:
        return self._players[plrNo]

    def GetCurrentPlayer(self) -> Player:
        return self._players[int(self._turn)]

    def GetOtherPlayer(self) -> Player:
        return self._players[int(not self._turn)]

    def GameStart(self) -> None:
        for p in range(2):
            plr = self.GetPlayer(p)
            for i in range(3):
                deck = plr.GetDeck()
                deckPos = random.randint(0,deck.GetNoOfCards()-1)
                plr.GetHand().AddCard(deck.GetCard(deckPos))
                deck.RemoveCard(deckPos)
            #Add squirrel
            plr.GetHand().AddCard(CardFactory.CreateCard("squirrel"))
            plr.GetHand().AddCard(CardFactory.CreateCard("squirrel"))

    def DrawCard(self, isSquirrel: bool) -> None:
        if self._state != GameState.Drawing:
            raise RuntimeError

        plr = self.GetCurrentPlayer()
        if isSquirrel:
            plr.GetHand().AddCard(CardFactory.CreateCard("squirrel"))
        else:
            deck = plr.GetDeck()
            deckPos = random.randint(0,deck.GetNoOfCards()-1)
            plr.GetHand().AddCard(deck.GetCard(deckPos))
            deck.RemoveCard(deckPos)

        self._state = GameState.Normal


    def Sacrifice(self, handCardPos: int, boardCardPos: list[int]) -> None:
        if self._state != GameState.Normal:
            raise RuntimeError

        plr = self.GetCurrentPlayer()
        enemy = self.GetOtherPlayer()

        handCard = plr.GetHand().GetCard(handCardPos)
        if handCard.GetBase().GetCostType() != CostType.Blood:
            raise TypeError("Card does not cost blood...")
        
        # Check total blood
        sacrificeEvents = []
        totalBlood = 0
        for i in boardCardPos:
            sacrificeEvent = Sacrifice(i, plr, enemy, handCard)
            totalBlood += sacrificeEvent.GetFinalBlood()
            sacrificeEvents.append(sacrificeEvent)

        cost = handCard.GetBase().GetCost()
        if totalBlood < cost:
            raise ValueError

        # Finish sacrificing and destroy cards
        for s in sacrificeEvents:
            print("sacrificing "+s.GetSacrificedCard().GetBase().GetName())
            s.Process()

        self._state = GameState.Sacrificed
        self._chosenCard = handCardPos


    def PlaceCard(self, handPos: int, boardPos: int) -> None:
        if self._state != GameState.Sacrificed and self._state != GameState.Normal:
            raise RuntimeError

        plr = self.GetCurrentPlayer()
        enemy = self.GetOtherPlayer()
      
        handCard = plr.GetHand().GetCard(handPos)
        print(handCard.GetBase().GetName())
        print(handCard.GetBase().GetName())

        if self._state == GameState.Sacrificed: # Card was sacrificed
            handPos = self._chosenCard
        elif handCard.GetBase().GetCostType() == CostType.Bones: # Card costed bones
            plr.AddBones(-handCard.GetCost())
        elif not handCard.GetBase().GetCostType() == CostType.Free:
            raise RuntimeError

        playEvent = CardPlay(boardPos, plr, enemy, handPos)
        playEvent.Process()

        self._state = GameState.Normal

    
    def InitiateCombat(self) -> dict[int,list[dict[str,any]]]:
        if self._state != GameState.Normal:
            raise RuntimeError
        self._state = GameState.Combat

        plr = self.GetCurrentPlayer()

        strikeData = {}

        ownerBoard = plr.GetBoard()
        for i in range(4):
            card = ownerBoard.GetCard()
            if card != None and isinstance(card, CardFactory._Card):
                attackEvent = Attack(i, self._owner, self._enemy)
                attackEvent.Process()
                attackData = []
                for x in attackEvent.GetStrikeData():
                    attackData.append(vars(x))
                strikeData[i] = attackData

        self._state = GameState.Normal
        self._turn = not self._turn



class GameState: #Enum
    Normal = 0
    Sacrificed = 1
    Combat = 2
    Drawing = 3

    _stateStr = {
      0: "NORMAL",
      1: "SACRIFICED",
      2: "COMBAT",
      3: "DRAWING"
    }
  
    @staticmethod
    def ToString(state: int) -> str:
      return GameState._stateStr[state]
  

class Player:
    def __init__(self, deck: CardCollection):
        self._scaleTeeth = 0 #Higher teeth means you are losing
        
        self._board = Board()
        self._hand = CardCollection(20) #Stores cards in hand
        if deck.GetNoOfCards() < 40:
            raise TypeError
        self._deck = deck

        self._bones = 0

    def GetTeeth(self) -> int:
        return self._scaleTeeth

    def Damage(self, amount: int) -> None:
        self._scaleTeeth += amount

    def AddBones(self, amount: int) -> None: #amount can be negative
        self._bones = max(self._bones+amount, 0)

    def GetBones(self) -> int:
        return self._bones

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

    def GetNoOfCards(self) -> int:
        return len(self._cards)
  
    def IsFull(self) -> bool:
        return len(self._cards) >= self._max


class Board(CardCollection):
    def __init__(self):
        super().__init__(4)
        self._cards = [None, None, None, None]

    def AddCard(self, newCard: CardFactory._Card, cardNo: int) -> bool:
        if not isinstance(newCard, CardFactory._Card):
            raise TypeError("Invalid Card")
        self._cards[cardNo] = newCard
        return True

    def RemoveCard(self, cardNo: int) -> None:
        self._cards[cardNo] = None

    def IsFree(self, pos: int) -> bool:
        return self._cards[pos] == None

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

    def ActivateSigils(self, card: CardFactory._Card) -> None:
        pass

    def Process(self) -> None:
        pass

class CardEvent(MatchEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player):
        super().__init__(owner, enemy)
        self._cardPos = cardPos
        
class CardPlay(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player, handPos: int):
        super().__init__(cardPos, owner, enemy)
        self._handPos = handPos

    def GetCard(self) -> CardFactory._Card:
        return self._owner.GetHand().GetCard(self._handPos)

    def ActivateSigils(self, card: CardFactory._Card) -> None:
        for sigil in card.GetSigils():
            sigil.OnPlay(self)

    def Process(self) -> None:
        hand = self._owner.GetHand()
        board = self._owner.GetBoard()

        playedCard = self.GetCard()

        if not board.IsFree(self._cardPos):
            raise ValueError

        self.ActivateSigils(playedCard)

        board.AddCard(playedCard, self._cardPos)
        hand.RemoveCard(self._handPos)
        


class Sacrifice(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player, handCard: CardFactory._UnitCard):
        super().__init__(cardPos, owner, enemy)
        self._handCard = handCard

    def GetSacrificedCard(self) -> CardFactory._UnitCard:
        return self._owner.GetBoard().GetCard(self._cardPos)

    def GetHandCard(self) -> CardFactory._UnitCard:
        return self._handCard

    def GetFinalBlood(self) -> int:
        return self.GetSacrificedCard().GetBlood()

    def ActivateSigils(self, card: CardFactory._Card) -> None:
        for sigil in card.GetSigils():
            sigil.OnSacrifice(self)
          
    def Process(self) -> None:
        self.ActivateSigils(self.GetSacrificedCard())
        dieEvent = Die(self._cardPos, self._owner, self._enemy, False)
        dieEvent.Process()

        
class Attack(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player):
        super().__init__(cardPos, owner, enemy)
        self._targets = [StrikeData(cardPos, self.GetAttacker().GetPower(), False)] #Array of positions going to be attacked

    def GetStrikeData(self) -> list[StrikeData]:
        return self._targets

    def GetAttacker(self) -> CardFactory._Card:
        return self._owner.GetBoard().GetCard(self._cardPos)

    def ActivateSigils(self, card: CardFactory._Card) -> None:
        for sigil in card.GetSigils():
            sigil.OnAttack(self)
        
    def Process(self) -> None:
        self.ActivateSigils(self.GetAttacker())
        
        for target in self._targets:
            hurtEvent = Hurt(self._cardPos, self._enemy, self._owner, target)
            hurtEvent.Process()
        

class Hurt(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player, strikeData: StrikeData):
        super().__init__(cardPos, owner, enemy)
        self._strikeData = strikeData

    def GetStrikeData(self) -> StrikeData:
        return self._strikeData

    def GetAttacker(self) -> CardFactory._Card:
        return self._enemy.GetBoard().GetCard(self._cardPos)

    def GetTarget(self) -> CardFactory._Card:
        return self._owner.GetBoard().GetCard(self._cardPos)

    def ActivateSigils(self, card: CardFactory._Card) -> None:
        for sigil in card.GetSigils():
            sigil.OnHurt(self)

    def Process(self) -> None:
        self.ActivateSigils(self.GetTarget())
      
        if self._strikeData.attacksDirectly:
            self._owner.Damage(self._strikeData.power)
        else:
            target = self.GetTarget()
            target.Damage(self._strikeData.power)
            if target.GetHealth() <= 0:
                dieEvent = Die(self._cardPos, self._owner, self._enemy, True)
                dieEvent.Process()


class Die(CardEvent):
    def __init__(self, cardPos: int, owner: Player, enemy: Player, inCombat: bool):
        super().__init__(cardPos, owner, enemy)
        self._inCombat = inCombat

    def GetCard(self) -> CardFactory._Card:
        return self._owner.GetBoard().GetCard(self._cardPos)

    def isInCombat(self) -> bool:
        return self._inCombat

    def ActivateSigils(self, card: CardFactory._Card) -> None:
        for sigil in card.GetSigils():
            sigil.OnDie(self)

    def Process(self) -> None:
        self.ActivateSigils(self.GetCard())
        self._owner.GetBoard().RemoveCard(self._cardPos)


class StrikeData:
    def __init__(self, cardPos: int, power: int, attacksDirectly: bool):
        self.cardPos = cardPos
        self.power = power
        self.attacksDirectly = attacksDirectly



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
        return TribeFactory._tribes[name.upper()]



### Sigils ###
class SigilFactory:
    class _Sigil: #abstract
        def __init__(self, name: str, image: str):
            self._name = name
            self._image = image
    
        def GetName(self) -> str:
            return self._name
    
        def GetImage(self) -> str:
            return self._image

        def GetBonusBlood(self) -> None:
            return 0
    
        def OnPlay(self, cardPlay: CardPlay) -> None:
            pass

        def OnSacrificed(self, sacrifice: Sacrifice) -> None:
            pass
    
        def OnAttack(self, attack: Attack) -> None:
            pass
    
        def OnHurt(self, hurt: Hurt) -> None:
            pass

        def OnDie(self, die: Die) -> None:
            pass


    class _Airborne(_Sigil):
        def __init__(self):
            super().__init__("AIRBORNE", "airborne.png")
    
        def OnAttack(self, attack: Attack) -> None:
            for sd in attack.GetStrikeData():
                sd.attacksDirectly = True

    class _MightyLeap(_Sigil):
        def __init__(self):
            super().__init__("MIGHTYLEAP", "mightyleap.png")
    
        def OnHurt(self, hurt: Hurt) -> None:
            hurt.GetStrikeData().attacksDirectly = False


    ## Record all sigils ##
    _sigils = {
      "AIRBORNE": _Airborne(),
      "MIGHTYLEAP": _MightyLeap()
    }

    @staticmethod
    def GetSigil(sigilName: str) -> SigilFactory._Sigil:
        return SigilFactory._sigils[sigilName.upper()]


      
## Cards ##
class CostType:
    Free = 0
    Blood = 1
    Bones = 2

class CardFactory:
    class _CardBase: #abstract
        def __init__(self, name: str, image: str, health: int, sigils: list[SigilFactory._Sigil], tribes: list[TribeFactory._Tribe], costType: int, costAmount: int):
            self._name = name
            self._image = image
            self._health = health

            self._sigils = []
            if sigils != None:
                self._sigils = sigils

            self._tribes = []
            if tribes != None:
                self._tribes = tribes

            if not isinstance(costType, int) or not (0 <= costType <= 2):
                raise TypeError("Cost must be 0, 1, or 2")
            self._costType = costType # 0=Nothing, 1=Blood, 2=Bone
            
            self._costAmount = costAmount


        def GetName(self) -> str:
            return self._name

        def GetImage(self) -> str:
            return self._image

        def GetHealth(self) -> int:
            return self._health

        def GetSigils(self) -> list[SigilFactory._Sigil]:
            return self._sigils.copy()

        def GetTribes(self) -> list[TribeFactory._Tribe]:
            return self._tribes.copy()

        def GetCostType(self) -> int:
            return self._costType

        def GetCost(self) -> int:
            if self._costType == 0:
                return 0
            return self._costAmount


    class _UnitCardBase(_CardBase):
        def __init__(self, name: str, image: str, health: int, sigils: list[SigilFactory._Sigil], tribes: list[TribeFactory._Tribe], costType: int, costAmount: int, power: int):
            super().__init__(name, image, health, sigils, tribes, costType, costAmount)
            self._power = power

        def GetPower(self) -> int:
            return self._power

        def GetCostType(self) -> int:
            return self._costType

        def GetCostAmount(self) -> int:
            if self._costType == 0:
                return 0
            else:
                return self._costAmount
        


    class _Card: #abstract
        def __init__(self, base: CardFactory._CardBase):
            self._base = base
            self._id = uuid.uuid4()
            
            self._health = self._base.GetHealth()
            self._buffs = [] #List of buffs

        def GetBase(self) -> CardFactory._CardBase:
            return self._base

        def GetId(self) -> uuid.UUID:
            return self._id

        def GetHealth(self) -> int:
            return self._health

        def IsDamaged(self) -> bool:
            return self._health < self._base.GetHealth()

        def Damage(self, amount: int) -> None:
            self._health = max(self._health-amount, 0)

        def GetSigils(self) -> list[SigilFactory._Sigil]:
            return self._base.GetSigils()

        def GetBlood(self) -> int:
            total = 1
            for s in self.GetSigils():
                total += s.GetBonusBlood()
            return total

        def __deepcopy__(self):
            return CardFactory.CreateCard(self._base.GetName())


    class _UnitCard(_Card):
        def __init__(self, base: CardFactory._UnitCardBase):
            super().__init__(base)
            self._power = self._base.GetPower()

        def GetPower(self) -> int:
            return self._power

    class _TerrainCard(_Card):
        def __init__(self, base: CardFactory._TerrainCardBase):
            super().__init__(base)


    _cardBases = {}
          
    # Get cards from cards.json #
    with open("cards.json","r") as f:
        cardData = json.load(f)
        for c in cardData["cards"]:
            name = c["name"].upper()
            image = c["image"]
            tribes = []
            if "tribes" in c:
              for tname in c["tribes"]:
                tribes.append(TribeFactory.GetTribe(tname))
            health = c["health"]
            sigils = []
            if "sigils" in c:
              for sname in c["sigils"]:
                sigils.append(SigilFactory.GetSigil(sname))
            #Unit Card
            if c["type"] == "unit":
                power = c["power"]
                costType = c["costType"]
                costAmount = 0
                if costType > 0:
                  costAmount = c["costAmount"]
                _cardBases[name] = _UnitCardBase(name, image, health, sigils, tribes, costType, costAmount, power)
            #Terrain Card
            elif c["type"] == "terrain":
                _cardBases[name] = _TerrainCardBase(name, image, health, sigils, tribes, costType, costAmount)


    @staticmethod
    def CreateCard(cardName: str) -> CardFactory._Card:
        cardBase = CardFactory._cardBases[cardName.upper()]
        if isinstance(cardBase, CardFactory._UnitCardBase):
            return CardFactory._UnitCard(cardBase)
        elif isinstance(cardBase, CardFactory._TerrainCardBase):
            return CardFactory._TerrainCard(cardBase)
        return None
