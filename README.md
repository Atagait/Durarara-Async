# Durarara Async
An asynchronous framework for building Durarara applications.

`on_message` is called whenever the DurararaAsync client processes a message.
The function called is passed a reference to the client, and the message.
`on_message(client, Message)`
The client's on_message function is set as so
`client.on_message = on_message`

`on_join` is passed the client, and the room it has joined.
`client.on_join = on_join`
`on_join(client, Room)`
