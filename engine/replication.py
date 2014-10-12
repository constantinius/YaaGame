
class AbstractReplicationMessage(object):
    pass
    
class ObjectCreateMessage(AbstractReplicationMessage):
    pass

class ObjectDeleteMessage(AbstractReplicationMessage):
    pass

class ObjectUpdateMessage(AbstractReplicationMessage):
    pass

class PingMessage(AbstractReplicationMessage):
    pass
    
class PongMessage(AbstractReplicationMessage):
    pass

class ReplicationClientService(AbstractService):
    """
    The ReplicationClientService is responsible to replicate certain
    game objects over a network to the server and/or other clients.
    TODO: implement
    """
    
    priority = 5
    
    def __init__(self, connection = ("localhost", 12345)):
        self.messages = []
        # TODO set up client
        
    def on_tick(self, dt):
        """
        Send contents of objects this client/server has authority over.
        Receive contents of other objects and update them.
        """
        
        # TODO receive from server
        # deserialize messages
        # loop messages
        # if msg.type == object update:
        # get object by ID and set attributes
        
        # check for dirty objects
        # serialize objects
        # append to messages
        # TODO send all messages to the server
        
        pass
    
    def on_object_added(self, obj):
        """
        Check if the object is to be replicated (i.e: has the 'local'
        attribute). If it is a locally created object (local=True) it 
        is to be replicated to the server.
        """
        try:
            if obj.local:
                self.messages.append(('c', obj.id, obj.serialize()))
        except AttributeError: pass # not a replicable object
        
    def on_object_removed(self, obj):
        """
        Check if the object is replicated (see 'on_object_added') and
        whether or not it is a local object. If it is a local object
        it needs to be destroyed on the server and on other clients
        too, thus a destroy message needs to be sent.
        """
        try:
            if obj.local:
                self.messages.append(('d', obj.id))
        except AttributeError: pass # not a replicable object
    
