import random


class Mesh:
    """This class handles the high level structure of the mesh simulation, including all nodes and links it contains.

    Summary:
    The main purpose of the Mesh class is to act as a container for all node and connection data as well as acting
    as the nexus for simulating the network itself. In addition, all link failures are tracked at the Mesh level,
    represented as a list of a pair of strings containing the node IDs where the link has failed.

    The class has four main parts: initialization, simulation, messaging, and link handling. Initialization parses
    JSON data to create the mesh network itself, making new Node objects and tracking the topology of the network.
    Simulation is handled mainly via the run() function with several helper functions allowing for modifications
    to the simulation. Messaging is primarily via the update() function and collects a set of messages indicating
    what has occurred in the network. Finally link handling is used to enable or disable links and notify nodes
    whether or not a particular link can be traveled on.

    Public methods:
    update(msg, node=None)
    restore()
    toggle_link(node0, node1)
    link_status(node0, node1)
    generate_topology()
    get_links()
    run()
    rand_fail(fail_type="node", fail_chance=100)
    set_rand_fail(fail_type="node", fail_chance=0)

    Private methods:
    __generate_mesh(json_mesh)
    """

    def __init__(self, mesh, node_fail=0, link_fail=0):
        """Initializes a new Mesh object and requires raw JSON data to build nodes."""
        self.mesh = {}
        """A dictionary that will contain all mesh IDs as the key value and a list of all links as a data value."""
        self.dead_links = []
        """A list of all links that are currently disabled in 2 element tuples, i.e. ('0', '1')."""
        self.__generate_mesh(mesh)
        self.tick = 0
        """The current tick, representing timing, of the mesh simulation."""
        self.actions = []
        """A list containing all actions that happened on the previous tick via the update() function."""
        self.fail_chances = {
            "node": node_fail,
            "link": link_fail
        }
        """The current fail chances for links and nodes in the mesh, checked randomly each tick of the simulation."""
        self.hops = []
        """A list of completed packet hop (number of transmissions to reach destination) values."""
        self.congestion = []
        """A list of congestion (average buffer size) values per tick."""
        self.errors = 0
        """A counter of the total number of failed transmissions over the simulation."""
        self.unreached = 0
        """A counter of the total number of packets that were unable to reach their destination."""
        self.round_trip = 0
        """A counter of the total number of packets able to reach destination and return acknowledgement to origin."""

    def __getitem__(self, item):
        """Allows indexing of mesh from object."""
        return self.mesh[item]

    def update(self, msg, node=None):
        """Appends a string detailing an event to the actions list.

        Parameters:
            :param msg The message to append.
            :param node The node this update applies to. If None, will apply to mesh instead.
        """
        self.actions.append(f"{self.tick}-{'Node ' if node else 'Mesh'}{node if node else ''}: {msg}")

    def restore(self):
        """Restores all links and nodes (but not tick value)."""
        self.dead_links.clear()
        for node in self.mesh:
            self.mesh[node].status = True
        self.update("Restored all links and nodes")

    def __generate_mesh(self, json_mesh):
        """Creates the underlying mesh data structures.

        Parameters:
            :param json_mesh: The mesh data in parsed JSON data from the json.loads() function.
        """
        for node in sorted(json_mesh.items()):
            # Creates a new item with an ID equal to its key in the mesh containing a list of all links
            self.mesh[node[0]] = Node(node[0], node[1], self)

    def toggle_link(self, node0, node1):
        """Toggles a dead link into the mesh (tuple containing IDs of both ends of link).

        Details:
            - The order does not matter between node0 and node1 as links will be checked in both directions.
            - There is no error checking on whether or not an actual link exists between the nodes. If an invalid
                link is added it will simply never fail.

        Parameters:
            :param node0: The first node in the link.
            :param node1: The second node in the link.
        """
        # Toggle links by adding if it doesn't currently exist in list, otherwise remove from list
        link = (node0, node1)
        r_link = (node1, node0)
        if link in self.dead_links:
            self.dead_links.remove(link)
            self.update(f"Link {link} is now working")
        elif r_link in self.dead_links:
            self.dead_links.remove(r_link)
            self.update(f"Link {r_link} is now working")
        else:
            self.dead_links.append(link)
            self.update(f"FAIL: Link {link} failed")

    def link_status(self, node0, node1):
        """Checks if a link is active, returns true if active, false otherwise."""
        return (node0, node1) not in self.dead_links and (node1, node0) not in self.dead_links

    def generate_topology(self):
        """Generates topology for entire mesh by iterating through all node topology functions."""
        self.update("Generating mesh topology...")
        for node in self.mesh:
            self.mesh[node].generate_topology()

    def get_links(self):
        """Returns a list of all unique links in mesh."""
        links = []
        for node in self.mesh:
            for connection in self.mesh[node].links:
                # Check if link already exists
                if (node, connection) not in links and (connection, node) not in links:
                    links.append((node, connection))    # Add a tuple of the connection
        return links

    def get_average_buffer(self):
        """Returns the average buffer size across the mesh, ignoring empty nodes."""
        sizes = []
        for node in self.mesh:
            size = len(self.mesh[node].buffer)
            if size >= 1:
                sizes.append(size)
        if len(sizes) == 0:     # Check if there is nothing else in the buffer, if so, return -1
            return -1.0
        return sum(sizes) / len(sizes)

    def run(self, never_fail=None):
        """Runs all nodes on the mesh, keeping track of ordering to simulate simultaneous action."""
        # Update time if actions occurred last run and store metrics for buffer sizes
        if not never_fail:
            never_fail = []
        if self.actions:
            self.tick += 1
            self.save("congestion", self.get_average_buffer())
        # Clear all events:
        self.actions.clear()
        # Run fail chances if set
        for fail_type in ("node", "link"):
            if self.fail_chances[fail_type] > 0:
                self.rand_fail(fail_type, self.fail_chances[fail_type], never_fail)
        # Run all nodes, skipping anything that received a packet
        for node in self.mesh:
            self.mesh[node].run()

    def rand_fail(self, fail_type="node", fail_chance=100, never_fail=None):
        """Causes a random failure in a specific type with a specific chance.

        Parameters:
            :param fail_type The type of failure to generate, can be 'node' or 'link'
            :param fail_chance The percent chance of failure.
            :param never_fail A list of nodes to never cause failures in.
        """
        if not never_fail:
            never_fail = []
        roll = random.randint(1, 100)
        if roll <= fail_chance:
            # Get a random node
            rand_node = random.choice(list(self.mesh.keys()))
            # Check if this is a non-fail option
            if rand_node in never_fail:
                return
            if fail_type == "node":
                # If type is node, just disable the node if it's up, otherwise re-enable
                target = self.mesh[rand_node]
                if target.status:
                    target.status = False
                    self.update(f"FAIL: Node {rand_node} has failed.")
                else:
                    target.status = True
                    self.update(f"Node {rand_node} has been restored.")
            else:
                # Otherwise, pull a random link node from the random node and disable or enable that link
                rand_link = random.choice(self.mesh[rand_node].links)
                self.toggle_link(rand_node, rand_link)

    def set_rand_fail(self, fail_type="node", fail_chance=0):
        """Sets the random failure chance values for the mesh.

        Parameters:
            :param fail_type The type of failure chance to set, can be 'node' or 'link'
            :param fail_chance The percent chance of failure.
        """
        if fail_type == "node":
            self.fail_chances["node"] = fail_chance
        else:
            self.fail_chances["link"] = fail_chance

    def save(self, metric, value=1.0):
        """Saves a metric to the mesh for analysis.

        Parameters:
            :param metric A string that determines what is going to be adjusted.
            :param value For hops and congestion, this is the calculated value to add. For everything else
                         each call of save will add 1 and value is not used.
        """
        if metric == "hops":
            self.hops.append(value)
        elif metric == "congestion":
            self.congestion.append(value)
        elif metric == "errors":
            self.errors += 1
        elif metric == "unreached":
            self.unreached += 1
        elif metric == "round_trip":
            self.round_trip += 1

    def print_metrics(self):
        """Displays all current metrics in the mesh."""
        print("Metrics")
        print("-------")
        print(f"Total ticks: {self.tick}")
        print(f"Node failure chance: {self.fail_chances['node']}")
        print(f"Link failure chance: {self.fail_chances['link']}")
        print(f"Hops: {len(self.hops)}")
        # print(f"Congestion: {self.congestion}")
        print(f"Average hops: {sum(self.hops) / len(self.hops) if len(self.hops) > 0 else 1}")
        print(f"Average congestion: {sum(self.congestion) / len(self.congestion) if len(self.congestion) > 0 else 1}")
        print(f"Total errors: {self.errors}")
        print(f"Total packets unable to reach destination: {self.unreached}")
        print(f"Total received acknowledgements: {self.round_trip}")
        print("-------")

    def print_average_topology_size(self):
        """Prints the average topology size."""
        val = 0
        for node in self.mesh:
            print(node)
            val += len(self.mesh[node].topology)
        avg = val/len(self.mesh)
        print("The average topology size is: ", avg)
        print(len(self.get_links()))


