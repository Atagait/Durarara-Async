import asyncio

class DrrrUser:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.id = kwargs.get("id")
        self.icon = kwargs.get("icon")
        self.tripcode = kwargs.get("tripcode")
        self.device = kwargs.get("device")


    @classmethod
    def FromDict(cls, Dictionary):
        if Dictionary is None:
            return None
        Tmp = DrrrUser()
        Tmp.name = Dictionary.get("name")
        Tmp.id = Dictionary.get("id")
        Tmp.icon = Dictionary.get("icon")
        Tmp.tripcode = Dictionary.get("tripcode")
        Tmp.device = Dictionary.get("device")
        return Tmp


class DrrrMessage:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.type = kwargs.get("type")
        self.time = kwargs.get("time")
        self.message = kwargs.get("message")
        self.music = kwargs.get("music")
        self.content = kwargs.get("content")
        self.direct = False if kwargs.get("secret") is None else True
        self.host = kwargs.get("host")
        self.author = DrrrUser.FromDict(kwargs.get("from"))
        self.author = DrrrUser.FromDict(kwargs.get("user")) if not kwargs.get("user") is None else self.author
        self.reciever = DrrrUser.FromDict(kwargs.get("to"))

    @classmethod
    async def FromDict(cls, Dictionary):
        Tmp = DrrrMessage()
        Tmp.id = Dictionary.get("id")
        Tmp.type = Dictionary.get("type")
        Tmp.time = Dictionary.get("time")
        Tmp.message = Dictionary.get("message")
        Tmp.music = Dictionary.get("music")
        Tmp.content = Dictionary.get("content")
        Tmp.direct = Dictionary.get("secret")
        Tmp.host = Dictionary.get("host")
        Tmp.author = DrrrUser.FromDict(Dictionary.get("from"))
        Tmp.author = DrrrUser.FromDict(Dictionary.get("user")) if not Dictionary.get("user") is None else Tmp.author
        Tmp.reciever = DrrrUser.FromDict(Dictionary.get("to"))
        return Tmp



class DrrrRoom:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.id = kwargs.get("roomId")
        self.description = kwargs.get("description")
        self.opened = kwargs.get("since")
        self.update = kwargs.get("update")
        self.limit = kwargs.get("limit")
        self.language = kwargs.get("language")
        self.music = kwargs.get("music")
        self.publicMusic = kwargs.get("djMode")
        self.adult = kwargs.get("adultRoom")
        self.host = kwargs.get("host")
        self.users = kwargs.get("users")
        self.messages = kwargs.get("messages")


    @classmethod
    async def FromDict(cls, Dictionary):
        Tmp = DrrrRoom()
        Tmp.name = Dictionary.get("name")
        Tmp.id = Dictionary.get("roomId")
        Tmp.description = Dictionary.get("description")
        Tmp.opened = Dictionary.get("since")
        Tmp.update = Dictionary.get("update")
        Tmp.limit = Dictionary.get("limit")
        Tmp.language = Dictionary.get("language")
        Tmp.music = Dictionary.get("music")
        Tmp.publicMusic = Dictionary.get("djMode")
        Tmp.adult = Dictionary.get("adultRoom")

        Tmp.host = Dictionary.get("host")
        Tmp.host = [User for User in Dictionary.get("users") if User["id"] == Tmp.host]
        Tmp.host = DrrrUser.FromDict(Tmp.host[0])

        Tmp.users = []
        for User in Dictionary.get("users"):
            Tmp.users.append(DrrrUser.FromDict(User))

        Tmp.messages = []
        for Msg in Dictionary.get("talks"):
            Msg["host"] = Tmp.host
            Tmp.messages.append(await DrrrMessage.FromDict(Msg))

        return Tmp


    async def _Update(self, Data):
        self.name = Data.get("name")
        self.description = Data.get("description")
        self.publicMusic = Data.get("djMode")
        self.adult = Data.get("adultRoom")

        if not Data.get("users") is None:
            for User in Data.get("users"):
                self.users.append(DrrrUser.FromDict(User))

        if not Data.get("host") is None:
            self.host = Data.get("host")
            self.host = [User for User in self.users if User.id == self.host]
            self.host = self.host[0]

        NewMessages = []
        if not Data.get("talks") is None:
            for Msg in Data.get("talks"):
                Msg["host"] = self.host
                Tmp = await DrrrMessage.FromDict(Msg)
                if [msg for msg in self.messages if msg.id == Tmp.id] == []:
                    self.messages.append(Tmp)
                    NewMessages.append(Tmp)
        return NewMessages


    async def Get_User(self, **kwargs):
        ID = kwargs.get("id")
        Name = kwargs.get("name")
        if ID is None and Name is None:
            raise ValueError("<id> or <name> must be provided.")
        for user in self.users:
            if not ID is None:
                if user.id == ID:
                    return user
            elif not Name is None:
                if user.name == Name:
                    return user
