from __future__ import annotations

from typing import Dict, List, Any, Iterable, Optional
from datetime import datetime, timezone, timedelta
from tenacity import retry, wait_exponential, stop_after_attempt
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..config import settings
from ..models import SlackMessage
from ..state import RunState


class SlackService:
    def __init__(self, token: Optional[str] = None):
        token = token or settings.slack_token
        if not token:
            raise ValueError("Missing SLACK_TOKEN")
        self.client = WebClient(token=token)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(5)
    )
    def _safe_call(self, method: str, **kwargs) -> Dict[str, Any]:
        try:
            api = getattr(self.client, method)
            resp = api(**kwargs)
            return resp.data
        except SlackApiError as e:
            raise e

    def get_self_user_id(self) -> str:
        if settings.self_slack_user_id:
            return settings.self_slack_user_id
        auth = self._safe_call("auth_test")
        return auth.get("user_id")

    def list_conversations(self, types: Iterable[str]) -> List[Dict[str, Any]]:
        # Paginate conversations.list
        all_channels: List[Dict[str, Any]] = []
        cursor = None
        while True:
            resp = self._safe_call(
                "conversations_list",
                types=",".join(types),
                limit=1000,
                cursor=cursor,
                exclude_archived=True,
            )
            channels = resp.get("channels", [])
            all_channels.extend(channels)
            cursor = resp.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                break

        return all_channels

    def fetch_messages(
        self, channel_id: str, oldest: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        all_messages: List[Dict[str, Any]] = []
        cursor = None
        while True:
            kwargs: Dict[str, Any] = {"channel": channel_id, "limit": 1000}
            if oldest:
                kwargs["oldest"] = str(oldest)
            if cursor:
                kwargs["cursor"] = cursor
            resp = self._safe_call("conversations_history", **kwargs)
            messages = resp.get("messages", [])
            all_messages.extend(messages)
            cursor = resp.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                break
        return all_messages

    def fetch_thread_replies(
        self, channel_id: str, thread_ts: str, oldest: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        all_replies: List[Dict[str, Any]] = []
        cursor = None
        while True:
            kwargs: Dict[str, Any] = {
                "channel": channel_id,
                "ts": thread_ts,
                "limit": 1000,
            }
            if cursor:
                kwargs["cursor"] = cursor
            resp = self._safe_call("conversations_replies", **kwargs)
            msgs = resp.get("messages", [])
            if oldest:
                msgs = [m for m in msgs if float(m.get("ts", 0)) >= oldest]
            all_replies.extend(msgs)
            cursor = resp.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                break
        return all_replies

    def get_channel_name_map(self, channels: List[Dict[str, Any]]) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for ch in channels:
            cid = ch.get("id")
            name = ch.get("name") or ch.get("user") or ch.get("id")
            mapping[cid] = name
        return mapping

    def send_message(
        self, channel_id: str, text: str, blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel."""
        kwargs = {"channel": channel_id, "text": text}
        if blocks:
            kwargs["blocks"] = blocks
        return self._safe_call("chat_postMessage", **kwargs)

    def open_dm(self, user_id: str) -> str:
        """Open a DM conversation with a user and return the channel ID."""
        resp = self._safe_call("conversations_open", users=user_id)
        return resp.get("channel", {}).get("id")

    def send_dm(
        self, user_id: str, text: str, blocks: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send a direct message to a user."""
        dm_channel = self.open_dm(user_id)
        return self.send_message(dm_channel, text, blocks)

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users in the workspace."""
        all_users: List[Dict[str, Any]] = []
        cursor = None
        while True:
            kwargs: Dict[str, Any] = {"limit": 200}
            if cursor:
                kwargs["cursor"] = cursor
            resp = self._safe_call("users_list", **kwargs)
            users = resp.get("members", [])
            all_users.extend(users)
            cursor = resp.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                break
        return all_users

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a Slack user by their email address."""
        try:
            resp = self._safe_call("users_lookupByEmail", email=email)
            return resp.get("user")
        except SlackApiError as e:
            if e.response.get("error") == "users_not_found":
                return None
            raise

    # To do: Change this.
    # We should fetch messages from the last 24h, load it in the databases and then filter which ones are relevant to the user.
    # once we have the messages, get the thread replies and add them to the messages.

    def collect_relevant_messages(
        self,
        oldest_by_channel: Optional[Dict[str, float]] = None,
        global_oldest: Optional[float] = None,
        include_threads: bool = False,
        target_channel_ids: Optional[List[str]] = None,
    ) -> List[SlackMessage]:

        oldest_by_channel = oldest_by_channel or {}

        self_id = self.get_self_user_id()

        # Get all channels first to build name mapping
        all_channels = self.list_conversations(
            types=["public_channel", "private_channel", "im", "mpim"]
        )

        # Filter channels based on target_channel_ids if provided
        if target_channel_ids:
            # Include target channels + DMs/MPIMs
            channels = [
                ch
                for ch in all_channels
                if ch.get("id") in target_channel_ids
                or ch.get("is_im")
                or ch.get("is_mpim")
            ]
        else:
            # General behavior: process all channels
            channels = all_channels

        name_map = self.get_channel_name_map(channels)

        relevant: List[SlackMessage] = []

        mention_token = f"<@{self_id}>"

        for ch in channels:
            cid = ch.get("id")
            is_dm = ch.get("is_im") or ch.get("is_mpim") or False
            oldest = oldest_by_channel.get(cid)
            if oldest is None and global_oldest is not None:
                oldest = global_oldest
            msgs = self.fetch_messages(cid, oldest=oldest)
            for m in msgs:
                text = m.get("text") or ""
                ts = float(m.get("ts", 0))
                user = m.get("user") or m.get("bot_id")
                thread_ts = m.get("thread_ts")
                include = False
                if is_dm:
                    include = True  # all DMs / MPIMs involve me
                elif target_channel_ids and cid in target_channel_ids:
                    include = True  # include all messages from target channels
                else:
                    if user == self_id or mention_token in text:
                        include = True
                if include:
                    relevant.append(
                        SlackMessage(
                            channel_id=cid,
                            channel_name=name_map.get(cid, cid),
                            ts=ts,
                            user=user,
                            text=text,
                            is_dm=bool(is_dm),
                            thread_ts=(
                                thread_ts
                                if thread_ts
                                else (m.get("ts") if m.get("reply_count") else None)
                            ),
                            is_thread_reply=bool(
                                thread_ts and thread_ts != m.get("ts")
                            ),
                        )
                    )
                # Optionally fetch thread replies
                if include_threads and (
                    m.get("reply_count") or (thread_ts and thread_ts == m.get("ts"))
                ):
                    root_ts = thread_ts or m.get("ts")
                    replies = self.fetch_thread_replies(cid, root_ts, oldest=oldest)
                    for r in replies:
                        if r.get("ts") == root_ts:
                            continue  # skip root duplicate
                        r_text = r.get("text") or ""
                        r_user = r.get("user") or r.get("bot_id")
                        r_ts = float(r.get("ts", 0))
                        r_include = False
                        if is_dm:
                            r_include = True
                        elif target_channel_ids and cid in target_channel_ids:
                            r_include = (
                                True  # include all thread replies from target channels
                            )
                        else:
                            if r_user == self_id or mention_token in r_text:
                                r_include = True
                        if r_include:
                            relevant.append(
                                SlackMessage(
                                    channel_id=cid,
                                    channel_name=name_map.get(cid, cid),
                                    ts=r_ts,
                                    user=r_user,
                                    text=r_text,
                                    is_dm=bool(is_dm),
                                    thread_ts=root_ts,
                                    is_thread_reply=True,
                                )
                            )
        relevant.sort(key=lambda x: x.ts)
        return relevant

    def ingest(
        self,
        include_threads: bool = True,
        target_channel_ids: Optional[List[str]] = None,
        force_last_24h: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete Slack ingestion: fetch new messages AND store in database.

        Behavior:
        - If force_last_24h=True or target_channel_ids provided: Always fetch last 24h
        - If state exists and not forcing: Fetch only NEW messages since last sync (incremental)
        - If no state: Fetch last 24h (initial run)
        - Automatically stores in database and updates state

        Args:
            include_threads: Whether to include thread replies
            target_channel_ids: Optional list of channel IDs to specifically monitor.
                              If provided, all messages from these channels are included.
                              If None, uses general filtering (DMs, mentions, etc.)
            force_last_24h: If True, always fetch last 24h regardless of state (useful for dev workflows)

        Returns:
            Dict with ingestion stats (fetched, stored, mode, etc.)
        """
        from ..storage.db import Database

        # Load state
        state = RunState.load()

        # Determine what to fetch
        # When using target channels (dev config) or force_last_24h, always fetch last 24h
        if force_last_24h or target_channel_ids:
            # Always fetch last 24h when using dev config or forced
            now = datetime.now(timezone.utc)
            oldest_dt = now - timedelta(hours=24)
            oldest_ts = oldest_dt.timestamp()
            messages = self.collect_relevant_messages(
                global_oldest=oldest_ts,
                include_threads=include_threads,
                target_channel_ids=target_channel_ids,
            )
            mode = "last_24h" if target_channel_ids else "initial"
        elif state.per_channel_last_ts:
            # Incremental: fetch since last sync per channel
            messages = self.collect_relevant_messages(
                oldest_by_channel=state.per_channel_last_ts,
                include_threads=include_threads,
                target_channel_ids=target_channel_ids,
            )
            mode = "incremental"
        else:
            # Initial: fetch last 24h
            now = datetime.now(timezone.utc)
            oldest_dt = now - timedelta(hours=24)
            oldest_ts = oldest_dt.timestamp()
            messages = self.collect_relevant_messages(
                global_oldest=oldest_ts,
                include_threads=include_threads,
                target_channel_ids=target_channel_ids,
            )
            mode = "initial"

        if not messages:
            return {
                "fetched": 0,
                "stored": 0,
                "db_stats": Database().get_stats(),
                "mode": mode,
                "channels_updated": 0,
            }

        # Store in database
        db = Database()
        stored = db.insert_messages(messages)

        # Update state with newest timestamps
        newest_by_channel: Dict[str, float] = {}
        for msg in messages:
            newest_by_channel[msg.channel_id] = max(
                newest_by_channel.get(msg.channel_id, 0.0), msg.ts
            )

        for channel_id, ts in newest_by_channel.items():
            state.update_channel_ts(channel_id, ts)

        state.save()

        # Get database stats
        stats = db.get_stats()

        return {
            "fetched": len(messages),
            "stored": stored,
            "db_stats": stats,
            "mode": mode,
            "channels_updated": len(newest_by_channel),
        }


def run_ingestion(
    include_threads: bool = False,
    target_channel_ids: Optional[List[str]] = None,
    force_last_24h: bool = False,
) -> Dict[str, Any]:
    """
    Main entry point for Slack ingestion.

    Run this to ingest new Slack messages into the database.
    Can be called from CLI or run directly.

    Args:
        include_threads: Whether to fetch thread replies (slower, may hit rate limits)
        target_channel_ids: Optional list of channel IDs to specifically monitor.
                          If provided, all messages from these channels are included.
                          If None, uses general filtering (DMs, mentions, etc.)
        force_last_24h: If True, always fetch last 24h regardless of state.
                       When target_channel_ids is provided, this is automatically True.

    Returns:
        Dict with ingestion results
    """
    service = SlackService()
    # When using target channels, automatically force last 24h
    if target_channel_ids:
        force_last_24h = True
    return service.ingest(
        include_threads=include_threads,
        target_channel_ids=target_channel_ids,
        force_last_24h=force_last_24h,
    )


if __name__ == "__main__":
    # Allow running this file directly for ingestion
    import sys

    # Optionally use dev config if available
    target_channel_ids = None
    try:
        # Try absolute import first (when running as module)
        from app.workflows.dev.config import SLACK_TARGET_CHANNEL_IDS

        target_channel_ids = SLACK_TARGET_CHANNEL_IDS
    except ImportError:
        try:
            # Try relative import (when running as script)
            from ...workflows.dev.config import SLACK_TARGET_CHANNEL_IDS

            target_channel_ids = SLACK_TARGET_CHANNEL_IDS
        except ImportError:
            # Dev config not available, use general behavior
            pass

    # When using dev config, include threads by default
    include_threads = "--threads" in sys.argv or target_channel_ids is not None

    print("🔄 Running Slack ingestion...")
    if target_channel_ids:
        print(f"📋 Using dev config: {len(target_channel_ids)} target channels")
        print(f"🧵 Including threads: {include_threads}")
        print(f"⏰ Fetching last 24h from target channels")
    result = run_ingestion(
        include_threads=include_threads, target_channel_ids=target_channel_ids
    )

    mode_emoji = {
        "initial": "📥 Initial",
        "incremental": "🔄 Incremental",
        "last_24h": "⏰ Last 24h",
    }
    print(f"\n{mode_emoji.get(result['mode'], '🔄')} {result['mode'].title()}")
    print(f"✓ Fetched: {result['fetched']}")
    print(f"✓ Stored: {result['stored']}")
    print(f"✓ Channels: {result['channels_updated']}")
    print(f"\n📊 Total in DB: {result['db_stats']['total']}")
