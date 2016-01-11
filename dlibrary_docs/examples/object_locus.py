"""This is an example on how to work with locus objects.
"""
from dlibrary import Locus


def run():

    # Create a loci by specifying the origin.
    locus = Locus.create((0, 0))

    # You can also use length strings, or a mixture of both.
    locus = Locus.create(('10cm', '10cm'))
    locus = Locus.create(('10cm', 0))
