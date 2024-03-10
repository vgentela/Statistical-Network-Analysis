#%%
from project_data import *

#%%

login = Login(username = input('username:'),password = input('password:'))
client,jwt = login.output_client()
user_data= login.UserData(client = client, data=client.app.bsky.feed.get_feed({
    'feed': 'at://did:plc:nylio5rpw7u3wtven3vcriam/app.bsky.feed.generator/aaai4amp77qp6',
    'limit': 100,
}, headers={'Accept-Language': 'en-US'}),jwt=jwt)
# %%
actor_list,actor_likes,post_likes,reposts,thread_replies = user_data.followers_and_following()
# %%
print(actor_list[0])
# %%
build_network = Build(actor_list,actor_likes,post_likes,reposts,thread_replies)
G = build_network.build_network()