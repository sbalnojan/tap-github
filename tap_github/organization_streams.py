"""User Stream types classes for tap-github."""

from typing import Any, Dict, Iterable, List, Optional

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_github.client import GitHubRestStream


class OrganizationStream(GitHubRestStream):
    """Defines a GitHub Organization Stream.
    API Reference: https://docs.github.com/en/rest/reference/orgs#get-an-organization
    """

    name = "organizations"
    path = "/orgs/{org}"

    @property
    def partitions(self) -> Optional[List[Dict]]:
        return [{"org": org} for org in self.config["organizations"]]

    def get_child_context(self, record: Dict, context: Optional[Dict]) -> dict:
        return {
            "org": record["login"],
        }

    def get_records(self, context: Optional[Dict]) -> Iterable[Dict[str, Any]]:
        """
        Override the parent method to allow skipping API calls
        if the stream is deselected and skip_parent_streams is True in config.
        This allows running the tap with fewer API calls and preserving
        quota when only syncing a child stream. Without this,
        the API call is sent but data is discarded.
        """
        if (
            not self.selected
            and "skip_parent_streams" in self.config
            and self.config["skip_parent_streams"]
            and context is not None
        ):
            # build a minimal mock record so that self._sync_records
            # can proceed with child streams
            yield {
                "org": context["org"],
            }
        else:
            yield from super().get_records(context)

    schema = th.PropertiesList(
        th.Property("login", th.StringType),
        th.Property("id", th.IntegerType),
        th.Property("node_id", th.StringType),
        th.Property("url", th.StringType),
        th.Property("repos_url", th.StringType),
        th.Property("events_url", th.StringType),
        th.Property("hooks_url", th.StringType),
        th.Property("issues_url", th.StringType),
        th.Property("members_url", th.StringType),
        th.Property("public_members_url", th.StringType),
        th.Property("avatar_url", th.StringType),
        th.Property("description", th.StringType),
    ).to_dict()


class TeamsStream(GitHubRestStream):
    """
    API Reference: https://docs.github.com/en/rest/reference/teams#list-teams
    """

    name = "teams"
    primary_keys = ["id"]
    path = "/orgs/{org}/teams"
    ignore_parent_replication_key = True
    parent_stream_type = OrganizationStream
    state_partitioning_keys = ["org"]

    def get_child_context(self, record: Dict, context: Optional[Dict]) -> dict:
        new_context = {"team_slug": record["slug"]}
        if context:
            return {
                **context,
                **new_context,
            }
        return new_context

    schema = th.PropertiesList(
        # Parent Keys
        th.Property("org", th.StringType),
        # Rest
        th.Property("id", th.IntegerType),
        th.Property("node_id", th.StringType),
        th.Property("url", th.StringType),
        th.Property("html_url", th.StringType),
        th.Property("name", th.StringType),
        th.Property("slug", th.StringType),
        th.Property("description", th.StringType),
        th.Property("privacy", th.StringType),
        th.Property("permission", th.StringType),
        th.Property("members_url", th.StringType),
        th.Property("repositories_url", th.StringType),
        th.Property(
            "parent",
            th.ObjectType(
                th.Property("id", th.IntegerType),
                th.Property("node_id", th.StringType),
                th.Property("url", th.StringType),
                th.Property("html_url", th.StringType),
                th.Property("name", th.StringType),
                th.Property("slug", th.StringType),
                th.Property("description", th.StringType),
                th.Property("privacy", th.StringType),
                th.Property("permission", th.StringType),
                th.Property("members_url", th.StringType),
                th.Property("repositories_url", th.StringType),
            ),
        ),
    ).to_dict()


class TeamMembersStream(GitHubRestStream):
    """
    API Reference: https://docs.github.com/en/rest/reference/teams#list-team-members
    """

    name = "team_members"
    primary_keys = ["id"]
    path = "/orgs/{org}/teams/{team_slug}/members"
    ignore_parent_replication_key = True
    parent_stream_type = TeamsStream
    state_partitioning_keys = ["team_slug", "org"]

    def get_child_context(self, record: Dict, context: Optional[Dict]) -> dict:
        new_context = {"username": record["login"]}
        if context:
            return {
                **context,
                **new_context,
            }
        return new_context

    schema = th.PropertiesList(
        # Parent keys
        th.Property("org", th.StringType),
        th.Property("team_slug", th.StringType),
        # Rest
        th.Property("login", th.StringType),
        th.Property("id", th.IntegerType),
        th.Property("node_id", th.StringType),
        th.Property("avatar_url", th.StringType),
        th.Property("gravatar_id", th.StringType),
        th.Property("url", th.StringType),
        th.Property("html_url", th.StringType),
        th.Property("type", th.StringType),
        th.Property("site_admin", th.BooleanType),
    ).to_dict()


class TeamRolesStream(GitHubRestStream):
    """
    API Reference: https://docs.github.com/en/rest/reference/teams#get-team-membership-for-a-user
    """

    name = "team_roles"
    path = "/orgs/{org}/teams/{team_slug}/memberships/{username}"
    ignore_parent_replication_key = True
    primary_keys = ["url"]
    parent_stream_type = TeamMembersStream
    state_partitioning_keys = ["username", "team_slug", "org"]

    schema = th.PropertiesList(
        # Parent keys
        th.Property("org", th.StringType),
        th.Property("team_slug", th.StringType),
        th.Property("username", th.StringType),
        # Rest
        th.Property("url", th.StringType),
        th.Property("role", th.StringType),
        th.Property("state", th.StringType),
    ).to_dict()
