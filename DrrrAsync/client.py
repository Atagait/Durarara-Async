import traceback
import asyncio
import aiohttp
import regex
import random
import datetime
import objects

class DrrrClient:
    def __init__(self, Name=None, Icon=None):
        """Initializes variables related to the DrrrClient.
        It does not log the client in, but does initialize
        the asyncio session.

        :param Name: String, name to use when logging in.
        :param Icon: String, name of icon on the site.
        """
        self.session = aiohttp.ClientSession()
        self.name = Name
        self.icon = Icon

        self.user = None
        self.room = None

        self._login = False
        self._run = False

        self.on_message = None
        self.on_login = None
        self.on_join = None

        self._send_queue = []


    def IconList():
        """Returns a list of all the usable icons on drrr.com.
        """
        return ["setton","bakyura-2x","ya-2x","sharo-2x","kuromu-2x","kanra","kakka","kyo-2x","gg","junsui-2x","tanaka-2x","gaki-2x","kanra-2x","rotchi-2x","saki-2x","zaika","san-2x","zawa","bakyura","eight","zaika-2x","setton-2x","tanaka"]


    async def get_text(self, url):
        """Coroutine. A wrapper for asyncio to GET text given a url.
        :param url: String, url to get text from.
        """
        async with self.session.get(url) as response:
            return await response.text()


    async def get_json(self, url):
        """Coroutine. A wrapper for asyncio to GET json given a url.
        :param url: String, url to get json from.
        """
        async with self.session.get(url) as response:
            return await response.json()


    async def post(self, url, data):
        """Coroutine. A wrapper for asyncio to POST  given a url.
        Returns text.

        :param url: String, url to get json from.
        :param data: Dictionary of data.
        """
        async with self.session.post(url, data=data) as response:
            return await response.text()


    async def post_json(self, url, data):
        """Coroutine. A wrapper for asyncio to POST  given a url.
        returns JSON.

        :param url: String, url to get json from.
        :param data: Dictionary of data.
        """
        async with self.session.post(url, json=data) as response:
            return await response.text()


    async def Login(self, Username=None, Icon=None):
        """Coroutine. Logs into drrr.com
        :param Username: String, Username to use, if it hasn't been set.
        :param Icon: String, Icon to use, if it hasn't been set.
        """
        self.name = Username if self.name is None else self.name
        self.icon = random.choice(DrrrClient.IconList()) if self.icon is None else self.icon

        if self.name is None:
            raise ValueError("Username not set.")
        if self.name.strip() == "":
            raise ValueError("Username cannot be blank")

        Text = await self.get_text("https://drrr.com")
        Token = regex.findall(r"\"token\" data-value=\"(\w+)\"", Text)[0]
        await self.post("https://drrr.com", {"name":self.name, "login":"ENTER", "token":Token, "language":"en-US", "icon":self.icon})
        self._login = True
        Data = await self.Lounge()
        self.user = DrrrUser.FromDict(Data["profile"])
        if not self.on_login is None:
            await self.on_login(self, self.user)


    async def Lounge(self):
        """Coroutine. Gets the pure JSON for the lounge.
        """
        if not self._login:
            return AttributeError("Not logged in.")
        return await self.get_json("https://drrr.com/lounge?api=json")


    async def SearchForRoom(self, **kwargs):
        """Coroutine. Searches for a room on drrr's lounge.

        :param kwargs:
        id - the room's ID in the lounge
        name - the room's Name in the lounge
        """
        ID = kwargs.get("id")
        Name = kwargs.get("name")
        if ID is None and Name is None:
            raise ValueError("<id> or <name> must be provided.")

        LoungeData = await self.Lounge()
        for room in LoungeData['rooms']:
            if not ID is None:
                if room["roomId"] == ID:
                    return room
            elif not Name is None:
                if room["name"] == Name:
                    return room
        return None


    async def JoinRoom(self, Room):
        """Coroutine. Joins a room on drrr.com

        :param Room: String, the room's ID
        """
        await self.get_text("https://drrr.com/room/?id="+Room["roomId"])
        RoomData = await self.GetRoom()
        if not self.on_join is None:
            await self.on_join(self, RoomData)
        self.room = RoomData
        return RoomData


    async def MakeRoom(self, Name, Description, Limit, AdultRoom):
        """Coroutine. Creates a room on Drrr.com

        :param Name: String, The name of the room you want to make
        :param Description: String, The descripton of the room you want to make
        :param Limit: Integer, the number of users in the room.
        :param AdultRoom: Bool, whether or not to make it an adult room.
        """
        Payload = {
            "name":Name,
            "description":Description,
            "limit":Limit,
            "language":"en-US",
            "adult":"true" if AdultRoom else "false",
            "submit":"Create Room"
        }
        await self.post("https://drrr.com/create_room/?", Payload)

        Data = await self.get("https://drrr.com/json.php?fast=1")
        return await DrrrRoom.FromDict(Data)


    async def LeaveRoom(self):
        """Coroutine. Leaves a room on Drrr.com
        """
        await self.post("https://drrr.com/room/?ajax=1", {"leave":"leave"})


    async def GetRoom(self):
        """Coroutine. Gets all data for a room.
        """
        if not self._login:
            return AttributeError("Not logged in.")
        Data = await self.get_json("https://drrr.com/json.php?fast=1")
        return await DrrrRoom.FromDict(Data)


    async def SendMessage(self, message, **kwargs):
        """Coroutine. Adds a message to the sendmessage queue.
        :param message: a DrrrMessage object to send.
        :param kwargs: Optional
        reciever: DrrrUser, who should recieve the message
        url: a URL to be sent with the message.
        """
        Tmp = DrrrMessage()
        Tmp.message = message
        Tmp.reciever = kwargs.get("reciever")
        Tmp.content = kwargs.get("url")
        self._send_queue.append(Tmp)


    async def GiveHost(self, user : DrrrUser):
        """Coroutine. Gives host to a user.
        :param user: DrrrUser, who to give host to.
        """
        if not self.room is None:
            await self.post("https://drrr.com/room/?ajax=1", {"new_host":user.id})
            return True


    async def Kick(self, user : DrrrUser):
        """Coroutine. Gives host to a user.
        :param user: DrrrUser, who to kick
        """
        if not self.room is None:
            print(self.room.host.id, self.user.id)
            if self.room.host.id == self.user.id:
                await self.post("https://drrr.com/room/?ajax=1", {"kick":user.id})


    async def Ban(self, user : DrrrUser):
        """Coroutine. Gives host to a user.
        :param user: DrrrUser, who to ban
        """
        if not self.room is None:
            print(self.room.host.id, self.user.id)
            if self.room.host.id == self.user.id:
                await self.post("https://drrr.com/room/?ajax=1", {"ban":user.id})


    async def _update_room(self):
        """Coroutine. Handles fetching data for the room, and calling the on_message callback.
        """
        while self._run:
            if not self.room is None:
                Data = await self.get_json("https://drrr.com/json.php?update="+str(self.room.update))
                Data = await self.room._Update(Data)
                try:
                    for Mesg in Data:
                        if not self.on_message is None:
                            await self.on_message(self, Mesg)
                except Exception as E:
                    print("r", "ERROR", str(E))
                    traceback.print_tb(E.__traceback__)
            await asyncio.sleep(0.5)


    async def _proc_messages(self):
        """Coroutine. Handles sending messages from the message queue.
        """
        LastMsg = datetime.datetime.now()
        while self._run:
            if not self.room is None:
                if len(self._send_queue) > 0:
                    Msg = self._send_queue.pop(0)
                    payload = {
                        "message":Msg.message,
                        "to":"" if Msg.reciever is None else Msg.reciever.id,
                        "url":"" if Msg.content is None else Msg.content.strip()
                    }
                    await self.post("https://drrr.com/room/?ajax=1", payload)
                    LastMsg = datetime.datetime.now()
                Delta = datetime.datetime.now() - LastMsg
                if Delta.total_seconds() > (10*60):
                    await self.SendMessage("[HEARTBEAT]", reciever=self.user)
            await asyncio.sleep(0.5)


    async def Run(RoomName):
        """Coroutine. Handles joining a room, and starting _update_room and _proc_messages
        I suggest using this as a template for your own scripts.

        :param RoomName: String, the name of the room the client should join.
        """
        await client.Login()
        data = await client.SearchForRoom(name=RoomName)
        if data is None:
            raise AttributeError("Room not found.")
        else:
            await client.JoinRoom(data)

        client._run = True

        await asyncio.gather(
            client._update_room(),
            client._proc_messages(),
        )
