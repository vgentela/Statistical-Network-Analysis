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
    communities = nx.algorithms.community.girvan_newman(graph)
    print(communities)
    # Get the first set of communities
    first_iteration_communities = next(communities)
    pos = nx.spring_layout(graph)
    cmap = plt.get_cmap('viridis')
    size = float(len(first_iteration_communities))
    for idx, community in enumerate(first_iteration_communities):
        nx.draw_networkx_nodes(graph, pos, community, node_size=20, node_color=[cmap(idx / size)])

    nx.draw_networkx_edges(graph, pos, alpha=0.5)
    plt.savefig('communities.png')
    plt.show()



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
    plt.gca().invert_yaxis()  # Invert y-axis to have highest score at the top
    plt.savefig('PageRank')
    plt.show()

rank_nodes(G)
