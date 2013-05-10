from django.test import TransactionTestCase
from django.db import connection
from django.db.migrations.graph import MigrationGraph, CircularDependencyError
from django.db.migrations.loader import MigrationLoader


class GraphTests(TransactionTestCase):
    """
    Tests the digraph structure.
    """

    def test_simple_graph(self):
        """
        Tests a basic dependency graph:

        app_a:  0001 <-- 0002 <--- 0003 <-- 0004
                                 /
        app_b:  0001 <-- 0002 <-/
        """
        # Build graph
        graph = MigrationGraph()
        graph.add_dependency(("app_a", "0004"), ("app_a", "0003"))
        graph.add_dependency(("app_a", "0003"), ("app_a", "0002"))
        graph.add_dependency(("app_a", "0002"), ("app_a", "0001"))
        graph.add_dependency(("app_a", "0003"), ("app_b", "0002"))
        graph.add_dependency(("app_b", "0002"), ("app_b", "0001"))
        # Test root migration case
        self.assertEqual(
            graph.forwards_plan(("app_a", "0001")),
            [('app_a', '0001')],
        )
        # Test branch B only
        self.assertEqual(
            graph.forwards_plan(("app_b", "0002")),
            [("app_b", "0001"), ("app_b", "0002")],
        )
        # Test whole graph
        self.assertEqual(
            graph.forwards_plan(("app_a", "0004")),
            [('app_b', '0001'), ('app_b', '0002'), ('app_a', '0001'), ('app_a', '0002'), ('app_a', '0003'), ('app_a', '0004')],
        )
        # Test reverse to b:0002
        self.assertEqual(
            graph.backwards_plan(("app_b", "0002")),
            [('app_a', '0004'), ('app_a', '0003'), ('app_b', '0002')],
        )
        # Test roots and leaves
        self.assertEqual(
            graph.root_nodes(),
            set([('app_a', '0001'), ('app_b', '0001')]),
        )
        self.assertEqual(
            graph.leaf_nodes(),
            set([('app_a', '0004'), ('app_b', '0002')]),
        )

    def test_complex_graph(self):
        """
        Tests a complex dependency graph:

        app_a:  0001 <-- 0002 <--- 0003 <-- 0004
                      \        \ /         /
        app_b:  0001 <-\ 0002 <-X         /
                      \          \       /
        app_c:         \ 0001 <-- 0002 <-
        """
        # Build graph
        graph = MigrationGraph()
        graph.add_dependency(("app_a", "0004"), ("app_a", "0003"))
        graph.add_dependency(("app_a", "0003"), ("app_a", "0002"))
        graph.add_dependency(("app_a", "0002"), ("app_a", "0001"))
        graph.add_dependency(("app_a", "0003"), ("app_b", "0002"))
        graph.add_dependency(("app_b", "0002"), ("app_b", "0001"))
        graph.add_dependency(("app_a", "0004"), ("app_c", "0002"))
        graph.add_dependency(("app_c", "0002"), ("app_c", "0001"))
        graph.add_dependency(("app_c", "0001"), ("app_b", "0001"))
        graph.add_dependency(("app_c", "0002"), ("app_a", "0002"))
        # Test branch C only
        self.assertEqual(
            graph.forwards_plan(("app_c", "0002")),
            [('app_b', '0001'), ('app_c', '0001'), ('app_a', '0001'), ('app_a', '0002'), ('app_c', '0002')],
        )
        # Test whole graph
        self.assertEqual(
            graph.forwards_plan(("app_a", "0004")),
            [('app_b', '0001'), ('app_c', '0001'), ('app_a', '0001'), ('app_a', '0002'), ('app_c', '0002'), ('app_b', '0002'), ('app_a', '0003'), ('app_a', '0004')],
        )
        # Test reverse to b:0001
        self.assertEqual(
            graph.backwards_plan(("app_b", "0001")),
            [('app_a', '0004'), ('app_c', '0002'), ('app_c', '0001'), ('app_a', '0003'), ('app_b', '0002'), ('app_b', '0001')],
        )
        # Test roots and leaves
        self.assertEqual(
            graph.root_nodes(),
            set([('app_a', '0001'), ('app_b', '0001'), ('app_c', '0001')]),
        )
        self.assertEqual(
            graph.leaf_nodes(),
            set([('app_a', '0004'), ('app_b', '0002'), ('app_c', '0002')]),
        )

    def test_circular_graph(self):
        """
        Tests a circular dependency graph.
        """
        # Build graph
        graph = MigrationGraph()
        graph.add_dependency(("app_a", "0003"), ("app_a", "0002"))
        graph.add_dependency(("app_a", "0002"), ("app_a", "0001"))
        graph.add_dependency(("app_a", "0001"), ("app_b", "0002"))
        graph.add_dependency(("app_b", "0002"), ("app_b", "0001"))
        graph.add_dependency(("app_b", "0001"), ("app_a", "0003"))
        # Test whole graph
        self.assertRaises(
            CircularDependencyError,
            graph.forwards_plan, ("app_a", "0003"),
        )


class LoaderTests(TransactionTestCase):
    """
    Tests the disk and database loader.
    """

    def test_load(self):
        """
        Makes sure the loader can load the migrations for the test apps.
        """
        migration_loader = MigrationLoader(connection)
        graph = migration_loader.build_graph()
        self.assertEqual(
            graph.forwards_plan(("migrations", "0002_second")),
            [("migrations", "0001_initial"), ("migrations", "0002_second")],
        )
