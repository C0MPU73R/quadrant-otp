from panda3d.core import QueuedConnectionListener, QueuedConnectionManager, QueuedConnectionReader, ConnectionWriter, PointerToConnection, NetAddress
from direct.task.Task import Task

from lib.logging.Logger import Logger


class Listener(QueuedConnectionManager):
    logger = Logger("network_listener")

    def __init__(self, host_addr, port, backlog=10000):
        self.host_addr = host_addr
        self.__port = port
        self.backlog = backlog  # if we're ignoring 10000 connection attempts, something is going wrong

        self.server_sock = None
        self.active_connections = []

        self.listen_task = None
        self.read_task = None

        QueuedConnectionManager.__init__(self)
        self.qcl = QueuedConnectionListener(self, 0)
        self.qcr = QueuedConnectionReader(self, 0)
        self.cw = ConnectionWriter(self, 0)

    def configure(self):
        if self.server_sock is None:
            try:
                self.server_sock = self.openTCPServerRendezvous(self.host_addr, self.__port, self.backlog)
                self.qcl.addConnection(self.server_sock)
            except:
                raise Exception("unable to open socket at %s-%s" % (self.host_addr, str(self.port)))

        self.listen_task = taskMgr.add(self.poll_incoming_connections, "poll-suggestions")
        self.read_task = taskMgr.add(self.poll_incoming_data, "poll-data")

    def poll_incoming_connections(self, task):
        if self.qcl.newConnectionAvailable():
            rendezvous = PointerToConnection()
            net_addr = NetAddress()
            new_conn = PointerToConnection()

            if self.qcl.getNewConnection(rendezvous, net_addr, new_conn):
                new_conn = new_conn.p()
                self.active_connections.append(new_conn)  # remember the connection
                self.qcr.addConnection(new_conn)  # begin reading the connection
                self.logger.warn("new connection from %s" % net_addr)

        return Task.cont

    def poll_incoming_data(self, task):
        if self.qcr.dataAvailable():
            dg = NetDatagram()
            if self.qcr.getData(dg):
                self.handle_data(dg)

        return Task.cont

    def handle_data(self, dg):
        # TODO - handle data
        pass