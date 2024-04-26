#%%
import threading
import multiprocessing
import datetime
import time
import http.client
import re
import numpy as np
import pandas as pd
import atproto_core
from atproto import Client
from atproto import CAR, models ,AtUri
from atproto import FirehoseSubscribeReposClient, firehose_models, parse_subscribe_repos_message
import json
import networkx as nx
#import network_cards as nc
import matplotlib.pyplot as plt
from pyvis.network import Network
from collections import deque
import itertools as it
#%% Looping using feed generator to extract like_count,reply_count,repost_count,hash_tags for every did

class Login():

    def __init__(self,username,password) :

        self.client = Client(base_url='https://bsky.social/xrpc')

        self.username = username
        self.password = password
        

        try:
        
            self.ab = self.client.login(self.username, self.password)
            self.jwt = self.client._access_jwt
            
        except Exception as e:
            print(f"Error:{e}")

        #self.output_client()

    def output_client(self):
        return self.client,self.jwt
    

class UserData():
    
    def __init__(self,datas,client,jwt):
        
        
        self.datas = datas
        self.client = client
        self.jwt = jwt
        q = deque()
        self.q = q
        
    def extract_did_list(self):
        did_list = []   
        datas = self.datas
        
        for d in datas:
            #print(d)
            data = self.client.app.bsky.feed.get_feed({
                'feed': d,
                'limit': 100,
            }, headers={'Accept-Language': 'en-US'})
            next_page = data.cursor
            for post in data.feed:
                
                post_str = str(post)
                #print(post_str)
                created_at = re.search(r"created_at='(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)'",post_str)        
                time_stamp = created_at.group(1) if created_at is not None else None
                if time_stamp is not None:
                    t = datetime.datetime.strptime(time_stamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                    self.q.append(t)
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
                        
                    #data = data
                        
                    next_page = data.cursor
                    #print(next_page)
                else:
                    did_list.append([did,like_count,reply_count,repost_count,uri,cid,hash_tags,time_stamp])    
        return did_list

#Function to extract did's,cid's,uri's only from the did_list
    
    def extract_attributes(self):
        dids = []
        cids =[]
        uris = []

        did_list = self.extract_did_list()
        
        for i in did_list:
            if len(i[0]) >4:
                did = i[0]
                uri = i[4]
                cid = i[5]
            dids.append(did)
            cids.append(cid)
            uris.append(uri)
        return dids,cids,uris
    

#Function to extract the followers and following count of every did
# Instead of using this function, try using get_profile function in the BlueSky API
    def followers_and_following(self):

        dids,cids,uris = self.extract_attributes()

        actor_list = []
        actor_likes = []
        post_likes = []
        reposts = []
        thread_replies = []

        jwt = self.jwt

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
        
            ff_pattern = re.search(pattern,actor_profile)
            
            if ff_pattern is not None:
                followers_count = ff_pattern.group(1)
                following_count = ff_pattern.group(2)

                actor_list.append(list(zip([did, followers_count,following_count])))
                actor_likes.append(list(zip([did, likers]))) 
                post_likes.append(likes)
                reposts.append(list(zip([did,repost_dids])))
    
               
            else :
                followers_count = np.nan
                following_count = np.nan

                actor_list.append(list(zip([did, followers_count,following_count])))
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
            
        return actor_list, actor_likes, post_likes,reposts,thread_replies,dids

class Mapping(UserData):
    
    def __init__(self,jwt,init_feed,client):
        
        self.jwt = jwt
        #self.dids = dids
        self.init_feed = init_feed
        self.client = client
        super().__init__(init_feed,client,jwt)
        #threading.Thread(target =self.worker).start()
        self.worker()
    def actors_feeds(self):
        
        jwt = self.jwt
        dids,cids,uris = self.extract_attributes()
        
        conn = http.client.HTTPSConnection("bsky.social")
        payload = ''
        headers = {
          'Accept': 'application/json',
          'Authorization': f'Bearer {jwt}'
        }
        
        feeds =[]
        tags = []
        self.tags = tags
        for did in dids:
            conn.request("GET", f"/xrpc/app.bsky.feed.getActorFeeds?actor={did}", payload, headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            if data is not None:
                try:
                    uri = re.findall(r'"uri":"(at://[^"]+)"', data)
                    hash_tags = re.findall(r"#\w+", data)
                    feeds.append(uri)
                    tags.append(hash_tags)
                except:
                    continue
                        
        return list(it.chain.from_iterable(feeds)),tags

    def worker(self):
        g1 = nx.DiGraph()
        g2 = nx.DiGraph()
        while True:
            
            conn = http.client.HTTPSConnection("bsky.social")
            payload = ''
            headers = {
              'Accept': 'application/json',
              'Authorization': f'Bearer {self.jwt} '
            }
            current_tags = []
            if len(self.init_feed)>1:
                for i in range(len(self.init_feed)):
                    conn.request("GET", f"/xrpc/app.bsky.feed.getFeedGenerator?feed={self.init_feed[i]}", payload, headers)
                    res = conn.getresponse()
                    data = res.read()
                    feed_info = data.decode("utf-8")
                    current_tag = re.search(r"#\w+", feed_info)
                    current_tags.append(current_tag)
            
            actor_list,actor_likes,post_likes,reposts,thread_replies,dids = self.followers_and_following()
            feeds,tags = self.actors_feeds()
            #print(feeds,tags)
            self.datas = feeds
            self.init_feed = feeds
            g = Build(dids,actor_list,actor_likes,reposts,thread_replies,current_tags,tags)
            g.build_network(g1)
            g.build_network_feed(g2)
            
            print('----------------------------------------------------------------')
            #g = 
            t = self.q[-1]
            if t.date() == datetime.date(2023,4,15):
                print(t.date())
                nx.write_gml(g1,'g1.gml')
                nx.write_gm(g2,'g2.gml')
                nx.kamada_kawai_layout(g1)
                nx.kamada_kawai_layout(g2)
                plt.show()
                return g1,g2
        
       
#%%
login = Login('t0st.bsky.social', 'Val124#$')
client,jwt = login.output_client()
#%%
init_feed = ['at://did:plc:nylio5rpw7u3wtven3vcriam/app.bsky.feed.generator/aaai4amp77qp6']
Mapping(jwt,init_feed, client)
#%% test statements
#feeds =['at://did:plc:ekakc6ukwom6kbkhttmf5iot/app.bsky.feed.generator/aaafzcponj76k', 'at://did:plc:ekakc6ukwom6kbkhttmf5iot/app.bsky.feed.generator/aaaem5qglmtme', 'at://did:plc:ekakc6ukwom6kbkhttmf5iot/app.bsky.feed.generator/aaadowj3kyaqg', 'at://did:plc:ekakc6ukwom6kbkhttmf5iot/app.bsky.feed.generator/aaaahszoazxnq', 'at://did:plc:obzgiyh5vnhtwrtewot77mi4/app.bsky.feed.generator/aaaj56gtwli3u', 'at://did:plc:obzgiyh5vnhtwrtewot77mi4/app.bsky.actor.profile/self']
#for feed in feeds:
    #print(feed)
#print(init_feed.strip())
#print(post_likes[5])
#print(len(actor_likes[7][1][0]))
#print(thread_replies[0][1][0])
#print(dids[0])
#print(actor_likes[5][1][0])
#print(reposts[1][0][0])
#print(dids)
#print(actor_list)


    #%% Building the network:
class Build():
    
    def __init__(self,dids,actor_list,actor_likes,reposts,thread_replies,current_tags,tags):
        self.dids = dids
        self.actor_list = actor_list
        self.actor_likes = actor_likes
        self.reposts = reposts
        self.thread_replies = thread_replies
        self.current_tags = current_tags
        self.tags = tags
        
    def build_network(self,G):
        # Create an empty directed graph

        # Add nodes for each DID from the feed with follower and following counts
        for i in range(len(self.dids)):
            did = self.dids[i]
            if did in self.actor_list[i][0][0]:
                followers_count = self.actor_list[i][1][0]
                follows_count = self.actor_list[i][2][0]
                G.add_node(did, followers_count=followers_count, follows_count=follows_count)
                #print(did)
        # Add edges based on likes, reposts, and replies with edge attributes
        
            if i < len(self.actor_likes):
                for liker in self.actor_likes[i][1][0]:
                    G.add_edge(did, liker, relationship='like')

            if i < len(self.reposts):
                for repost in self.reposts[i][1][0]:
                    G.add_edge(did, repost, relationship='repost')

            if i < len(self.thread_replies):
                for thread_reply in self.thread_replies[i][1][0]:
                    G.add_edge(did, thread_reply, relationship='reply')

            #plt.show()
            #nx.write_gml(G, 'graph.gml', stringizer=None)
            
      
    
    def build_network_feed(self,G):
        tags = self.tags
        current_tags = self.current_tags

        if len(current_tags) >0 and len(tags)>0:
           for idx, ct,ts in enumerate(zip(current_tags,tags)):
               G.add_node(ct)
               for t in ts:
                   if t is not None:
                       G.add_nodes_from(t)
                       G.add_edge_from([ct,tag] for tag in t)
        #plt.show()
        #nx.write_gml(G,'graph_2.gml')
        
    
#%%

# Function to create a network card
    """
    def net_card(self,G):
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
            "Citation":                "None"
            "Access":                   "https://docs.bsky.app/docs/get-started"
            })

        card.to_latex("Bsky_network_card.tex")
        print(card)
        """




