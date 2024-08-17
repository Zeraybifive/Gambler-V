# List of server (guild) IDs where the bot will operate
Servers = [1221555741479931944, 1221555741479931944]  # Example server IDs

# Dictionary mapping channel IDs to their related sub-channels
Channels = {
    1259214788467101737: [1.1, 1.2, 1.3],
    # 1270629650128961546: [2.1, 2.2, 2.3],  # Example commented out channel
}
   # 1:[1270629650128961546], #The first one is the main channel, inside the brackets are the sub channels (channels within the same server) that have the same timers (roll resets, etc), 
   # The first channel is also where the daily vote and pokemon rolls will be done in
   # 2:[1270629650128961546],

# The bot token for authentication with Discord API
Token = 'your token here'
# Token = 'your token here'  # Example commented out token

# Command used by the bot to trigger the roll functionality
Rollcommand = 'hg'

# Boolean flag to determine if the bot should continue rolling after a claim
AlwaysRoll = True

# Wishlist containing names of characters that the bot should prioritize
Wishlist = [
    'Zero Two', 'Rem', 'Megumin', 'Cayde-6', 'Radahn', 'Andrew Graves',
    'Dogmeat (FO4)', 'Will Wood', 'V2', 'Sundowner', 'Adam Smasher', 'Blade (NUc)',
    'William Afton', 'Wallace', 'Gromit', 'Rock Pikmin', 'Golden Freddy', 'The Knight',
    'Elizabeth', 'Homelander', 'Unknown', 'Osamu Dazai', 'Sou Hiyori', 'Nagito Komaeda',
    'Monika', 'Valentine', 'N', 'Aigis', 'Goro Akechi', 'Aqua Hoshino',
    'Mudae-chan', 'Oh Sangwoo', 'Yoon Bum', 'Aki Hayakawa', 'Hua Cheng', 'Xie Lian',
    'Elysia', 'Nier (Brother)', 'Alice Liddell', 'Ciel Phantomhive', 'Kainé', 'Miyashita Yuu',
    'Ashe', 'Antarcticite', 'Kyuubi', 'Qingque', 'Raiden Mei', 'Sion',
    ':ribbon:OMGkawaii:ribbon:Angel-chan', 'Ahri', 'Minato Namikaze', 'Sakuya Izayoi', 'Fujiwara no Mokou',
    'Haku (Naruto)', 'Corin Wickes'
]

# Timers for different bot functionalities in minutes
Daily = 1200  # Duration for daily 
Claim = 180   # Duration between claim resets
Roll = 60     # Duration between roll resets

# Kakera thresholds for claiming
minkak = 200            # Minimum kakera needed to claim
lastminkak = 50         # Minimum kakera needed to claim in the last 60 minutes before reset
