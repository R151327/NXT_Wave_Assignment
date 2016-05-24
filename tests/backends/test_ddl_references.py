from django.db.backends.ddl_references import (
    Columns, ForeignKeyName, IndexName, Statement, Table,
)
from django.test import SimpleTestCase


class TableTests(SimpleTestCase):
    def setUp(self):
        self.reference = Table('table', lambda table: table.upper())

    def test_references_table(self):
        self.assertIs(self.reference.references_table('table'), True)
        self.assertIs(self.reference.references_table('other'), False)

    def test_repr(self):
        self.assertEqual(repr(self.reference), "<Table 'TABLE'>")

    def test_str(self):
        self.assertEqual(str(self.reference), 'TABLE')


class ColumnsTests(TableTests):
    def setUp(self):
        self.reference = Columns(
            'table', ['first_column', 'second_column'], lambda column: column.upper()
        )

    def test_references_column(self):
        self.assertIs(self.reference.references_column('other', 'first_column'), False)
        self.assertIs(self.reference.references_column('table', 'third_column'), False)
        self.assertIs(self.reference.references_column('table', 'first_column'), True)

    def test_repr(self):
        self.assertEqual(repr(self.reference), "<Columns 'FIRST_COLUMN, SECOND_COLUMN'>")

    def test_str(self):
        self.assertEqual(str(self.reference), 'FIRST_COLUMN, SECOND_COLUMN')


class IndexNameTests(ColumnsTests):
    def setUp(self):
        def create_index_name(table_name, column_names, suffix):
            return ', '.join("%s_%s_%s" % (table_name, column_name, suffix) for column_name in column_names)
        self.reference = IndexName(
            'table', ['first_column', 'second_column'], 'suffix', create_index_name
        )

    def test_repr(self):
        self.assertEqual(repr(self.reference), "<IndexName 'table_first_column_suffix, table_second_column_suffix'>")

    def test_str(self):
        self.assertEqual(str(self.reference), 'table_first_column_suffix, table_second_column_suffix')


class ForeignKeyNameTests(IndexNameTests):
    def setUp(self):
        def create_foreign_key_name(table_name, column_names, suffix):
            return ', '.join("%s_%s_%s" % (table_name, column_name, suffix) for column_name in column_names)
        self.reference = ForeignKeyName(
            'table', ['first_column', 'second_column'],
            'to_table', ['to_first_column', 'to_second_column'],
            '%(to_table)s_%(to_column)s_fk',
            create_foreign_key_name,
        )

    def test_references_table(self):
        super().test_references_table()
        self.assertIs(self.reference.references_table('to_table'), True)

    def test_references_column(self):
        super().test_references_column()
        self.assertIs(self.reference.references_column('to_table', 'second_column'), False)
        self.assertIs(self.reference.references_column('to_table', 'to_second_column'), True)

    def test_repr(self):
        self.assertEqual(
            repr(self.reference),
            "<ForeignKeyName 'table_first_column_to_table_to_first_column_fk, "
            "table_second_column_to_table_to_first_column_fk'>"
        )

    def test_str(self):
        self.assertEqual(
            str(self.reference),
            'table_first_column_to_table_to_first_column_fk, '
            'table_second_column_to_table_to_first_column_fk'
        )


class MockReference(object):
    def __init__(self, representation, referenced_tables, referenced_columns):
        self.representation = representation
        self.referenced_tables = referenced_tables
        self.referenced_columns = referenced_columns

    def references_table(self, table):
        return table in self.referenced_tables

    def references_column(self, table, column):
        return (table, column) in self.referenced_columns

    def __str__(self):
        return self.representation


class StatementTests(SimpleTestCase):
    def test_references_table(self):
        statement = Statement('', reference=MockReference('', {'table'}, {}), non_reference='')
        self.assertIs(statement.references_table('table'), True)
        self.assertIs(statement.references_table('other'), False)

    def test_references_column(self):
        statement = Statement('', reference=MockReference('', {}, {('table', 'column')}), non_reference='')
        self.assertIs(statement.references_column('table', 'column'), True)
        self.assertIs(statement.references_column('other', 'column'), False)

    def test_repr(self):
        reference = MockReference('reference', {}, {})
        statement = Statement("%(reference)s - %(non_reference)s", reference=reference, non_reference='non_reference')
        self.assertEqual(repr(statement), "<Statement 'reference - non_reference'>")

    def test_str(self):
        reference = MockReference('reference', {}, {})
        statement = Statement("%(reference)s - %(non_reference)s", reference=reference, non_reference='non_reference')
        self.assertEqual(str(statement), 'reference - non_reference')
