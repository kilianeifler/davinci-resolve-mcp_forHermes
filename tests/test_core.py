import unittest

from resolve_mcp.core import (
    PAGE_NAMES,
    build_status,
    clip_names_from_folder,
    normalize_clip_names,
    normalize_import_paths,
    normalize_name,
    normalize_page,
    prepare_import_items,
)


class FakeTimeline:
    def GetName(self):
        return "Main"


class FakeProject:
    def GetName(self):
        return "Demo"

    def GetCurrentTimeline(self):
        return FakeTimeline()


class FakeResolve:
    def GetVersionString(self):
        return "21.1.1.10"

    def GetCurrentPage(self):
        return "edit"

    def GetCurrentProject(self):
        return FakeProject()


class CoreTests(unittest.TestCase):
    def test_normalize_page_accepts_only_resolve_pages_case_insensitively(self):
        self.assertEqual(normalize_page("EDIT"), "edit")
        self.assertEqual(set(PAGE_NAMES), {"media", "cut", "edit", "fusion", "color", "fairlight", "deliver"})
        with self.assertRaises(ValueError):
            normalize_page("settings")

    def test_build_status_reports_version_page_project_and_timeline(self):
        self.assertEqual(
            build_status(FakeResolve()),
            {
                "connected": True,
                "version": "21.1.1.10",
                "page": "edit",
                "project": "Demo",
                "timeline": "Main",
            },
        )

    def test_build_status_handles_no_open_project(self):
        class ResolveWithoutProject(FakeResolve):
            def GetCurrentProject(self):
                return None

        self.assertEqual(
            build_status(ResolveWithoutProject()),
            {
                "connected": True,
                "version": "21.1.1.10",
                "page": "edit",
                "project": None,
                "timeline": None,
            },
        )


    def test_normalize_import_paths_requires_existing_absolute_files(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "clip.mov"
            media.touch()
            self.assertEqual(normalize_import_paths([str(media)]), [str(media.resolve())])
            with self.assertRaises(ValueError):
                normalize_import_paths(["relative.mov"])
            with self.assertRaises(ValueError):
                normalize_import_paths([str(Path(directory) / "missing.mov")])

    def test_normalize_name_trims_and_rejects_blank_or_long_names(self):
        self.assertEqual(normalize_name("  New Cut  ", "timeline"), "New Cut")
        with self.assertRaises(ValueError):
            normalize_name("   ", "timeline")
        with self.assertRaises(ValueError):
            normalize_name("x" * 256, "timeline")

    def test_normalize_clip_names_requires_unique_non_empty_names(self):
        self.assertEqual(normalize_clip_names([" A.mov ", "B.mov"]), ["A.mov", "B.mov"])
        with self.assertRaises(ValueError):
            normalize_clip_names([])
        with self.assertRaises(ValueError):
            normalize_clip_names(["A.mov", "A.mov"])

    def test_prepare_import_items_uses_resolve_clip_info_shape(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "clip.mov"
            media.touch()
            self.assertEqual(
                prepare_import_items([str(media)]),
                [{"FilePath": str(media.resolve())}],
            )

    def test_clip_names_from_folder_applies_limit(self):
        class Item:
            def __init__(self, name):
                self.name = name

            def GetName(self):
                return self.name

        class Folder:
            def GetClipList(self):
                return [Item("A.mov"), Item("B.mov"), Item("C.mov")]

        self.assertEqual(clip_names_from_folder(Folder(), 2), ["A.mov", "B.mov"])


if __name__ == "__main__":
    unittest.main()
