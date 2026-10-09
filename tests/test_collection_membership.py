"""Collection management: add/remove photos, parent sets, delete collection/set."""

from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from cli.main import cli
from lightroom_sdk.schema import COMMAND_SCHEMAS
from lightroom_sdk.validation import ValidationError, validate_params
from mcp_server.tool_registry import create_tool_function, sanitize_tool_name

NEW_COMMANDS = {
    "catalog.addPhotosToCollection": ("catalog.add-to-collection", "lr_catalog_add_photos_to_collection"),
    "catalog.removePhotosFromCollection": (
        "catalog.remove-from-collection",
        "lr_catalog_remove_photos_from_collection",
    ),
    "catalog.deleteCollection": ("catalog.delete-collection", "lr_catalog_delete_collection"),
    "catalog.deleteCollectionSet": ("catalog.delete-collection-set", "lr_catalog_delete_collection_set"),
}


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_bridge():
    with patch("cli.helpers.get_bridge") as mock_get_bridge:
        bridge = AsyncMock()
        bridge.send_command.return_value = {"id": "1", "success": True, "result": {}}
        mock_get_bridge.return_value = bridge
        yield bridge


class TestSchemas:
    @pytest.mark.parametrize("command", list(NEW_COMMANDS))
    def test_schema_registered(self, command):
        cli_path, tool_name = NEW_COMMANDS[command]
        schema = COMMAND_SCHEMAS[command]
        assert schema.cli_path == cli_path
        assert schema.mutating is True
        assert schema.supports_dry_run is True
        assert sanitize_tool_name(command) == tool_name

    def test_delete_commands_are_destructive(self):
        assert COMMAND_SCHEMAS["catalog.deleteCollection"].risk_level == "destructive"
        assert COMMAND_SCHEMAS["catalog.deleteCollectionSet"].risk_level == "destructive"

    def test_membership_commands_are_write(self):
        assert COMMAND_SCHEMAS["catalog.addPhotosToCollection"].risk_level == "write"
        assert COMMAND_SCHEMAS["catalog.removePhotosFromCollection"].risk_level == "write"

    @pytest.mark.parametrize("command", ["catalog.createCollection", "catalog.createCollectionSet"])
    def test_create_accepts_optional_parent(self, command):
        params = {p.name: p for p in COMMAND_SCHEMAS[command].params}
        assert params["parentId"].required is False
        assert params["parentName"].required is False
        assert "id" in COMMAND_SCHEMAS[command].response_fields

    def test_collections_lists_sets(self):
        assert "collectionSets" in COMMAND_SCHEMAS["catalog.getCollections"].response_fields

    def test_add_requires_photo_ids(self):
        with pytest.raises(ValidationError):
            validate_params("catalog.addPhotosToCollection", {"collectionId": 1})

    def test_add_coerces_collection_id(self):
        result = validate_params("catalog.addPhotosToCollection", {"photoIds": ["1"], "collectionId": "42"})
        assert result["collectionId"] == 42


