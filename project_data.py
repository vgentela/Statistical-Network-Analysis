#%%
import http.client
import re
import numpy as np
import pandas as pd
from atproto import Client
import json
import networkx as nx
import network_cards as nc
#from network_cards import NetworkCard, NodeCard, EdgeCard

import matplotlib.pyplot as plt
from pyvis.network import Network
#%%
client = Client(base_url='https://bsky.social/xrpc')
ab = client.login('username', 'password')

jwt = client._access_jwt
print(jwt)


#%% Looping using feed generator to extract like_count,reply_count,repost_count,hash_tags for every did

def extract_did_list(data):
    did_list = []
    
    next_page = data.cursor

    for post in data.feed:
        post_str = str(post)
        like_count = re.search(r"like_count=(\d+)", post_str).group(1)
        reply_count = re.search(r"reply_count=(\d+)", post_str).group(1)
        repost_count = re.search(r"repost_count=(\d+)", post_str).group(1)
        hash_tags = re.findall(r"tag='([^']+)'", post_str)
        did = re.search(r"did='(.*?)'", post_str).group(1)
        uri = re.search(r"uri='(at://[^']+)'", post_str).group(1)
        cid = re.search(r"cid='([^']+)'",post_str).group(1)
        #print(post)
        if next_page is not None:
    
            did_list.append([did,like_count,reply_count,repost_count,uri,cid,hash_tags])
                
            data = client.app.bsky.feed.get_feed({
                    'feed': 'at://did:plc:nylio5rpw7u3wtven3vcriam/app.bsky.feed.generator/aaai4amp77qp6',
                    'limit': 100, 'cursor': next_page
                    }, headers={'Accept-Language': 'en-US'})  
                
            next_page = data.cursor

        else:
            did_list.append([did,like_count,reply_count,repost_count,uri,cid,hash_tags])    
    return did_list


# %% Function to extract did's,cid's,uri's only from the did_list

did_list = extract_did_list(data = client.app.bsky.feed.get_feed({
    'feed': 'at://did:plc:nylio5rpw7u3wtven3vcriam/app.bsky.feed.generator/aaai4amp77qp6',
    'limit': 100,
}, headers={'Accept-Language': 'en-US'})  )
print(did_list[3])

def extract_attributes(did_list):
    dids = []
    cids =[]
    uris = []

    for i in did_list:
        did = i[0]
        uri = i[4]
        cid = i[5]
        dids.append(did)
        cids.append(cid)
        uris.append(uri)

    return dids,cids,uris

dids,cids,uris = extract_attributes(did_list)
#print(dids[3],cids[3],uris[3])


# %% Function to extract the followers and following count of every did

def followers_and_following(dids,cids, uris):
    actor_list = []
    actor_likes = []
    post_likes = []
    reposts = []
    thread_replies = []

    conn = http.client.HTTPSConnection("bsky.social")
    pattern = r'"followersCount":(\d+),"followsCount":(\d+),'
    for did,cid,uri in zip(dids,cids,uris):
        payload = ''
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {jwt}'
        }
        conn.request("GET", f"/xrpc/app.bsky.actor.getProfile?actor={did}", payload, headers)
        res1 = conn.getresponse()
        data1= res1.read()
        actor_profile = data1.decode("utf-8")

        conn.request("GET", f"/xrpc/app.bsky.feed.getLikes?uri={uri}&cid={cid}", payload, headers)
        res2 = conn.getresponse()
        data2 = res2.read()
        likes = data2.decode("utf-8")
        
        conn.request("GET", f"/xrpc/app.bsky.feed.getRepostedBy?uri={uri}", payload, headers)
        res3 = conn.getresponse()
        data3 = res3.read()
        repost = data3.decode("utf-8")

        conn.request("GET", f"/xrpc/app.bsky.feed.getPostThread?uri={uri}", payload, headers)
        res4 = conn.getresponse()
        data4 = res4.read()
        thread = data4.decode("utf-8")

        
        repost_dids = re.findall(r'"did":"(did:plc:[^"]+)"',repost)

        likers = re.findall(r'"did":"(did:plc:[^"]+)"',likes)
    
        match = re.search(pattern,actor_profile)
        followers_count = match.group(1)
        follows_count = match.group(2)

        actor_list.append(list(zip([did, followers_count,follows_count])))
        actor_likes.append(list(zip([did, likers]))) 
        post_likes.append(likes)
        reposts.append(list(zip([did,repost_dids])))

        thread_dict = json.loads(thread)
        #print(thread_dict)
        if 'thread' in thread_dict:
            if 'replies' in thread_dict['thread']:
                for reply in thread_dict['thread']['replies']:
                    post = reply.get('post')
                    author = post.get('author')
                    replier_did = author.get('did')
                    thread_replies.append(list(zip([did,replier_did])))
        
    return actor_list, actor_likes, post_likes,reposts,thread_replies

actor_list,actor_likes,post_likes,reposts,thread_replies = followers_and_following(dids,cids,uris)




