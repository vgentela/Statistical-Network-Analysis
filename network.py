# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 20:09:12 2024

@author: Varshney
"""
from project_data import *
import networkx as nx
import json
from pathlib import Path
#%%

login = Login('t0st.bsky.social', 'Val124#$')
client,jwt = login.output_client()
#%%
init_feed = ['at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/hot-classic']

ud = UserData(init_feed, client, jwt)
#%%
did_list = ud.extract_did_list()

dids,cids,uris = ud.extract_attributes(did_list)

actor_list, actor_likes, post_likes,reposts,thread_replies,dids = ud.followers_and_following(dids,cids,uris)
#%%
g1 ,g2 = nx.DiGraph(), nx.DiGraph()

mp = Mapping(jwt, init_feed, client, g1, g2)


#%% 
tags,timestamps,feed_uris = mp.actors_feeds(dids,cids,uris)

#%%
build = Build(dids,actor_list, actor_likes,reposts,thread_replies,tags)

build.build_network(g1)

#%%% ----------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
#%% For 2nd Set of Feeds

ud_1 = UserData(feed_uris[0:50], client, jwt)
#%%
feed_list_1 = ud_1.extract_did_list(tags[0:50])
#%%
dids_1,cids_1,uris_1 = ud.extract_attributes(feed_list_1)
#%%
actor_list_1, actor_likes_1, post_likes_1,reposts_1,thread_replies_1,dids_1 = ud.followers_and_following(dids_1,cids_1,uris_1)
#%%
g1_1 ,g2_1 = nx.DiGraph(), nx.DiGraph()

mp_1 = Mapping(jwt, uris, client, g1_1, g2_1)


#%% 
#tags_1,timestamps_1,uris_1_1 = mp.actors_feeds(dids,cids,uris)

#%%
len(cids_1[0][1])
#%%