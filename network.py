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

did_list = ud.extract_did_list()

dids,cids,uris = ud.extract_attributes(did_list)

actor_list, actor_likes, post_likes,reposts,thread_replies,dids = ud.followers_and_following(dids,cids,uris)

g1 ,g2 = nx.DiGraph(), nx.DiGraph()

mp = Mapping(jwt, init_feed, client, g1, g2)


#%% 
with open(f'{Path.cwd}','w+') as f:
    for i in did_list:
        f.write('%')