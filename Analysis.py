import networkx as nx
import matplotlib.pyplot as plt

G = nx.read_gml('n17.gml')

# Apply Force-Directed layout algorithm to position nodes
def mixing_analysis(graph, attribute):
    assortativity_coefficient = nx.attribute_assortativity_coefficient(graph, attribute)
    print(assortativity_coefficient)
    return assortativity_coefficient

ac = mixing_analysis(G,'followers_count')

### Step 3: Clustering and Community Detection



def detect_communities(graph):
    # Find communities using the greedy modularity maximization
    communities = nx.community.greedy_modularity_communities(graph,best_n=3)

    # Visualization setup
    pos = nx.spring_layout(graph)  # Node positions in 2D space using spring layout
    colors = plt.get_cmap('viridis')  # Color map for different communities

    # Prepare a color palette with enough colors
    color_map = {}
    for idx, community in enumerate(communities):
        for node in community:
            color_map[node] = idx  # Assign community index as color

    # Draw nodes with community colors
    nx.draw_networkx_nodes(graph, pos, node_color=[colors(color_map[node] / len(communities)) for node in graph], node_size=50)

    # Draw edges
    nx.draw_networkx_edges(graph, pos, alpha=0.5)

    plt.savefig('greedy_modularity_communities.png')
    plt.tight_layout()
    plt.show()

    return communities  # Optionally return the communities

detect_communities(G)

### Step 4: Ranking Methodologies (PageRank)
#Finally, let's use PageRank to rank the nodes in the network based on their influence.


def rank_nodes(graph):
    pagerank = nx.pagerank(graph)
    # Sort nodes by PageRank scores in descending order
    ranked_nodes = sorted(pagerank.items(), key=lambda item: item[1], reverse=True)
    top_nodes = ranked_nodes[:10]
    top_nodes_names = [node[0] for node in top_nodes]
    top_nodes_scores = [node[1] for node in top_nodes]
    
    # Plot the PageRank scores of the top 10 nodes
    plt.figure(figsize=(10, 6))
    plt.barh(top_nodes_names, top_nodes_scores, color='skyblue')
    plt.xlabel('PageRank Score')
    plt.ylabel('Node')
    plt.title('Top 10 Nodes by PageRank Score')
    plt.savefig('PageRank')
    plt.tight_layout()
    plt.show()

rank_nodes(G)
