import time
import datetime
import Config
import asyncio

class Timer:
    """
    Class to manage auto-rolling and timers for various actions in a Discord bot interacting with the Mudae game.
    
    Attributes:
        claim_timer (datetime.datetime): Time of the next claim opportunity.
        roll_timer (datetime.datetime): Time of the next roll opportunity.
        daily_timer (datetime.datetime): Time of the next daily reward opportunity.
        claim_available (bool): Whether a claim is currently available or not.
        kakera_timer (datetime.datetime): Time of the next kakera opportunity.
        kakera_available (bool): Whether kakera loot is currently available or not.
        rolling_event (asyncio.Event): Event to signal when rolling is completed.
    """

    def __init__(self, next_claim, next_roll, next_daily, claim_available, next_kakera, kakera_available, channel, channel_id, client):
        """
        Initialize a Timer instance.

        Args:
            next_claim (datetime.datetime): Time of the next claim opportunity.
            next_roll (datetime.datetime): Time of the next roll opportunity.
            next_daily (datetime.datetime): Time of the next daily reward opportunity.
            claim_available (bool): Whether a claim is currently available.
            next_kakera (datetime.datetime): Time of the next kakera opportunity.
            kakera_available (bool): Whether kakera loot is currently available.
            channel (discord.TextChannel): Discord channel where the bot operates.
            channel_id (int): ID of the channel.
            client (discord.Client): The Discord client instance.
        """
        self.claim_timer = next_claim
        self.roll_timer = next_roll
        self.daily_timer = next_daily
        self.claim_available = claim_available
        self.kakera_available = kakera_available
        self.kakera_timer = next_kakera
        self.claim_duration = Config.Claim
        self.roll_duration = Config.Roll
        self.daily_duration = Config.Daily
        self.channel = channel
        self.channel_id = channel_id
        self.client = client
        self.rolling_event = asyncio.Event()

    def get_claim_availability(self):
        """
        Get the availability of claims.

        Returns:
            bool: True if claims are available, False otherwise.
        """
        return self.claim_available

    def set_claim_availability(self, available: bool):
        """
        Set the availability of claims.

        Args:
            available (bool): True if claims should be available, False otherwise.
        """
        self.claim_available = available

    def get_kakera_availability(self):
        """
        Get the availability of kakera.

        Returns:
            bool: True if kakera is available, False otherwise.
        """
        return self.kakera_available

    def set_kakera_availability(self, available: bool):
        """
        Set the availability of kakera.

        Args:
            available (bool): True if kakera should be available, False otherwise.
        """
        self.kakera_available = available

    async def wait_for_roll(self):
        """
        Asynchronously wait for the roll timer to elapse and trigger rolling.
        """
        while True:
            # Calculate time remaining until the next roll
            x = (self.roll_timer - datetime.datetime.now()).total_seconds()
            print(f'Roll timer sleeping for {x:.0f} seconds for {self.channel.name}')
            await asyncio.sleep(x)
            # Reset the roll timer
            self.roll_timer += datetime.timedelta(minutes=self.roll_duration)
            print(f'Rolls have been reset for {self.channel.name}')
            # Trigger rolling if claims are available or AlwaysRoll is enabled
            if Config.AlwaysRoll or self.claim_available:
                print(f'Initiating rolls for {self.channel.name}')
                await self.client.rolltest(self.channel_id)
            else:
                print(f'No claim available for {self.channel.name}, not rolling')

    async def wait_for_claim(self):
        """
        Asynchronously wait for the claim timer to elapse and reset the claim availability.
        """
        while True:
            # Calculate time remaining until the next claim
            x = (self.claim_timer - datetime.datetime.now()).total_seconds()
            print(f'Claim timer sleeping for {x:.0f} seconds for {self.channel.name}')
            await asyncio.sleep(x)
            # Reset the claim timer
            self.claim_timer += datetime.timedelta(minutes=self.claim_duration)
            print(f'Claims have been reset for {self.channel.name}')
            self.claim_available = True

    def is_last_min_claim_active(self) -> bool:
        """
        Check if the last-minute claim is active.

        Returns:
            bool: True if last-minute claim is active, False otherwise.
        """
        current_time = datetime.datetime.now()
        time_until_claim_reset = (self.claim_timer - current_time).total_seconds()
        return time_until_claim_reset <= 3600 and self.claim_available

    async def wait_for_daily(self):
        """
        Asynchronously wait for the daily timer to elapse and trigger daily commands.
        """
        while True:
            # Calculate time remaining until the daily reset
            x = (self.daily_timer - datetime.datetime.now()).total_seconds()
            if x > 0:  # Check if daily is already ready
                print(f'Daily timer sleeping for {x:.0f} seconds for {self.channel.name}')
                await asyncio.sleep(x)
                print(f'Daily has been reset, initiating daily commands for {self.channel.name}')
            else:
                print(f'Daily is ready, initiating daily commands for {self.channel.name}')
            # Reset the daily timer
            self.daily_timer += datetime.timedelta(minutes=self.daily_duration)
            # Send message $dk in all main channels
            main_channel = self.channel_id
            sub_channels = Config.Channels.get(main_channel, [])
            await self.send_messages([main_channel] + sub_channels, '$dk')
            await asyncio.sleep(3)  # Wait for processing
            # Send message $daily only in the first main channel
            if main_channel == list(Config.Channels.keys())[0]:
                await self.client.get_channel(main_channel).send('$daily')

    async def wait_for_p(self):
        """
        Asynchronously wait for 3 hours and send the $p command in the first main channel.
        """
        while True:
            await asyncio.sleep(3 * 60 * 60)  # Wait for 3 hours
            main_channel = self.channel_id
            sub_channels = Config.Channels.get(main_channel, [])
            # Send message $p only in the first main channel
            if main_channel == list(Config.Channels.keys())[0]:
                await self.send_messages([main_channel], '$p')

    async def send_messages(self, channels, message):
        """
        Send a message to a list of channels.

        Args:
            channels (list[int]): List of channel IDs to send the message to.
            message (str): The message to send.
        """
        main_channels = [channel_id for channel_id in channels if channel_id in Config.Channels]
        for channel_id in main_channels:
            await self.client.get_channel(channel_id).send(message)

    def get_timers(self):
        """
        Get the current timers.

        Returns:
            dict: A dictionary containing the remaining time for claim, roll, daily, and kakera timers.
        """
        current_time = datetime.datetime.now()
        return {
            'claim_timer': (self.claim_timer - current_time).total_seconds(),
            'roll_timer': (self.roll_timer - current_time).total_seconds(),
            'daily_timer': (self.daily_timer - current_time).total_seconds(),
            'kakera_timer': (self.kakera_timer - current_time).total_seconds()
        }
