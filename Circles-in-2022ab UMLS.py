import mysql.connector
import networkx as nx

# Connect to the UMLS database
cnx = mysql.connector.connect(host='172.16.34.1',
                              port='3307',
                              user='umls',
                              password='umls', database='umls2022')

# Create a cursor to execute queries
cursor = cnx.cursor()

# Get the CUI relationships from the UMLS database
query = 'SELECT CUI1, CUI2, RELA FROM MRREL limit 6000'
cursor.execute(query)

# Build the graph of CUIs and their relationships
G = nx.DiGraph()
for cui1, cui2, rela in cursor:
    G.add_edge(cui1, cui2)

# Function to check for cycles in the graph
def find_cycles(node, graph, visited, path):
    visited.add(node)
    path.append(node)

    for neighbor in graph[node]:
        if neighbor in path:
            return True
        if neighbor not in visited:
            if find_cycles(neighbor, graph, visited, path):
                return True

    path.pop()
    return False

# Check for cycles in the graph
for node in G:
    visited = set()
    path = []
    if find_cycles(node, G, visited, path):
        path.append(path[0]) # add the first term to the end of the path
        if len(path)>3 and len(path)<40:
            print(path)

# Close the cursor and connection to the database
cursor.close()
cnx.close()
