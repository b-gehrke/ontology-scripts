import unittest

from pyhornedowl.model import *

from axiompatterns import normalise, Context


class NormaliseTestCase(unittest.TestCase):
    def test_normalise_class(self):
        value = Class(IRI.parse("http://example.org/A"))

        ctx = Context()

        actual = normalise(value, ctx)
        expected = Class(IRI.parse("C0"))

        self.assertEqual(expected, actual)

        actual = normalise(value, ctx)
        expected = Class(IRI.parse("C0"))

        self.assertEqual(expected, actual)

    def test_normalise_classes(self):
        c1 = Class(IRI.parse("http://example.org/A"))
        c2 = Class(IRI.parse("http://example.org/B"))

        ctx = Context()

        actual = normalise(c1, ctx)
        expected = Class(IRI.parse("C0"))
        self.assertEqual(expected, actual)

        actual = normalise(c2, ctx)
        expected = Class(IRI.parse("C1"))
        self.assertEqual(expected, actual)

    def test_normalise_object_property(self):
        value = ObjectProperty(IRI.parse("http://example.org/property"))

        ctx = Context()

        actual = normalise(value, ctx)
        expected = ObjectProperty(IRI.parse("R0"))
        self.assertEqual(expected, actual)

        actual = normalise(value, ctx)
        expected = ObjectProperty(IRI.parse("R0"))
        self.assertEqual(expected, actual)

    def test_normalise_object_properties(self):
        p1 = ObjectProperty(IRI.parse("http://example.org/property1"))
        p2 = ObjectProperty(IRI.parse("http://example.org/property2"))

        ctx = Context()

        actual = normalise(p1, ctx)
        expected = ObjectProperty(IRI.parse("R0"))
        self.assertEqual(expected, actual)

        actual = normalise(p2, ctx)
        expected = ObjectProperty(IRI.parse("R1"))
        self.assertEqual(expected, actual)

    def test_normalise_data_property(self):
        value = DataProperty(IRI.parse("http://example.org/property"))

        ctx = Context()

        actual = normalise(value, ctx)
        expected = DataProperty(IRI.parse("R0"))
        self.assertEqual(expected, actual)

        actual = normalise(value, ctx)
        expected = DataProperty(IRI.parse("R0"))
        self.assertEqual(expected, actual)

    def test_normalise_data_properties(self):
        p1 = DataProperty(IRI.parse("http://example.org/property1"))
        p2 = DataProperty(IRI.parse("http://example.org/property2"))

        ctx = Context()

        actual = normalise(p1, ctx)
        expected = DataProperty(IRI.parse("R0"))
        self.assertEqual(expected, actual)

        actual = normalise(p2, ctx)
        expected = DataProperty(IRI.parse("R1"))
        self.assertEqual(expected, actual)

    def test_normalise_class_expression(self):
        c1, ec1 = Class(IRI.parse("http://example.org/A")), Class(IRI.parse("C0"))
        c2, ec2 = Class(IRI.parse("http://example.org/B")), Class(IRI.parse("C1"))
        op1, eop1 = ObjectProperty(IRI.parse("http://example.org/object-property1")), ObjectProperty(IRI.parse("R0"))

        ctx = Context()

        actual = normalise(c1 & c2, ctx)
        expected = ec1 & ec2
        self.assertEqual(expected, actual, "intersection")

        actual = normalise(c1 | c2, ctx)
        expected = ec1 | ec2
        self.assertEqual(expected, actual, "union")

        actual = normalise(op1.some(c1), ctx)
        expected = eop1.some(ec1)
        self.assertEqual(expected, actual, "object some")

        actual = normalise(op1.only(c1), ctx)
        expected = eop1.only(ec1)
        self.assertEqual(expected, actual, "object all")

        actual = normalise(op1.min(1, c1), ctx)
        expected = eop1.min(1, ec1)
        self.assertEqual(expected, actual, "object min")

        actual = normalise(op1.max(1, c1), ctx)
        expected = eop1.max(1, ec1)
        self.assertEqual(expected, actual, "object max")

        actual = normalise(op1.exact(1, c1), ctx)
        expected = eop1.exact(1, ec1)
        self.assertEqual(expected, actual, "object exact")

    def test_normalise_component(self):
        c1, ec1 = Class(IRI.parse("http://example.org/A")), Class(IRI.parse("C0"))
        c2, ec2 = Class(IRI.parse("http://example.org/B")), Class(IRI.parse("C1"))
        op1, eop1 = ObjectProperty(IRI.parse("http://example.org/object-property1")), ObjectProperty(IRI.parse("R0"))

        ctx = Context()

        actual = normalise(SubClassOf(c1, op1.some(c2)), ctx)
        expected = SubClassOf(ec1, eop1.some(ec2))
        self.assertEqual(expected, actual, "A SC R some B")





if __name__ == '__main__':
    unittest.main()
