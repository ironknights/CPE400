# CPE400-Project
Fall 2019 CPE400 Project

# Summary:
Assignment #4
This project creates a simulated mesh network and attempts to route packets from different nodes. During execution, various nodes and links can fail, forcing the network to reroute around the faulty component.

# Compilation / Execution Instructions

**Distribution File List**:

* main.py
* mesh.py

Project was written for Python 3.8 but should compile on Python 3+ without issues. It will *not* compile on Python 2.7 or earlier.

The file to execute with python3 is main.py. Attempting to run mesh.py will not execute as it only contains class definitions used by main.py.

The only import files other than the modules in this distribution are the default Python json and random modules which should be included with all standard Python installations. The program has been tested on both Windows and Macintosh computers but was not tested on Linux, however, there is no reason it should fail to run on a standard Python installation. 

# Test Mesh
Basic mesh format is shown below:
![test_mesh](https://user-images.githubusercontent.com/28155794/68997800-4160ce00-085f-11ea-966d-15e09c93da89.png)

Throughput testing mesh is shown below (3rd option):
![Throughput Mesh](https://user-images.githubusercontent.com/28155794/70180195-61342680-1694-11ea-8d96-5e2c2c8ee380.png)

## Objects:

### Mesh

_Summary_: Contains all data for a mesh network

#### Data Structures

JSON: The JSON for meshes are as follows:
```json
{
  "Node_ID": ["Link_ID", "Link_ID", "..." "Link_ID"],
  "Node_ID": ["Link_ID", "Link_ID", "..." "Link_ID"],
  "..."
  "Node_ID": ["Link_ID", "Link_ID", "..." "Link_ID"]
}
```
**mesh**: Dictionary containing all nodes with their name as key
**dead_links**: List of tuples containing any dead links
**debug_mode**: Bool (default true) indicating whether verbose feedback should be used
**packet_types**: List of strings containing all valid packet types for user input in selection menus (constant value)

#### Functions

**debug(self, msg)**: Generates verbose messages depending on whether debug_mode is True or False

**__generate_mesh(self, json_mesh)**: Creates program data structures based on JSON data

**toggle_link(self, node0, node1)**: Togles a link between node0 and node1 (string names of nodes). If the link is not disabled, adds a tuple containing the link to dead_links, otherwise it removes the tuple from dead_links (enabling the link)

**generate_topology(self)**: Generates topology data for all nodes in the mesh

**list get_links(self)**: Returns a list of all possible links in the mesh. This is one way only, so if node "0" and node "1" are linked it will only generate a tuple in the list of ('0', '1'), it will not also generate ('1', '0')

**run(self)**: Runs processing on all nodes in the mesh

### Packet

_Summary_: Packets are data only and contain only data structures which nodes use to route them appropriately.

#### Data Structures

**data**: Actual contents of packet

**packet_type**: Type of packet (data, ACK)

**source**: ID of packet origin

**destination**: ID of packet target

**routing**: List of node IDs describing route to destination

**path**: The current path of the node

### Node

_Summary_: A node or router within the mesh, responsible for the routing and rerouting of packets through the network, as well as sending acknoweledgements.

#### Data Structures

**node_id**: The string identification of this node.

**status**: Boolean value indicating whether or not the the node is faulty or operating.

**received**: Boolean value indicating whether or not the node received a new packet this run cycle for concurrence

**links**: List of all node IDs this node is connected to

**topology**: A list of all possible routes to other nodes in the mesh

**buffer**: A list of all packets currently in line for processing in the node

**failed**: A list of all links that have already been tried on transmit

#### Functions

**bool transmit_packet(self, target, packet=None)**: This function takes two parameters: the target node to send a packet to, and the packet object to send. It attempts to send the packet over the link, and checks for either an ACK return or timeout. On timeout it returns false, otherwise true. If no packet is provided attempts to send the top packet of the current buffer.

**bool receive_packet(self, packet)**: If the node is functional, save the packet onto the buffer for processing. If successful, return True and set received to True, otherwise return False.

**generate_packet(self, packet_type, destination, data=None)**: Creates a new packet on the current node with the specified type and destination. This function also clears the received flag for immediate processing.

**list find_route(self, destination)**: Find a route from the current node to the destination node using the topology list. The algorithm attempts to find the smallest number of hops that ends with the destination node while ignoring any links in the failed list. Returns None if no valid route is found or a list containing node_id if attempting to route to self.

**bool __in_path(self, path)**: Private function. Checks if the given path list contains any elements in the failed list stored on the node. Used to eliminate invalid paths from find_route.

**generate_topology(self)**: Generates the node's topology list recursively generating unique paths to all other reachable nodes in the network. This is a list of lists where each element of the main list is a valid possible path to another node that never repeats a node.

**__generate_routes(self, routes, node, path)**: Recursive function used to generate topology routes. Algorithm works by looping through all links in the current node, adding each of those as an additional link in the path variable, and then appending those paths to the routes list. Does not attempt to go through links that have already been passed through, ending when no further loops are possible.

**run(self)**: Attempts to process any packets on the buffer. Returns True if nothing is on the buffer or something has already been received this tick, False if status is down. It then attempts to process the packet at the top of the buffer and remove the packet once it has been successfully handled.

**bool __process_packet(self, packet)**: Checks the type of packet and runs processing on the packet depending on what type of packet it is. Returns the status of attempting to send packets.

**bool __send_packet(self, packet)**: Attempts to transmit a packet to the next hop in its routing path if possible. Returns the result of the transmit if possible, otherwise False.

**print_buffer, print_links, print_topology**: Debug functions to print out details of the node.