class Packet:
    """This class represents a data packet that is transmitted through a network.

    Summary:
    This class is purely data driven. From a design standpoint the packet should be run entirely by nodes and should
    simply be used as the basis for routing. The one function exists primarily for debug purposes.
    """

    def __init__(self, packet_type, source, destination, data=None):
        """Initialize the Packet class object.

        Parameters:
            :param packet_type A string representing the type of packet, currently 'data' or 'ACK'
            :param source A string containing the ID of the packet's source Node (where it originated)
            :param destination A string containing the ID of the packet's destination Node (where it should stop)
            :param data Usually a string, this data object is not actually used for anything specifically,
                        but is represented as the data the packet is carrying.
        """
        self.data = data
        """The data the Packet is carrying."""
        self.packet_type = packet_type
        """The type of packet ('data' or 'ACK')."""
        self.source = source
        """The ID of the packet's source."""
        self.destination = destination
        """The ID of the packet's destination."""
        self.routing = []
        """Used to represent the current routing path once calculated."""
        self.path = []
        """List of nodes already routed over."""

    def __repr__(self):
        """String representation of packet for debugging."""
        return f"Data: {self.data}, Type: {self.packet_type},  Source: {self.source}, " \
               f"Destination: {self.destination}, Routing: {self.routing}, Path: {self.path}"


