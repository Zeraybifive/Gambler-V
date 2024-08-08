import discum  # Importing the discum library for interacting with Discord via user accounts
import discord  # Importing the discord library for creating and managing a Discord bot
import Config  # Importing a custom configuration module for handling bot settings
import threading  # Importing threading for running tasks concurrently
import asyncio  # Importing asyncio for asynchronous operations
import time  # Importing time for time-related functions
import datetime  # Importing datetime for handling date and time
import re  # Importing re for regular expression operations
from MudaeSchedule import Timer  # Importing a Timer class from the MudaeSchedule module for timing events
from EzMudae import Mudae  # Importing a Mudae class from the EzMudae module to handle Mudae bot interactions
from discum.utils.slash import SlashCommander  # Importing SlashCommander to handle slash commands for the bot

bot_id = 432610292342587392  # ID of the Mudae bot used in the script
botID = '432610292342587392'  # Same as bot_id but stored as a string
bot = discum.Client(token=Config.Token, log=False)  # Creating a Discum client instance with the bot token from Config
rollCommand = SlashCommander(bot.getSlashCommands(botID).json()).get([Config.Rollcommand])  # Fetching and preparing the roll command for the bot
reaction_lock = asyncio.Lock()  # Creating an asyncio lock for handling reactions safely in asynchronous environment