class TestCLI:
    def test_add_by_id(self, runner, mock_bridge):
        result = runner.invoke(cli, ["catalog", "add-to-collection", "11", "12", "--collection-id", "5"])
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with(
            "catalog.addPhotosToCollection",
            {"photoIds": ["11", "12"], "collectionId": 5},
            timeout=60.0,
        )

    def test_add_by_name_and_parent(self, runner, mock_bridge):
        result = runner.invoke(
            cli,
            ["catalog", "add-to-collection", "11", "--collection", "Picks", "--parent-name", "2026"],
        )
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with(
            "catalog.addPhotosToCollection",
            {"photoIds": ["11"], "collectionName": "Picks", "parentName": "2026"},
            timeout=60.0,
        )

    def test_add_requires_photo_ids(self, runner):
        result = runner.invoke(cli, ["catalog", "add-to-collection", "--collection-id", "5"])
        assert result.exit_code != 0

    def test_remove(self, runner, mock_bridge):
        result = runner.invoke(cli, ["catalog", "remove-from-collection", "11", "--collection-id", "5"])
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with(
            "catalog.removePhotosFromCollection",
            {"photoIds": ["11"], "collectionId": 5},
            timeout=60.0,
        )

    def test_add_json_input(self, runner, mock_bridge):
        result = runner.invoke(
            cli,
            ["catalog", "add-to-collection", "0", "--json", '{"photoIds": ["7"], "collectionId": 3}'],
        )
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with(
            "catalog.addPhotosToCollection", {"photoIds": ["7"], "collectionId": 3}, timeout=60.0
        )

    def test_add_dry_run_does_not_send(self, runner, mock_bridge):
        result = runner.invoke(
            cli, ["-o", "json", "catalog", "add-to-collection", "11", "--collection-id", "5", "--dry-run"]
        )
        assert result.exit_code == 0
        assert '"dry_run": true' in result.output
        mock_bridge.send_command.assert_not_called()

    def test_create_collection_with_parent_id(self, runner, mock_bridge):
        result = runner.invoke(cli, ["catalog", "create-collection", "Picks", "--parent-id", "9"])
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with(
            "catalog.createCollection", {"name": "Picks", "parentId": 9}, timeout=30.0
        )

    def test_create_collection_without_parent_is_unchanged(self, runner, mock_bridge):
        result = runner.invoke(cli, ["catalog", "create-collection", "Picks"])
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with("catalog.createCollection", {"name": "Picks"}, timeout=30.0)

    def test_create_collection_set_with_parent_name(self, runner, mock_bridge):
        result = runner.invoke(cli, ["catalog", "create-collection-set", "Day 1", "--parent-name", "Trip"])
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with(
            "catalog.createCollectionSet", {"name": "Day 1", "parentName": "Trip"}, timeout=30.0
        )

    @pytest.mark.parametrize(
        "subcommand,command,param",
        [
            ("delete-collection", "catalog.deleteCollection", "collectionId"),
            ("delete-collection-set", "catalog.deleteCollectionSet", "collectionSetId"),
        ],
    )
    def test_delete_requires_confirm(self, runner, mock_bridge, subcommand, command, param):
        result = runner.invoke(cli, ["catalog", subcommand, "5"])
        assert result.exit_code == 2
        assert "CONFIRMATION_REQUIRED" in result.output
        mock_bridge.send_command.assert_not_called()

        result = runner.invoke(cli, ["catalog", subcommand, "5", "--confirm"])
        assert result.exit_code == 0, result.output
        mock_bridge.send_command.assert_called_once_with(command, {param: 5}, timeout=30.0)

    def test_delete_dry_run_without_confirm(self, runner, mock_bridge):
        result = runner.invoke(cli, ["-o", "json", "catalog", "delete-collection", "5", "--dry-run"])
        assert result.exit_code == 0
        assert '"risk_level": "destructive"' in result.output
        mock_bridge.send_command.assert_not_called()


class TestMCP:
    @pytest.mark.asyncio
    async def test_add_tool_forwards_params(self):
        connection = AsyncMock()
        connection.execute.return_value = {"added": 1}
        tool = create_tool_function(COMMAND_SCHEMAS["catalog.addPhotosToCollection"], connection)
        await tool(photoIds=["1"], collectionName="Picks", parentName="Trip")
        connection.execute.assert_called_once_with(
            command="catalog.addPhotosToCollection",
            params={"photoIds": ["1"], "collectionName": "Picks", "parentName": "Trip"},
            timeout=60.0,
            mutating=True,
        )

    @pytest.mark.asyncio
    async def test_delete_tool_dry_run(self):
        connection = AsyncMock()
        tool = create_tool_function(COMMAND_SCHEMAS["catalog.deleteCollection"], connection)
        result = await tool(collectionId=5, dry_run=True)
        assert result["dry_run"] is True
        assert result["risk_level"] == "destructive"
        connection.execute.assert_not_called()