class Node:
    """This class represents a Node, such as a router, in a Mesh network.

    Summary:
    The Node is where most of the calculation for routing occurs and the driver of packet transmission. Each node
    keeps track of its own status, a list of all connected nodes (whether or not they are currently accessible),
    and the potential routes to all other nodes in the Mesh. If a failure occurs, the node at the point of failure
    is responsible for rerouting the packet to try and get it to its destination.

    From a design standpoint, the Node has no information on the Mesh status other than what it attempts, so if another
    node or link goes down somewhere else in the Mesh the current Node has no way to tell. All routing calculation
    and methods are designed around this systemic ignorance. As such, the algorithm will not necessarily find the
    'best' theoretical path under all circumstances, as a failure further down the line might be obscured. It will,
    however, always find a path to the target if one exists.

    Public methods:
    update(msg)
    generate_packet(packet_type, destination, data=None)
    generate_topology()
    run()
    print_buffer()
    print_links()
    print_topology()

    Private methods:
    __transmit_packet(target, packet=None)
    __receive_packet(packet, generated=False)
    __find_route(packet)
    __in_path(path)
    __generate_routes(routes, node, path)
    __process_packet(packet)
    __send_packet(packet)
    """

    def __init__(self, node_id, links, mesh):
        """Node class constructor.

        Parameters:
            :param node_id The ID of this object, usually a string.
            :param links A list of all connected node IDs.
            :param mesh A reference to the mesh this node is a member of.
        """
        self.node_id = node_id
        """A string representing the 'name' or ID of the node (must be unique)"""
        self.status = True
        """Boolean value representing whether this node is currently working"""
        self.received = False
        """Flag for receiving packets to avoid ordering issues, if true, will skip processing this tick.
        
        The detailed reason for this is that the Mesh run() command works sequentially through the nodes but
        transmission happens instantly. Therefore you'd get different behavior if transmitting to a node lower
        on the list than on one higher. By flagging the receiver it doesn't matter where they are on the list;
        in both cases the packet will not be processed until next tick. This causes an extra bit of delay pretty
        much all the time but this is generally handled via the Mesh run() command and is only noticeable when
        manually triggering the run() command.
        """
        self.links = links
        """A list of node IDs this object is linked to."""
        self.mesh = mesh
        """A reference back to the parent mesh object, primarily used for checking links and sending updates."""
        self.topology = []
        """A list containing all possible paths to other nodes in a mesh. Increases in size exponentially."""
        self.buffer = []
        """A list of Packet objects currently pending processing. Works on a 'First In, First Out' ordering."""
        self.failed = []
        """Contains list of attempted links for routing purposes."""

    def __repr__(self):
        """Representation of the node for debug purposes."""
        return f"ID: {self.node_id}, status: {self.status}"

    def update(self, msg):
        """Saves update message for current run.

        Parameters:
            :param msg: The message to save.
        """
        self.mesh.update(msg, self.node_id)

    def generate_packet(self, packet_type, destination, data=None):
        """Generates a new packet with a source of this node.

        Parameters:
            :param packet_type: The type of packet, either 'data' or 'ACK'.
            :param destination: The destination ID of the new packet.
            :param data: The data to be assigned to the packet.
        """
        new_packet = Packet(packet_type, self.node_id, destination, data)
        # Create initial routing
        new_packet.routing = self.__find_route(new_packet)
        # Add to buffer using receive function
        self.__receive_packet(new_packet, True)

    def __transmit_packet(self, target, packet=None):
        """Attempts to transmit a packet over a link.

        Parameters:
            :param target The node ID of the node to send to.
            :param packet The Packet object to transmit. If None will attempt to send packet on top of buffer.

        :return Returns True if transmission is successful, False otherwise.
        """
        # Handle None packet values, try to take from top of buffer, otherwise return false
        if not packet and len(self.buffer) > 0:
            packet = self.buffer[0]  # Default to top of buffer if not empty
        elif not packet:
            return False
        # Check for self-send
        if target == self.node_id:
            self.__receive_packet(packet)
            return True

        self.update(f"Attempting to send packet to node {target}")

        # Check if link is valid and active
        if target not in self.links:
            self.update(f"FATAL ERROR: routing link does not exist from self to {target}!")
            return False
        if not self.mesh.link_status(self.node_id, target):
            self.failed.append((self.node_id, target))  # Add tuple representing down link to avoid status
            self.update(f"FAIL: node {target} could not be reached")
            self.mesh.save("errors")
            return False

        # Link is valid, attempt to transmit
        if not self.mesh[target].__receive_packet(packet):
            # If target status is down, add status flag and return false (timeout)
            # NOTE: This appends the same thing as the link failure, the reason is because
            #       this node has no way of knowing if the link or node is actually down
            self.failed.append((self.node_id, target))
            self.update(f"FAIL: node {target} could not be reached")
            self.mesh.save("errors")
            return False
        # Packet successfully submitted
        # If packet sent successfully add action to list
        self.update(f"Successfully transmitted packet '{packet}'")
        return True

    def __receive_packet(self, packet, generated=False):
        """Receives a packet from another source or self, returns success.

        Parameters:
            :param packet The packet to receive.
            :param generated Boolean flag to detect whether or not this node is the origin of the call.

        :return True if packet is received successfully, False if the node is down.
        """
        if self.status:
            packet.path.append(self.node_id)    # Add self to path
            self.buffer.append(packet)
            if not generated:
                self.received = True  # Flag that this node just received a packet
                self.update(f"Successfully received packet '{packet}'")
            else:
                self.update(f"Created new packet '{packet}'")
            return True
        else:
            self.update(f"Failed to receive packet '{packet}', node down")
            return False

    def __find_route(self, packet):
        """Finds a route for a packet to a destination.

        Summary:
        Path found: returns the route between current node and packet destination
        i.e. path from node 0 (self) to destination 2 = ["0", "1", "2"] if all connected
        Route to self: returns a list containing self, i.e. path from node 0 to node 0 = ["0"]
        No route: if no route can be made between nodes returns an empty list = []

        Parameters:
            :param packet The packet object to find a route for.
        """
        length = 2  # Any route is going to be at least length for two elements
        max_length = 0
        route = []
        alternate = []
        found = False
        # Check if packet is routed to self, if so, return a single element list with self
        if packet.destination == self.node_id:
            return [self.node_id]
        # Loop through all paths, checking the shortest first, then continuing to longer paths
        while not found:
            for path in self.topology:
                # Generate max length to avoid infinite loops
                if len(path) > max_length:
                    max_length = len(path)
                # Find the first shortest path where destination is last element
                # Also check to make sure path doesn't include something already traveled
                if len(path) == length and path[-1] == packet.destination and not self.__in_path(path)\
                        and not (set(path[1:]) & set(packet.path)):
                    # Set route to path, break out of for and while loops
                    route = path
                    found = True
                    break
                # Check for an alternate path backwards in case no other path is found
                elif len(path) == length and path[-1] == packet.destination and not self.__in_path(path):
                    alternate = path
            # Search the next highest size
            length += 1
            # If still searching and we've already checked longest possible paths, break
            # and return an empty route
            if length > max_length:
                break
        # Use an alternate route if necessary
        repeated = False
        if not route and alternate:
            # Break if path includes same location multiple times
            for node in packet.path:
                if packet.path.count(node) > 1:
                    repeated = True
                    break
            if not repeated:
                route = alternate
        return route

    def __in_path(self, path):
        """Checks if any element of a path is in an avoidance list.

        Summary:
        avoid: can contain tuples representing a link between two nodes or a string
        representing a single node in a list, i.e.:
        ["1", "2"] = avoids nodes 1 and 2
        [("1", "2"), ("3", "4")] = avoids link between 1 and 2 and also link between 3 and 4
        [("1", "2"), "3"] = avoid link between 1 and 2 and any link passing through 3

        Parameters:
            :param path The path to compare
        """
        # First check if failure list is empty, if so, path is good
        if not self.failed:
            return False
        # Next check for node avoidance by seeing if any element of path is part
        # of the path, which means a node has been found
        for element in self.failed:
            if element in path:
                return True
        # Finally check tuples for links that fail (use both directions)
        for index in range(len(path) - 1):  # Use range(len( instead of path directly to get indexes for making tuples
            if (path[index], path[index + 1]) in self.failed or (path[index + 1], path[index]) in self.failed:
                return True
        # If none of that is found, then the path has no elements of avoid
        return False

    def generate_topology(self):
        """Generates topology for the node by sending packets."""
        path = [self.node_id]   # Start path with self
        node = self.node_id     # Start with self as first node to check
        self.__generate_routes(self.topology, node, path)   # Recursively generates routes

    def __generate_routes(self, routes, node, path):
        """Recursively generates all possible routes."""
        for link in self.mesh[node].links:
            # Create a temporary path adding this link to the existing path
            new_path = path + [link]
            # Only continue if the new path has not already been created and
            # if the next node has not already been traveled on (no looping paths)
            if new_path not in routes and link not in path:
                # If it's a new path, append this path to the set of routes
                routes.append(new_path)
                # Recursively create new links for the next nodes in the path
                # it will recurse until the whole
                # Exactly like Djikstra except the distance between every single node is 1
                # creating every single possible path
                self.__generate_routes(routes, link, new_path)

    def __process_packet(self, packet):
        """Runs node processing on packet

        Parameters:
            :param packet The packet to process.
        """
        # Check for data node
        if packet.packet_type == "data":
            # Check if final location
            if packet.destination == self.node_id:
                # Create return packet
                self.generate_packet("ACK", packet.source)
                # Save number of hops
                self.mesh.save("hops", len(packet.path) - 1)
                return True
            else:
                return self.__send_packet(packet)
        # Handle ACK packets (acknowledgement)
        elif packet.packet_type == "ACK":
            # Check for original location
            if packet.destination == self.node_id:
                self.update(f"Acknowledgement packet has returned to {packet.destination}")
                # Increment successful return value
                self.mesh.save("round_trip")
                return True
            else:
                return self.__send_packet(packet)

    def __send_packet(self, packet):
        """Sends a packet along its route, creating a new route if necessary

        Parameters:
            :param packet The packet to send.
        """
        if not packet.routing:
            packet.routing = self.__find_route(packet)
        # next_hop is the index one after the index of the current path,
        # i.e. if packet.path = ['0', '1'] and packet.routing = ['0', '1', '2', '3']
        # then packet.path[-1] equals '1', and the index of packet.routing at '1'
        # is 1, then add 1 to get an index of 2, which returns '2' for next hop
        next_hop = packet.routing[
            packet.routing.index(packet.path[-1]) + 1
        ]
        return self.__transmit_packet(next_hop, packet)

    def run(self):
        """This command runs the default processing for packets"""
        # Clear any previous run's avoidance list
        self.failed.clear()
        # Check for empty buffer (no processing)
        if not self.buffer:
            return True
        # Check for node status (don't run if status is down)
        if not self.status:
            return False
        # Skip packet processing if already received
        if self.received:
            self.received = False   # Reset flag for next run
            return True
        # Process top packet in buffer
        packet = self.buffer[0]
        check = False
        # Attempt to send packet along route, if it fails, seek new route
        while not check:
            check = self.__process_packet(packet)
            # Ensure maximum avoidance has not been reached
            if not check:
                packet.routing = self.__find_route(packet)
                if not packet.routing:
                    self.update(f"FAIL: Cannot find valid route for packet '{packet}'")
                    # Also update unreachable metric
                    self.mesh.save("unreached")
                    break
        # Once sent or failed, clear packet from buffer
        self.buffer.pop(0)
        return True

    def print_buffer(self):
        """DEBUG: Prints out the packet buffer."""
        if len(self.buffer) == 0:
            print(f"Node {self.node_id}: buffer empty")
        else:
            print(f"Node {self.node_id} buffer:")
            for index, buff in enumerate(self.buffer):
                print(f"    {index}-{buff}")

    def print_links(self):
        """DEBUG: Prints out all links attached to this node."""
        if len(self.links) == 0:
            print(f"Node {self.node_id}: links empty")
        else:
            print(f"Node {self.node_id} links:")
            for link in self.links:
                print(f"    {link}")

    def print_topology(self):
        """DEBUG: Prints the raw topology data"""
        if len(self.topology) == 0:
            print(f"Node {self.node_id}: topology empty")
        else:
            print(f"Node {self.node_id} topology: {self.topology}")
            print(f"Total: {len(self.topology)}")

