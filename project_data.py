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
from collections import deque
import itertools as it
import network_cards as nc
from pathlib import Path
#%% Login class

class Login():
    """A class to handle login functionality for the Bluesky API.

    Args:
        username (str): The username for logging in.
        password (str): The password for logging in.

    Attributes:
        client (Client): An instance of the Bluesky API client.
        jwt (str): The JSON Web Token (JWT) obtained after successful login.
    """
    def __init__(self,username,password) :

        self.client = Client(base_url='https://bsky.social/xrpc')

        self.username = username
        self.password = password
        

        try:
        
            self.ab = self.client.login(self.username, self.password)
            self.jwt = self.client._access_jwt
            
        except Exception as e:
            print(f"Error:{e}")

        

    def output_client(self):
        """Returns the Bluesky API client instance and the access token.

       Returns:
           tuple: A tuple containing the client instance and the access token.
       """
        return self.client,self.jwt
#%%

class UserData():
    """A class to handle the extraction of user data from Bluesky feeds.

    Args:
        datas (list): A list of feed URIs.
        client (Client): An instance of the Bluesky API client.
        jwt (str): The JSON Web Token (JWT) for authentication.

    Attributes:
        datas (list): A list of feed URIs.
        client (Client): An instance of the Bluesky API client.
        jwt (str): The JSON Web Token (JWT) for authentication.
      
    """
    def __init__(self,datas,client,jwt):
        
        self.datas = datas
        self.client = client
        self.jwt = jwt
      
        
    def extract_did_list(self,tags):
        
        """Extracts feed data including like count, reply count, repost count, and hashtags.

        Args:
            tags (list): A list of tags corresponding to the feeds.

        Returns:
            list: A list containing feed data including like count, reply count, repost count, and hashtags.
        """
        did_list = []  
        feed_list = []
        current_did = []
        
        for i in range(len(self.datas)):
           
            
                pattern = re.search(r'/([\w-]+)$',self.datas[i]).group(1)
           
                if pattern == 'self':
                    continue
                else:
                    try:
                        data = self.client.app.bsky.feed.get_feed({
                            'feed': self.datas[i],
                            'limit': 100
                        }, headers={'Accept-Language': 'en-US'})
                        next_page = data.cursor
                        while True:
                            for post in data.feed:
                                post_str = str(post)
                              
                                created_at = re.search(r"created_at='(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)'",post_str)        
                                time_stamp = created_at.group(1) if created_at is not None else None
                                
                                if time_stamp is not None:
                                    t = datetime.datetime.strptime(time_stamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                                    #print(t.date())
                                    if t.date() == datetime.date(2023,4,15):
                                        return None
                                        
                                 
                                like_count = re.search(r"like_count=(\d+)", post_str).group(1)
                                reply_count = re.search(r"reply_count=(\d+)", post_str).group(1)
                                repost_count = re.search(r"repost_count=(\d+)", post_str).group(1)
                                hash_tags = re.findall(r"tag='([^']+)'", post_str)
                                did = re.search(r"did='(.*?)'", post_str).group(1)
                                uri = re.search(r"uri='(at://[^']+)'", post_str).group(1)
                                cid = re.search(r"cid='([^']+)'",post_str).group(1)
                               
                                did_list.append([did,like_count,reply_count,repost_count,uri,cid,hash_tags])
                        
                            if next_page is not None:
            
                                data = self.client.app.bsky.feed.get_feed({
                                        'feed': self.datas[i],
                                        'limit': 100,
                                        'cursor': next_page
                                    }, headers={'Accept-Language': 'en-US'})
                                next_page = data.cursor
                                
                            else:
                                feed_list.append([tags[i],did_list])
                                break
                            
                    
                    except Exception as e:
                        print(e)
               
                            
            
        return feed_list

#Function to extract did's,cid's,uri's only from the did_list
    
    def extract_attributes(self,feed_list):
        """Extracts DID, CID, and URI from the feed list.

        Args:
            feed_list (list): A list containing feed data.

        Returns:
            tuple: A tuple containing lists of DID, CID, and URI extracted from the feed list.
        """
        dids = []
        cids =[]
        uris = []
        feed_dids=[]
        feed_cids=[]
        feed_uris=[]
        for feeds in feed_list:
            if feeds is not None:
                for i in feeds[1]:
                    if len(i) >4:
                        #print(i)
                        did = i[0]
                        uri = i[4]
                        cid = i[5]
                        dids.append(did)
                        cids.append(cid)
                        uris.append(uri)
                        
                feed_dids.append([feeds[0],dids])
                feed_cids.append([feeds[0],cids])
                feed_uris.append([feeds[0],uris])
                
        return feed_dids,feed_cids,feed_uris
            
    

#Function to extract the followers and following count of every did

    def followers_and_following(self,dids,cids,uris):
        
            """Extracts followers and following count for each DID.

        Args:
            dids (list): A list of DID data.
            cids (list): A list of CID data.
            uris (list): A list of URI data.

        Returns:
            tuple: A tuple containing lists of actor data including followers,following count,reposts and others from a feed.
            """
        
            actor_list = []
            actor_likes = []
            post_likes = []
            reposts = []
            thread_replies = []
            
            feed_actor_list = []
            feed_actor_likes = []
            feed_reposts =[]
            feed_thread_replies =[]
            jwt = self.jwt
    
            conn = http.client.HTTPSConnection("bsky.social")
            pattern = r'"followersCount":(\d+),"followsCount":(\d+),'
            for did,cid,uri in zip(dids,cids,uris):
                for d,c,u in zip(did[1][0:1000],cid[1][0:1000],uri[1][0:1000]):

                    payload = ''
                    headers = {
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {jwt}'
                    }
                    conn.request("GET", f"/xrpc/app.bsky.actor.getProfile?actor={d}", payload, headers)
                    res1 = conn.getresponse()
                    data1= res1.read()
                    actor_profile = data1.decode("utf-8")
                    
                    
                    conn.request("GET", f"/xrpc/app.bsky.feed.getLikes?uri={u}&cid={c}", payload, headers)
                    res2 = conn.getresponse()
                    data2 = res2.read()
                    likes = data2.decode("utf-8")
                    
                    conn.request("GET", f"/xrpc/app.bsky.feed.getRepostedBy?uri={u}", payload, headers)
                    res3 = conn.getresponse()
                    data3 = res3.read()
                    repost = data3.decode("utf-8")
        
                    conn.request("GET", f"/xrpc/app.bsky.feed.getPostThread?uri={u}", payload, headers)
                    res4 = conn.getresponse()
                    data4 = res4.read()
                    thread = data4.decode("utf-8")
        
                    
                    repost_dids = re.findall(r'"did":"(did:plc:[^"]+)"',repost)
        
                    likers = re.findall(r'"did":"(did:plc:[^"]+)"',likes)
                
                    ff_pattern = re.search(pattern,actor_profile)
                    
                    if ff_pattern is not None:
                        followers_count = ff_pattern.group(1)
                        following_count = ff_pattern.group(2)
        
                        actor_list.append(list(zip([d, followers_count,following_count])))
                        actor_likes.append(list(zip([d, likers]))) 
                        post_likes.append(likes)
                        reposts.append(list(zip([d,repost_dids])))
            
                       
                    else :
                        followers_count = np.nan
                        following_count = np.nan
        
                        actor_list.append(list(zip([d, followers_count,following_count])))
                        actor_likes.append(list(zip([d, likers]))) 
                        post_likes.append(likes)
                        reposts.append(list(zip([d,repost_dids])))
                        
                    if thread is not None:
                        try:
                            thread_dict = json.loads(thread)
                        #print(thread_dict)
                            if 'thread' in thread_dict:
                                if 'replies' in thread_dict['thread']:
                                    for reply in thread_dict['thread']['replies']:
                                        try:
                                            post = reply.get('post')
                                            author = post.get('author')
                                            replier_did = author.get('did')
                                            thread_replies.append(list(zip([d,replier_did])))
                                        except:
                                            continue
                        except:
                            continue
                feed_actor_list.append([did[0],actor_list]),feed_actor_likes.append([did[0],actor_likes]),feed_reposts.append([did[0],reposts]),feed_thread_replies.append([did[0],thread_replies])
            return feed_actor_list, feed_actor_likes, post_likes,feed_reposts,feed_thread_replies,dids
        
    
#%% Building the network:
class Build():
    """A class to build a network graph based on user data.

    Args:
        dids (list): A list of DID data.
        actor_list (list): A list of actor data.
        actor_likes (list): A list of actor likes data.
        reposts (list): A list of reposts data.
        thread_replies (list): A list of thread replies data.
        tags (list): A list of community tags.

    Attributes:
        dids (list): A list of DID data.
        actor_list (list): A list of actor data.
        actor_likes (list): A list of actor likes data.
        reposts (list): A list of reposts data.
        thread_replies (list): A list of thread replies data.
        tags (list): A list of community tags.
    """
    
    def __init__(self,dids,actor_list,actor_likes,reposts,thread_replies,tags):
        self.dids = dids
        self.actor_list = actor_list
        self.actor_likes = actor_likes
        self.reposts = reposts
        self.thread_replies = thread_replies
        #self.current_tags = current_tags
        self.tags = tags
    
    def destringizer(self,val):
        
        """Converts values to string format.

       Args:
           val: The value to be converted.

       Returns:
           list: A list of value converted to string format.
        """
        if type(val) is tuple or list:
            return [str(v) for v in val]

    def build_network(self,G):
        
        """Builds a network graph based on user data.

        Args:
            G (networkx.Graph): The network graph instance.

        Returns:
            networkx.Graph: The network graph instance with user data added.
        """
        current_did = []
        
        for i in range(len(self.dids)):
            for did in self.dids[i][1]:
                    #print(did)
                    if len(current_did)>0:
                        d = current_did.pop()
                        
                        if did !=d and did in self.actor_list[i][1][0]:
                            #print(self.actor_list[i][1][0])
                            followers_count = self.actor_list[i][1][1]
                            follows_count = self.actor_list[i][1][2]
                            G.add_node(did, followers_count=followers_count, follows_count=follows_count,category='User')
    
            # Add edges based on likes, reposts, and replies with edge attributes
            
                        if i < len(self.actor_likes):
                            for did,likers in self.actor_likes[i][1]:
                                for liker in likers:
                                    if len(liker)>0 and type(liker) is not list:
                                        #print(liker)
                                        G.add_edge(did, liker, relationship='like')
            
                        if i < len(self.reposts):
                            for did,reposts in self.reposts[i][1]:
                                for repost in reposts:
                                    #print(repost)
                                    if len(repost)>0 and type(repost) is not list:
                                        G.add_edge(did, repost, relationship='repost')
            
                        if i < len(self.thread_replies):
                            for poster,replier in self.thread_replies[i][1]:
                                    #print(thread_reply)
                                    if len(replier)>0 and type(replier) is not list:
                                        G.add_edge(poster, replier, relationship='reply')
                    else:
                        followers_count = self.actor_list[i][1][1]
                        follows_count = self.actor_list[i][1][2]
                        G.add_node(did, followers_count=followers_count, follows_count=follows_count,category='User')
                        current_did.append(did)
                        
            if len(self.dids)>1:
                while i<len(self.dids):
                    for did,(did,liker),(did,reposter),(poster,replier) in zip(self.dids[i][1],self.actor_likes[i][1],self.reposts[i][1],self.thread_replies[i][1]):
                        if did or liker or reposter or replier  in self.dids[i+1][1] or self.actor_likes[i+1][1] or self.reposts[i+1][1] or self.thread_replies[i+1][1]:
                            G.add_node(self.dids[i][0],category ='community')
                            G.add_edge(self.dids[i+1][0],self.dids[i][0],category='community')
                            
       

        nx.draw(G,alpha =0.5,linewidths =0.7)
        plt.savefig('net')
        nx.write_gml(G, 'graph.gml', stringizer=self.destringizer)
            
        return G

#%%      
class Mapping(UserData):
    
    """A class to map user data to a network graph.

   Args:
       jwt (str): The JSON Web Token (JWT) for authentication.
       init_feed (list): A list of initial feed data.
       client (Client): An instance of the Bluesky API client.
       g1 (networkx.Graph): The first network graph instance.
       g2 (networkx.Graph): The second network graph instance.

   Attributes:
       init_feed (list): A list of initial feed data.
       g1 (networkx.Graph): The first network graph instance.
       g2 (networkx.Graph): The second network graph instance.
   """
    def __init__(self,jwt,init_feed,client,g1,g2):
        super().__init__(init_feed,client,jwt)
        self.init_feed = init_feed
        self.g1 = g1
        self.g2 = g2
        
        #threading.Thread(target =self.worker).start()
        #self.worker(self.q)
        
    def actors_feeds(self,dids):
        """Extracts feed uris created by each DID(user).

        Args:
            dids (list): A list of DID data.

        Returns:
            tuple: A tuple containing lists of feed tags, timestamps, and URIs.
        """
        jwt = self.jwt
        
    
        conn = http.client.HTTPSConnection("bsky.social")
        payload = ''
        headers = {
          'Accept': 'application/json',
          'Authorization': f'Bearer {jwt}'
        }
        
        timestamps =[]
        tags = []
        uris = []
        
        current_did=[]
        self.tags = tags
        for did in dids:
            for d in did[1][0:1000]:
                if len(current_did) >0:
                    prev_did = current_did.pop()
                    if d != prev_did:
                        conn.request("GET", f"/xrpc/app.bsky.feed.getActorFeeds?actor={d}", payload, headers)
                        res = conn.getresponse()
                        data = res.read().decode("utf-8")
                        #print(data)
                        if data is not None:
                            feeds = json.loads(data)
                            if feeds is not None:
                                #print(feeds.get('feeds'))
                                try:
                                    for feed in feeds.get('feeds'):
                                      
                                        uri = feed.get('uri')   
                                        hash_tags = re.findall(r"#\w+", str(feed))
                                     
                                        if len(hash_tags) == 0:
                                            tags.append(feed.get('displayName'))
                                            timestamps.append(feed.get('indexedAt'))
                                            uris.append(uri)
                                        else:
                                            tags.append(hash_tags)
                                            timestamps.append(feed.get('indexedAt'))
                                            uris.append(uri)
                                    
                                except Exception as e:
                                    continue
                else:
                    current_did.append(d)
                    conn.request("GET", f"/xrpc/app.bsky.feed.getActorFeeds?actor={d}", payload, headers)
                    res = conn.getresponse()
                    data = res.read().decode("utf-8")
             
                    if data is not None:
                        feeds = json.loads(data)
                        if feeds is not None:
                        
                            try:
                                for feed in feeds.get('feeds'):
                                    uri = feed.get('uri')
                                
                                    hash_tags = re.findall(r"#\w+", str(feed))
                                
                                    if len(hash_tags) == 0:
                                       
                                        tags.append(feed.get('displayName'))
                                        timestamps.append(feed.get('indexedAt'))
                                        uris.append(uri)
                                    else:
                                        tags.append(hash_tags)
                                        timestamps.append(feed.get('indexedAt'))
                                        uris.append(uri)
                                
                            except Exception as e:
                                continue
                        
       
        return tags,timestamps,uris
        
    """
    def worker(self):
    
        
        conn = http.client.HTTPSConnection("bsky.social")
        payload = ''
        headers = {
          'Accept': 'application/json',
          'Authorization': f'Bearer {self.jwt} '
        }
        current_tags = []
        if len(self.init_feed)>0:
            for i in range(len(self.init_feed)):
                pattern = re.search(r'/(\w+)$',self.init_feed[i]).group(1)
                #print(pattern)
                if pattern == 'self':
                    continue
                else:
                    conn.request("GET", f"/xrpc/app.bsky.feed.getFeedGenerator?feed={self.init_feed[i]}", payload, headers)
                    res = conn.getresponse()
                    data = res.read()
                    feed_info = data.decode("utf-8")
                    current_tag = re.search(r"#\w+", feed_info)
                    if current_tag is not None:
                        current_tags.append(current_tag)
        

        if self.followers_and_following() and self.actors_feeds() is not None:
            actor_list,actor_likes,post_likes,reposts,thread_replies,dids = self.followers_and_following()
            feeds,tags = self.actors_feeds()
            g = Build(dids,actor_list,actor_likes,reposts,thread_replies,current_tags,tags)
            g.build_network(self.g1)
            g.build_network_feed(self.g2)
            #print(tags)
            #print('-----------changed tags follows--------------')
            self.init_feed = feeds
            self.datas = feeds
            #print(self.init_feed)
            return self.g1,self.g2
        else:
            return None
        """

    """
    def rec_function(self):
        
        stack = [self.worker]
        
        while stack is not None:
            task = stack.pop()
            res = task()
            if res is not None:
          
                g1, g2 = res
                self.g1,self.g2 = g1, g2
        
                stack.append(self.worker)
        
   
        feeds,g_1,g_2 = self.worker()
        nx.write_gml(g1,'g1.gml')
        nx.write_gm(g2,'g2.gml')
        nx.kamada_kawai_layout(g1)
        nx.kamada_kawai_layout(g2)
        plt.show()
        return g_1,g_2
        """
        
       
#%%
# Function to create a network card


def net_card(G):
    """
   Generates a network card for the given graph.

   Parameters:
   - G (networkx.Graph): The input graph.

   Returns:
   - None

   This function creates a network card for the given graph, including information about the network's name,
   the type of nodes and links present, and any additional considerations. It also includes metadata such as
   node and link attributes, creation date, data generation process, ethics considerations, funding details,
   citations, and access information. The generated network card is saved as 'Bsky_network_card.tex'.
   """

    # Create network card
    card = nc.NetworkCard(G)
    print(card)
    card.update_overall("Name", "BlueSky Network Graph")
    card.update_overall("Nodes are", "People whose post appeared on #hot-classic on Bluesky")
    card.update_overall("Links are", "People who interacted with the posts(likes,replies,reposts)")
    card.update_overall("Considerations", "This is an example network or overview of the full network") 

    card.update_metainfo({
        "Node metadata":           "Followers_count, Following_count",
        "Link metadata":           "like, reply, repost",
        "Date of creation":        "4/29/2024",
        "Data generating process": "Extracting the data from hot-classic feed using the BlueSky API",
        "Ethics":                   "N/A",
        "Funding":                 "None",
        "Citation":                "None",
        "Access":                  "None"
        })

    card.to_latex("Bsky_network_card.tex")
    print(card)
#%%
g = nx.read_gml('n17.gml')

net_card(g)
#%%


