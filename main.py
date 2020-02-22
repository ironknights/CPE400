import json
from mesh import *  # Covers the Mesh, Packet, and Node classes

loaded_mesh = 0     # Global variable used for simulation function


def init_mesh():
    """Asks the user which mesh to initialize and performs basic initialization"""
    # Full mesh network from assignment
    mesh1 = """
    {
        "0": ["1", "3"],
        "1": ["0", "2", "4"],
        "2": ["1"],
        "3": ["0", "4", "6"],
        "4": ["1", "3", "5", "7"],
        "5": ["4", "8", "9"],
        "6": ["3"],
        "7": ["4", "8"],
        "8": ["5", "7"],
        "9": ["5", "10"],
        "10": ["9", "11", "13"],
        "11": ["10", "12", "13", "14", "15"],
        "12": ["11", "15"],        
        "13": ["10", "11", "14"],
        "14": ["11", "13", "15"],
        "15": ["11", "12", "14"]
    }    
    """
    # Partial mesh network cut off at the '9' node
    mesh2 = """
    {
        "0": ["1", "3"],
        "1": ["0", "2", "4"],
        "2": ["1"],
        "3": ["0", "4", "6"],
        "4": ["1", "3", "5", "7"],
        "5": ["4", "8"],
        "6": ["3"],
        "7": ["4", "8"],
        "8": ["5", "7"]
    }
    """
    # Throughput testing mesh, runs from 0 and 1 to 11 and back.
    mesh3 = """
    {
        "0": ["2", "3"],
        "1": ["3", "4"],
        "2": ["0", "3", "5"],
        "3": ["0", "1", "2", "4", "6"],
        "4": ["1", "3", "7"],
        "5": ["2", "6", "8"],
        "6": ["3", "5", "7", "9"],
        "7": ["4", "6", "10"],
        "8": ["5", "9", "11"],
        "9": ["6", "8", "10"],
        "10": ["7", "9", "11"],
        "11": ["8", "9", "10"]
    }
    """
    print("1. Project Assignment Mesh (numbering from readme file)")
    print("2. Abridged Project Assignment Mesh (above with everything right of node '9' removed)")
    print("3. Throughput Test Mesh (numbering from readme file)")
    json_data = None
    global loaded_mesh  # Keep track for simulation
    # Get user input
    while not json_data:
        response = input("Which mesh would you like to load (enter to quit)?")
        if response == "1":
            loaded_mesh = 1
            json_data = json.loads(mesh1)
        elif response == "2":
            loaded_mesh = 2
            json_data = json.loads(mesh2)
        elif response == "3":
            loaded_mesh = 3
            json_data = json.loads(mesh3)
        elif not response:
            exit(0)
        else:
            print("Invalid response, please try again...")
    # Create mesh object and initialize all nodes
    mesh = Mesh(json_data)
    mesh.generate_topology()
    return mesh


def print_mesh(mesh):
    """Prints tick-by-tick details of the mesh's current status."""
    print("Network status flags:")
    # Display failed nodes (if any)
    for node in mesh.mesh:
        if not mesh[node].status:
            print(f"    Node {node} down")
    # Display failed links (if any)
    for link in mesh.dead_links:
        print(f"    Link {link} down")
    # Display current buffer sizes
    for node in mesh.mesh:
        if mesh[node].buffer:
            print(f"    Node {node} has {len(mesh[node].buffer)} packets pending")
    print("--------------")
    print(f"Network events for tick {mesh.tick}:")
    # Display contents of actions for last tick
    if mesh.actions:
        for action in mesh.actions:
            print(f"     {action}")
    print("--------------")


def print_ui(mesh):
    """Print the UI menu for the user."""
    print("     Menu")
    print("--------------")
    print("Generate new [p]acket")
    print("Run [n]ext tick")
    print("Build [s]imulation")
    print("Generate [r]andom failure")
    print(f"Set fail [c]hances (node: {mesh.fail_chances['node']}, link: {mesh.fail_chances['link']})")
    print("Toggle node [f]ailure")
    print("Toggle [l]ink failure")
    print("Res[t]ore mesh (disable all failures)")
    print("Show node [b]uffers")
    print("[I]nspect node")
    print("[A]verage topology size")
    print("[Q]uit")


def choose_object(msg, obj):
    """Function to choose an element from a list or dictionary."""
    # Display options to user
    for o in obj:
        print(o)
    while True:
        response = input(msg)
        # Break on no input (cancelled)
        if not response:
            return None
        # Only allow valid responses
        if response not in obj:
            print(f"'{response}' not a valid option")
            continue
        break
    return response


def get_number(msg, default):
    """Gets a number for user input or a default value on enter."""
    num = input(msg)
    if not num:
        value = default
    else:
        try:
            value = int(num)
        except ValueError:
            print("Invalid number (must be integer)...")
            return -1
    return value