#%% test statements


#print(post_likes[5])
#print(len(actor_likes[7][1][0]))
#print(thread_replies[0][1][0])
#print(dids[0])
#print(actor_likes[5][1][0])
#print(reposts[1][0][0])
#print(dids)
#print(actor_list)

#%% Building the network:

def build_network(dids,actor_list,actor_likes,reposts,thread_replies):
    # Create an empty directed graph
    G = nx.DiGraph()

    # Add nodes for each DID from the feed with follower and following counts
    for i in range(len(dids)):
        did = dids[i]
        if did in actor_list[i][0][0]:
            followers_count = actor_list[i][1][0]
            follows_count = actor_list[i][2][0]
            G.add_node(did, followers_count=followers_count, follows_count=follows_count)

    # Add edges based on likes, reposts, and replies with edge attributes
    
        if i < len(actor_likes):
            for liker in actor_likes[i][1][0]:
                G.add_edge(did, liker, relationship='like')

        if i < len(reposts):
            for repost in reposts[i][1][0]:
                G.add_edge(did, repost, relationship='repost')

        if i < len(thread_replies):
            for thread_reply in thread_replies[i][1][0]:
                G.add_edge(did, thread_reply, relationship='reply')

    return G
G = build_network(dids,actor_list,actor_likes,reposts,thread_replies)

plt.show()
nx.write_gml(G, 'graph.gml', stringizer=None)

#%%
# Create network card
card = nc.NetworkCard(G)
card.update_overall("Name", "BlueSky Network Graph")
card.update_overall("Nodes are", "People who posted in a community or feed in Bluesky")
card.update_overall("Links are", "People who interacted with the posts(likes,replies,reposts)")
card.update_overall("Considerations", "This is an example network or overview of the full network") 

card.update_metainfo({
    "Node metadata":           "Followers_count, Following_count",
    "Link metadata":           "like, reply, repost",
    "Date of creation":        "3/5/2024",
    "Data generating process": "Extracting the data using the BlueSky API",
    "Ethics":                   "N/A",
    "Funding":                 "None",
    "Citation":                "arXiv:2206.00026",
    "Access":                   "https://docs.bsky.app/docs/get-started"
    })

card.to_latex("Bsky_network_card.tex")
print(card)



#%% More Thoughts and Ideas
"""
conn.request("GET", "/xrpc/app.bsky.feed.getPostThread", payload, headers)
conn.request("GET", "/xrpc/app.bsky.actor.getProfile", payload, headers)
conn.request("GET", "/xrpc/app.bsky.feed.getActorLikes?actor=at://did:plc:uzdj33pvksktazllpypimbg4", payload, headers)
conn.request("GET", "/xrpc/com.atproto.admin.getRecord?uri=at://did:plc:nylio5rpw7u3wtven3vcriam/app.bsky.feed/aaai4amp77qp6", payload, headers)

conn.request("GET", "/xrpc/app.bsky.feed.getLikes", payload, headers)
conn.request("GET", "/xrpc/app.bsky.feed.getRepostedBy", payload, headers)
conn.request("GET", "/xrpc/app.bsky.graph.getFollowers", payload, headers)
conn.request("GET", "/xrpc/app.bsky.graph.getFollows", payload, headers)
"""

"""
Array : Two dimensional
    rows : nodes or users
    cols : connections or edges(likes, replies, reposts, mentions)
    Edges are directed and parallel.
    Node attributes : followers, following, mentions
    Edges also contain attribute info such as likes, replies, reposts.
    But, what about hashtags??? Probably, hashtags form the outer or the higher level in the network and every post in the feed is
    categorized under each hashtag and hastags are then linked in the network.

Drop Duplicate DID's
Here is the idea : For all the likes, replies,mentions and reposts : create edges.
get likes for did's in did list using http method and add an edge between the author of the post and liker of the post.

Every Node should display the name of the feed or feeds they belong to.
if there are reposts, the repost should be mentioned on the edge as reposted.

The outer layer of the network should be clustered into different feeds and the next hashtags and edges should be between users
in the same or different feeds.

Another idea : Start with actors in one feed and build a network as it expands.(actors in one feed liking posts of actors in other feed
,etc.. )

THE EDGE SHOULD CONTAIN THE NAME OF FEEDS THE CONNECTING DID FOLLOWS // TODO Implement this 
EXTRACT MULTIPLE REPLIES IN THREADS AND ADD EDGES BETWEEN THE DID's IN THREADS.//TODO Implement this

Nodes : did's in the first feed
Edges : for every did in the feed, edge to did's who have liked a post, replied to a post, reposted the post.

Node attributes : followers_count, following_count, like_count
Edge attributes : indicating if the edge is a like, reply or a repost.

did's from the did_list will be the nodes
for every other did that liked,replied to or reposted this did's post will have an edge.

edges to the did's in the actor_likes list will carry the like attribute.

"""