class MyClient(discord.Client):  # Defining a custom Discord client class by extending discord.Client
    def __init__(self):  # Constructor for the MyClient class
        super().__init__()  # Initializing the parent discord.Client class
        self.allowed_guilds = Config.Servers  # Setting allowed guilds (servers) from the Config module
        self.rolling = {}  # Dictionary to keep track of rolling status in different channels
        self.is_ready = False  # Boolean to track if the bot is fully ready

    async def on_ready(self):  # Event handler for when the bot is ready
        if self.is_ready:  # Check if the bot is already ready
            return  # Exit if the bot is already ready
        print(f'Logged on as {self.user.name} ({self.user.id})')  # Print bot's username and ID
        await self.initialize_channels()  # Initialize channels by calling the method

    async def initialize_channels(self):  # Method to initialize and process channels
        channel_status = {channel_id: False for channel_id in Config.Channels.keys()}  # Create a dictionary to track the status of each channel

        while not all(channel_status.values()):  # Loop until all channels are processed
            for main_channel, sub_channels in Config.Channels.items():  # Iterate over all channels
                if channel_status[main_channel]:  # Skip if the main channel is already processed
                    continue

                await self.process_channel(main_channel, channel_status)  # Process the main channel

        self.is_ready = True  # Set the bot as ready after processing all channels
        print("All channels processed. Ready.")  # Print a message indicating readiness

    async def process_channel(self, main_channel, channel_status):  # Method to process a single channel
        await asyncio.sleep(1)  # Sleep for 1 second before processing
        main_channel_obj = self.get_channel(main_channel)  # Get the channel object for the main channel

        try:
            print(f'Sending message in {main_channel_obj.name}')  # Print which channel is being processed
            await main_channel_obj.send('$tu')  # Send the '$tu' command to the channel
            message = await self.wait_for('message', timeout=3, check=lambda m: m.channel == main_channel_obj)  # Wait for a message response
            await asyncio.sleep(1)  # Sleep for 1 second
            await self.tuparsing(message, main_channel)  # Parse the '$tu' response message
            channel_status[main_channel] = True  # Mark the channel as processed
            self.print_current_timers(main_channel_obj, main_channel)  # Print the current timers for the channel

        except asyncio.TimeoutError:  # Handle case where no response is received within timeout
            print(f'No response received in {main_channel_obj.name} within 3 seconds')  # Print timeout message
            self.handle_timeout(main_channel_obj, message, main_channel, channel_status)  # Handle the timeout scenario

    def print_current_timers(self, main_channel_obj, main_channel):  # Method to print current timers for a channel
        try:
            timers = self.rolling[main_channel].get_timers()  # Get the current timers for the channel
            print(f"Current timers for {main_channel_obj.name}: {timers}")  # Print the timers
        except:  # If there's an issue retrieving timers
            self.find_previous_message(main_channel_obj, main_channel)  # Attempt to find the previous message

    def handle_timeout(self, main_channel_obj, message, main_channel, channel_status):  # Method to handle message timeout
        self.find_previous_message(main_channel_obj, main_channel)  # Try to find a previous message in the channel
        try:
            timers = self.rolling[main_channel].get_timers()  # Get the current timers for the channel
            print(f"Current timers for {main_channel_obj.name}: {timers}")  # Print the timers
        except:  # If there's an issue retrieving timers
            self.find_previous_message(main_channel_obj, main_channel)  # Attempt to find the previous message again
        channel_status[main_channel] = True  # Mark the channel as processed

    async def find_previous_message(self, main_channel_obj, main_channel):  # Method to find a previous message in the channel
        user_message = None  # Initialize user_message as None
        async for prev_message in main_channel_obj.history(limit=10, before=user_message):  # Iterate through message history
            if prev_message.author.id == self.user.id and '$tu' in prev_message.content:  # Check if the message is from the bot and contains '$tu'
                user_message = prev_message  # Assign the previous message to user_message
                break  # Exit the loop once the message is found
        if user_message:  # If a relevant previous message is found
            async for prev_message in main_channel_obj.history(limit=10, after=user_message):  # Search for bot responses after the found message
                if str(bot_id) in prev_message.content and self.user.name in prev_message.content:  # Check if the bot ID and username are in the message
                    print(f'Found previous message containing bot ID and user ID in {main_channel_obj.name}')  # Print a confirmation message
                    await self.tuparsing(prev_message, main_channel)  # Parse the previous message
                    timers = self.rolling[main_channel].get_timers()  # Get the current timers
                    print(f"Current timers for {main_channel_obj.name}: {timers}")  # Print the timers
                    break  # Exit the loop
        else:  # If no relevant previous message is found
            print(f'No relevant previous message found in {main_channel_obj.name}')  # Print a message indicating no previous message was found

    async def tuparsing(self, message, main_channel):  # Method to parse the '$tu' response message
        if message.author == self.user:  # Ignore the bot's own messages
            return

        match = re.search(r"""^.*?\*\*(.*?)\*\*.*?                          # Group 1: Username
                                (can't|can).*?                              # Group 2: Claim available
                                (\d+(?:h\ \d+)?)(?=\*\*\ min).*?            # Group 3: Claim reset
                                (\d+(?:h\ \d+)?)(?=\*\*\ min).*?            # Group 4: Rolls reset
                                (?<=\$daily).*?(available|\d+h\ \d+).*?     # Group 5: $daily reset
                                (can't|can).*?(?=react).*?                  # Group 6: Kakera available
                                (?:(\d+(?:h\ \d+)?)(?=\*\*\ min)|(now)).*?  # Group 7: Kakera reset
                                (?<=\$dk).*?(ready|\d+h\ \d+)               # Group 8: $dk reset
                                .*$                                         # End of string
                                """, message.content, re.DOTALL | re.VERBOSE)  # Regular expression to extract information from the message
        if not match or match.group(1) != self.user.name:  # If no match or not the correct user
            return  # Exit the function

        times = [self.parse_time(match.group(i)) for i in [3, 4, 5, 7]]  # Parse the time values from the matched groups
        kakera_available = match.group(6) == 'can'  # Check if kakera is available
        claim_available = match.group(2) == 'can'  # Check if claim is available

        timing_info = {  # Create a dictionary with all the timing information
            'claim_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[0]),  # Claim reset time
            'claim_available': claim_available,  # Whether claim is available
            'rolls_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[1], seconds=30),  # Rolls reset time
            'kakera_available': kakera_available,  # Whether kakera is available
            'kakera_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[3]),  # Kakera reset time
            'daily_reset': datetime.datetime.now() + datetime.timedelta(minutes=times[2]),  # Daily reset time
        }

        sub_channels = Config.Channels[main_channel]  # Get sub-channels related to the main channel
        self.update_timers(timing_info, main_channel, sub_channels)  # Update the timers for the channel

    def parse_time(self, time_str):  # Method to parse time strings
        if time_str is None:  # If no time is provided
            return 0  # Return 0
        elif 'h ' in time_str:  # If the time includes hours
            hours, minutes = map(int, time_str.split('h '))  # Split the string into hours and minutes
            return hours * 60 + minutes  # Convert the time to minutes
        elif time_str in {'ready', 'now', 'available'}:  # If the time indicates readiness
            return 0  # Return 0
        else:  # If only minutes are provided
            return int(time_str)  # Return the time as an integer

    def update_timers(self, timing_info, main_channel, sub_channels):  # Method to update timers for channels
        for channel_id in [main_channel] + sub_channels:  # Iterate over main and sub-channels
            self.rolling[channel_id] = Timer(  # Create a new Timer instance for the channel
                timing_info["claim_reset"],  # Set the claim reset time
                timing_info["rolls_reset"],  # Set the rolls reset time
                timing_info["daily_reset"],  # Set the daily reset time
                timing_info['claim_available'],  # Set whether claim is available
                timing_info["kakera_reset"],  # Set the kakera reset time
                timing_info["kakera_available"],  # Set whether kakera is available
                self.get_channel(channel_id),  # Get the channel object
                channel_id,  # Set the channel ID
                self  # Pass the current bot instance
            )

            if channel_id == main_channel:  # If it's the main channel
                asyncio.create_task(self.rolling[channel_id].wait_for_p())  # Start the wait_for_p task
                asyncio.create_task(self.rolling[channel_id].wait_for_claim())  # Start the wait_for_claim task
                if Config.Daily > 0:  # If daily tasks are configured
                    asyncio.create_task(self.rolling[channel_id].wait_for_daily())  # Start the wait_for_daily task
                if Config.Roll > 0:  # If rolling tasks are configured
                    asyncio.create_task(self.rolling[channel_id].wait_for_roll())  # Start the wait_for_roll task

    async def on_message(self, message):  # Event handler for receiving messages
        if not self.is_ready:  # If the bot is not ready
            return  # Ignore the message

        if self.is_valid_message(message):  # If the message is from an invalid source
            return  # Ignore the message

        mudae_wrap = Mudae(self, None)  # Create a Mudae wrapper instance

        waifu = mudae_wrap.waifu_from(message)  # Extract waifu information from the message

        main_channel_id = self.get_main_channel_id(message.channel.id)  # Get the main channel ID for the message's channel
        if not main_channel_id:  # If no main channel is found
            return  # Exit the function

        if waifu:  # If a waifu is found in the message
            await self.handle_waifu_message(waifu, message, main_channel_id)  # Handle the waifu message
        else:  # If it's not a waifu message
            await self.handle_bot_message(message)  # Handle the bot message

    def is_valid_message(self, message):  # Method to validate the message source
        return (
            message.author == self.user or  # Ignore the bot's own messages
            message.guild is None or  # Ignore messages not from a guild (server)
            message.guild.id not in self.allowed_guilds or  # Ignore messages from unauthorized guilds
            message.channel.id not in Config.Channels  # Ignore messages from unauthorized channels
        )

    def get_main_channel_id(self, channel_id):  # Method to get the main channel ID from a sub-channel ID
        for main_channel, sub_channels in Config.Channels.items():  # Iterate over all channels
            if channel_id == main_channel or channel_id in sub_channels:  # Check if the channel is a main or sub-channel
                return main_channel  # Return the main channel ID
        return None  # Return None if no main channel is found

    async def handle_waifu_message(self, waifu, message, main_channel_id):  # Method to handle a waifu message
        embed = message.embeds[0]  # Get the first embed in the message
        waifu_dict = {attr: getattr(waifu, attr) for attr in dir(waifu) if not attr.startswith('__') and not callable(getattr(waifu, attr))}  # Create a dictionary of waifu attributes

        if waifu.type == waifu.Type.info:  # If the waifu message is just info
            print("Just an $im command or something")  # Print a message indicating it's info
        elif embed.thumbnail:  # If the message contains a thumbnail
            print("probably mm")  # Print a message indicating it might be a mudae message
        else:  # If it's a claimable waifu
            await self.process_waifu_claim(waifu, message, main_channel_id)  # Process the waifu claim

    async def process_waifu_claim(self, waifu, message, main_channel_id):  # Method to process waifu claims
        channel_name = f"{message.channel.name} " if isinstance(message.channel, discord.TextChannel) else "Unknown"  # Get the channel name
        user = message.author.name if message.interaction is None else message.interaction.user.name  # Get the user who sent the message

        if message.interaction is None:  # If there was no interaction (e.g., slash command)
            async for prev_message in message.channel.history(limit=5, before=message):  # Look at the previous 5 messages
                if '$' in prev_message.content:  # If a command was used in a previous message
                    user = prev_message.author.name  # Set the user to the author of that message
                    break  # Exit the loop

        if waifu.is_claimed:  # If the waifu is already claimed
            print(f"❤️ ---- {waifu.kakera} - {waifu} - {waifu.series} - in {channel_name} by {user}")  # Print claim information
            await self.attempt_kakera_snipe(message, waifu)  # Attempt to snipe kakera
        else:  # If the waifu is not claimed yet
            print(f"🤍 ---- {waifu.kakera} - {waifu} - {waifu.series} - in {channel_name} by {user}")  # Print waifu information
            await self.attempt_claim(waifu, message, main_channel_id)  # Attempt to claim the waifu

    async def attempt_kakera_snipe(self, message, waifu):  # Method to attempt kakera sniping
        if message.components:  # If the message has components (buttons)
            print(f"\nAttempting to snipe kakera for {waifu}\n")  # Print snipe attempt message
            for child in message.components[0].children:  # Iterate over the components' children (buttons)
                await child.click()  # Click the button to attempt the snipe

    async def attempt_claim(self, waifu, message, main_channel_id):  # Method to attempt waifu claim
        if waifu.kakera > Config.lastminkak or waifu.kakera > Config.minkak or waifu.name in Config.Wishlist:  # Check if the waifu meets claim conditions
            if self.rolling[main_channel_id].get_claim_availability():  # Check if claim is available
                if self.rolling[main_channel_id].is_last_min_claim_active():  # Check if last minute claim is active
                        if waifu.kakera >= Config.lastminkak or waifu.name in Config.Wishlist:  # If waifu meets last minute conditions
                            await self.claim_waifu(message, waifu)  # Attempt to claim the waifu
                elif waifu.kakera >= Config.minkak or waifu.name in Config.Wishlist:  # If waifu meets regular claim conditions
                    await self.claim_waifu(message, waifu)  # Attempt to claim the waifu
            else:  # If claim is not available
                print(f"No Claim Available for - {message.channel.name} - to claim {waifu}")  # Print a message indicating no claim is available

    async def claim_waifu(self, message, waifu):  # Method to perform the actual waifu claim
        print(f"\nTrying to claim {waifu}\n")  # Print claim attempt message
        if message.components:  # If the message has components (buttons)
            print("Possibly a wish")  # Print a message indicating it might be a wishlist item
            for child in message.components[0].children:  # Iterate over the components' children (buttons)
                await child.click()  # Click the button to attempt the claim
            await message.add_reaction('❤️')  # React to the message to confirm the claim
        else:  # If there are no components
            await message.add_reaction('❤️')  # React to the message to confirm the claim

    async def handle_bot_message(self, message):  # Method to handle bot-specific messages
        if message.author.id == bot_id:  # Check if the message is from the bot
            if 'Upvote Mudae to reset the timer:' in message.content and f'**{self.user.name}**' in message.content:  # Check if the message is a specific Mudae command
                channel_id = message.channel.id  # Get the channel ID
                self.rolling[channel_id].rolling_event.set()  # Set the rolling event for the channel to stop rolling

    async def on_reaction_add(self, reaction, user):  # Event handler for reactions added to messages
        async with reaction_lock:  # Acquire the reaction lock
            if user != self.user:  # If the reaction is not from the bot itself
                return  # Ignore the reaction

            message = reaction.message  # Get the message the reaction was added to

            if self.is_valid_message(message):  # If the message is from an invalid source
                return  # Ignore the reaction

            main_channel_id = self.get_main_channel_id(message.channel.id)  # Get the main channel ID
            if not main_channel_id:  # If no main channel is found
                return  # Exit the function

            await self.process_reaction(reaction, message, main_channel_id)  # Process the reaction

    async def process_reaction(self, reaction, message, main_channel_id):  # Method to process reactions on messages
        mudae_wrap = Mudae(self, None)  # Create a Mudae wrapper instance
        waifu = mudae_wrap.waifu_from(message)  # Extract waifu information from the message
        await asyncio.sleep(2)  # Wait for 2 seconds
        async for next_message in reaction.message.channel.history(limit=20, after=message):  # Get the next 20 messages after the current one
            if next_message.author.id == bot_id and self.user.name in next_message.content and waifu.name in next_message.content:  # Check if the bot claimed the waifu
                await reaction.message.channel.send('get sniped idiot')  # Send a snipe message in the channel
                print(f"{waifu.name} Claimed")  # Print a message indicating the waifu was claimed
                self.rolling[main_channel_id].set_claim_availability(False)  # Set claim availability to False
                if not Config.AlwaysRoll:  # If always roll is not configured
                    self.rolling[main_channel_id].rolling_event.set()  # Stop the rolling event
                break  # Exit the loop
            elif f"<@{self.user.id}>" in next_message.content and "For this server" in message.content:  # If the claim was used for the server
                self.rolling[main_channel_id].set_claim_availability(False)  # Set claim availability to False
                print("Claim already used")  # Print a message indicating the claim was used
                if not Config.AlwaysRoll:  # If always roll is not configured
                    self.rolling[main_channel_id].rolling_event.set()  # Stop the rolling event
                break  # Exit the loop

    async def rolltest(self, channel_id):  # Method to test rolling in a channel
        channel = self.get_channel(channel_id)  # Get the channel object
        print(f"\nRolling is beginning for {channel.name} at {datetime.datetime.now().strftime('%H:%M:%S')}")  # Print a message indicating rolling has begun

        main_channel_id = self.get_main_channel_id(channel_id)  # Get the main channel ID
        if not main_channel_id:  # If no main channel is found
            return  # Exit the function

        self.rolling[channel_id].rolling_event = threading.Event()  # Create a threading event for rolling

        while not self.rolling[channel_id].rolling_event.is_set():  # While the rolling event is not set
            bot.triggerSlashCommand(bot_id, str(channel_id), str((self.get_channel(main_channel_id)).guild.id), data=rollCommand)  # Trigger a slash command for rolling
            await asyncio.sleep(1.8)  # Wait for 1.8 seconds before the next roll

        print(f"Rolling has ended for {channel.name} at {datetime.datetime.now().strftime('%H:%M:%S')}")  # Print a message indicating rolling has ended
        self.rolling[channel_id].rolling = False  # Set the rolling flag to False

client = MyClient()  # Create an instance of the MyClient class
client.run(Config.Token)  # Run the bot using the token in Config