def simulate(mesh, num_packets, node_fail=0, link_fail=0):
    """Runs a basic simulation for testing purposes.

    Summary:
    The simulation generates 10 packets at the first two nodes of the mesh over 10 ticks for a total of 20
    packets over 10 ticks and sends them to the last node of the mesh. It runs until all buffers are empty
    and then displays the results. It uses the current settings of the mesh but otherwise resets everything
    before running.

    Parameters:
        :param mesh The mesh object to simulate.
        :param num_packets The number of packets to create per simulation node.
        :param node_fail The node failure chance percent.
        :param link_fail The link failure chance percent.

    NOTE: Exits on finish due to unsolved bugs.
    """
    # Start by undoing any failures already set.
    mesh.restore()

    # Set failure chances
    if 0 < node_fail <= 100:
        mesh.set_rand_fail("node", node_fail)
    if 0 < link_fail <= 100:
        mesh.set_rand_fail("link", link_fail)

    # Get early node values
    count = 0
    node0, node1, target_node = None, None, None
    # Assign target based on mesh loaded
    if loaded_mesh == 1:
        target_node = "12"
    elif loaded_mesh == 2:
        target_node = "8"
    elif loaded_mesh == 3:
        target_node = "11"
    else:
        target_node = "2"
    # Assign origins as first two nodes
    for node in mesh.mesh:
        if count > 1:
            break
        if count == 0:
            node0 = node
        if count == 1:
            node1 = node
        count += 1
    # Main simulation loop
    packet_gen = 0
    while True:
        # Generate packets if still under total number of packets
        if packet_gen < num_packets:
            mesh[node0].generate_packet("data", target_node)
            mesh[node1].generate_packet("data", target_node)
        # Check for completion from all packets completed or timeout
        if mesh.get_average_buffer() < 0.0 or packet_gen > 5000:
            break
        # Run simulation until all buffers are cleared
        mesh.run()
        packet_gen += 1
    if packet_gen > 5000:
        print("TIMEOUT!")
    mesh.print_metrics()
    exit(0)     # Repeated simulations cause errors, so exit


def main():
    """Main program loop."""
    mesh = init_mesh()
    while True:
        print_mesh(mesh)
        print_ui(mesh)
        response = input("Enter response: ")
        response = response.lower()     # Convert to lowercase
        # Check for quit
        if not response or response == 'q':
            print("exiting...")
            return
        # Check for generating a packet
        elif response == 'p':
            origin = choose_object("Which node would you like to use as origin of packet? ", mesh.mesh)
            if not origin:
                print("Canceled")
                continue
            destination = choose_object("Which node would you like to use as destination? ", mesh.mesh)
            if not destination:
                print("Canceled")
                continue
            data = input("Type the data would you like to attach to packet (enter for None): ")
            mesh[origin].generate_packet("data", destination, data)
        # Check for generating a random failure
        elif response == 'r':
            fail_chance = input("What chance of failure do you want (0-100, default: 100)? ")
            try:
                if not fail_chance or 0 < int(fail_chance) <= 100:
                    if not fail_chance:
                        fail_chance = "100"
                    node_type = input("What would you like fail (node or link, default: node)? ")
                    if not node_type or node_type in ("node", "link"):
                        if not node_type:
                            node_type = "node"
                        mesh.rand_fail(node_type, int(fail_chance))
            except ValueError:
                continue
        # Check for changing failure chances
        elif response == 'c':
            fail_chance = input("What chance of failure do you want (0-100, default: 50)?? ")
            try:
                if not fail_chance or 0 < int(fail_chance) <= 100:
                    if not fail_chance:
                        fail_chance = "50"
                    node_type = input("What would you like set failure chance (node or link, default: node)? ")
                    if not node_type or node_type in ("node", "link"):
                        if not node_type:
                            node_type = "node"
                        mesh.fail_chances[node_type] = int(fail_chance)
            except ValueError:
                continue
        # Check for causing a specific failure in a node
        elif response == 'f':
            print("Nodes currently down:")
            found = False
            for node in mesh.mesh:
                if not mesh[node].status:
                    found = True
                    print(f"{node} down")
            if not found:
                print("None")
            node = choose_object("Choose a node to toggle: ", mesh.mesh)
            if not node:
                continue
            mesh[node].status = not mesh[node].status
        # Check for causing a specific failure in a link
        elif response == 'l':
            print("Links currently down:")
            if not mesh.dead_links:
                print("None")
            else:
                for link in mesh.dead_links:
                    print(link)
            node0 = choose_object("What is the first node in the link? ", mesh.mesh)
            node1 = choose_object("What is the next node in the link? ", mesh[node0].links)
            if not node0 or not node1:
                continue
            mesh.toggle_link(node0, node1)
        # Check for restoring the mesh
        elif response == 't':
            mesh.restore()
        # Check for incrementing to next tick
        elif response == 'n':
            mesh.run()
        # Check for inspecting a node
        elif response == 'i':
            node = choose_object("Choose a node to inspect: ", mesh.mesh)
            if not node:
                continue
            print("1: buffer")
            print("2: links")
            print("3: topology")
            inspect = input("What would you like to inspect?")
            if inspect == "1":
                mesh[node].print_buffer()
            elif inspect == "2":
                mesh[node].print_links()
            elif inspect == "3":
                mesh[node].print_topology()
        # Check for printing out all node buffers
        elif response == 'b':
            for node in mesh.mesh:
                mesh[node].print_buffer()
        # Check for printing out average topology size
        elif response == 'a':
            mesh.print_average_topology_size()
        # Check for running a simulation
        elif response == 's':
            num_packets = get_number("How many packets would you like to generate (default 10)? ", 10)
            if num_packets == -1:
                continue
            node_fail = get_number("Node fail chance (default 0)? ", 0)
            if node_fail == -1:
                continue
            link_fail = get_number("Link fail chance (default 0)? ", 0)
            if link_fail == -1:
                continue
            simulate(mesh, num_packets, node_fail, link_fail)
        else:
            print("Unknown response!")


if __name__ == "__main__":
    """This should always be run, but just in case this is imported, do not run automatically."""
    main()
