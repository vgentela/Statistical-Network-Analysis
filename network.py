# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 20:09:12 2024

@author: Varshney
"""
from project_data import *
import networkx as nx
import json
from pathlib import Path
#%% Login by replacing the handle and password with your your username and password

login = Login('handle', 'password')
client,jwt = login.output_client()
#%%
init_feed = ['at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/hot-classic']

ud = UserData(init_feed, client, jwt)
#%% Extract information about each user who has posted to a feed
did_list = ud.extract_did_list(['#hot-classic'])
#%%
dids,cids,uris = ud.extract_attributes(did_list)
#%%
actor_list, actor_likes, post_likes,reposts,thread_replies,dids = ud.followers_and_following(dids,cids,uris)
#%% Initialzie the mapping class
mp = Mapping(jwt, init_feed, client)

#Extract the feeds created by the user in present community if you want to use them for recursive data extraction
tags,timestamps,feed_uris = mp.actors_feeds(dids)

#%% Build the network
g1= nx.Graph()
build = Build(dids,actor_list, actor_likes,reposts,thread_replies)

build.build_network(g1)