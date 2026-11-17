import unittest

from resolve_mcp.server import mcp


class MCPServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_registers_only_the_documented_resolve_tools(self):
        tools = await mcp.list_tools()
        names = {tool.name for tool in tools}
        self.assertEqual(
            names,
            {
                "resolve_status",
                "list_projects",
                "list_media_pool",
                "set_page",
                "create_project",
                "save_current_project",
                "import_media",
                "create_empty_timeline",
                "append_media_pool_clips",
            },
        )
        self.assertFalse(names.intersection({"delete_project", "render", "export"}))


if __name__ == "__main__":
    unittest.main()
