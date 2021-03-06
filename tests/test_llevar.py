from typing import List

import dill

import networkx as nx
import networkx.algorithms.isomorphism as iso
import pytest
from _pytest import monkeypatch
from mwparserfromhell.wikicode import Wikicode

import pyetymology.eobjects.apiresult
import pyetymology.eobjects.mwparserhelper
from pyetymology import wikt_api as wx, etyobjects, main
from pyetymology.etyobjects import MissingException
from pyetymology.tests import assets, asset_llevar
import mwparserfromhell as mwp

from pyetymology.tests.test_ import fetch_resdom, fetch_query, fetch_wikitext, is_eq__repr, patch_multiple_input


G_llevaron = nx.DiGraph()
nx.add_path(G_llevaron, ['$0L{es-verb form of|Spanish|llevar}', 'llevaron#Spanish$0'])
G_llevar = nx.DiGraph()
nx.add_path(G_llevar, ['$0{m|Latin|levō}', '$0{inh|Latin|levāre}', '$0{inh|Old Spanish|levar}', 'llevar#Spanish$0'])

class TestLlevar:
    # https://en.wiktionary.org/wiki/llevar
    def test_all_lang_sections(self, monkeypatch):
        monkeypatch.setattr('builtins.input', lambda _: "dummy_input")

        res, dom = fetch_resdom("llevar", redundance=True)
        sections = list(pyetymology.eobjects.mwparserhelper.all_lang_sections(dom, flat=False)) #type: List[List[Wikicode]]
        assert len(sections) == 2
        catalan = sections[0][0]
        spanish = sections[1][0]

        catalantxt = asset_llevar.catalan_txt
        spanishtxt = asset_llevar.spanish_txt

        assert str(catalan) == catalantxt
        assert str(spanish) == spanishtxt

        sections = list(pyetymology.eobjects.mwparserhelper.all_lang_sections(dom, flat=True)) #type: List[List[Wikicode]]
        assert len(sections) == 2
        catalan = sections[0]
        spanish = sections[1]
        assert str(catalan) == catalantxt
        assert str(spanish) == spanishtxt

        res, dom = fetch_resdom("llevar", redundance=False)
        sections = list(pyetymology.eobjects.mwparserhelper.all_lang_sections(dom)) #type: List[List[Wikicode]] # This has been changed, b/c the removal of antiredundance
        assert len(sections) == 2
        catalan = sections[0]
        spanish = sections[1]
        assert str(catalan) == '==Catalan==\n\n'
        assert str(spanish) == '==Spanish==\n\n'

    def test_section_detect(self):
        res, dom = fetch_resdom("llevar", redundance=True)
        secs = list(pyetymology.eobjects.mwparserhelper.sections_by_level(dom, 3)) # this is catalan
        assert secs == [['===Etymology===\nFrom {{inh|ca|la|levāre}}, present active infinitive of {{m|la|levō}}.\n\n'],
                        ['===Pronunciation===\n* {{ca-IPA}}\n\n'],
                        ['===Verb===\n{{ca-verb}}\n\n# to [[remove]], to [[take out]]\n\n====Conjugation====\n{{ca-conj-ar|llev}}\n\n====Derived terms====\n* {{l|ca|llevaneu}}\n* {{l|ca|llevar-se}}\n\n',
                            '====Conjugation====\n{{ca-conj-ar|llev}}\n\n',
                            '====Derived terms====\n* {{l|ca|llevaneu}}\n* {{l|ca|llevar-se}}\n\n'],
                        ['===Further reading===\n* {{R:IEC2}}\n* {{R:GDLC}}\n* {{R:DNV}}\n* {{R:DCVB}}\n\n----\n\n']]
    def test_flat_dom(self):
        res, dom = fetch_resdom("llevar", redundance=False)
        secs = list(pyetymology.eobjects.mwparserhelper.sections_by_level(dom, 3))
        assert secs == [['===Etymology===\nFrom {{inh|ca|la|levāre}}, present active infinitive of {{m|la|levō}}.\n\n'],
                        ['===Pronunciation===\n* {{ca-IPA}}\n\n'],
                        ['===Verb===\n{{ca-verb}}\n\n# to [[remove]], to [[take out]]\n\n',
                         '====Conjugation====\n{{ca-conj-ar|llev}}\n\n',
                         '====Derived terms====\n* {{l|ca|llevaneu}}\n* {{l|ca|llevar-se}}\n\n'],
                        ['===Further reading===\n* {{R:IEC2}}\n* {{R:GDLC}}\n* {{R:DNV}}\n* {{R:DCVB}}\n\n----\n\n']]


# [['===Etymology===\nFrom {{inh|ca|la|levāre}}, present active infinitive of {{m|la|levō}}.\n\n'], ['===Pronunciation===\n* {{ca-IPA}}\n\n'], ['===Verb===\n{{ca-verb}}\n\n# to [[remove]], to [[take out]]\n\n', '====Conjugation====\n{{ca-conj-ar|llev}}\n\n', '====Derived terms====\n* {{l|ca|llevaneu}}\n* {{l|ca|llevar-se}}\n\n'], ['===Further reading===\n* {{R:IEC2}}\n* {{R:GDLC}}\n* {{R:DNV}}\n* {{R:DCVB}}\n\n----\n\n']]
    def test_auto_lang(self, monkeypatch):
        res, dom = fetch_resdom("llevar", redundance=True)
        monkeypatch.setattr('builtins.input', lambda _: "Spanish")

        assert pyetymology.eobjects.mwparserhelper.reduce_to_one_lang(dom) == (list(
            pyetymology.eobjects.mwparserhelper.sections_by_lang(dom, "Spanish")), "Spanish")

        monkeypatch.setattr('builtins.input', lambda _: "Catalan")

        assert pyetymology.eobjects.mwparserhelper.reduce_to_one_lang(dom) == (list(
            pyetymology.eobjects.mwparserhelper.sections_by_lang(dom, "Catalan")), "Catalan")

    def test_auto_lang_failure(self, monkeypatch):

        res, dom = fetch_resdom("llevar", redundance=True)
        monkeypatch.setattr('builtins.input', lambda _: "English")
        with pytest.raises(MissingException) as e_info:
            pyetymology.eobjects.mwparserhelper.reduce_to_one_lang(dom) == (list(
                pyetymology.eobjects.mwparserhelper.sections_by_lang(dom, "Spanish")), "Spanish")

        assert e_info.value.G is None
        assert e_info.value.missing_thing == "language_section"


    def test_graph(self, monkeypatch):
        # etyobjects.reset_global_o_id()
        # monkeypatch.setattr('builtins.input', lambda _: "1") #Multiple Definitions
        fetched_Q = fetch_query("llevar", "Spanish")
        G = wx.graph(fetched_Q)
        global G_llevar
        G2 = G_llevar
        assert nx.is_isomorphic(G, G2)

        assert [repr(s) for s in G.nodes] == [s for s in reversed(list(G2.nodes))] # nx reversed the nodes for some reason
        assert [(repr(l), repr(r)) for l, r in G.edges] == [e for e in reversed(list(G2.edges))]
    # G: {llevar#Spanish$0: {}, $0{inh|Old Spanish|levar}: {llevar#Spanish$0: {}}, $0{inh|Latin|levāre}: {$0{inh|Old Spanish|levar}: {}}, $0{m|Latin|levō}: {$0{inh|Latin|levāre}: {}}}
    # edges: [($0{inh|Old Spanish|levar}, llevar#Spanish$0), ($0{inh|Latin|levāre}, $0{inh|Old Spanish|levar}), ($0{m|Latin|levō}, $0{inh|Latin|levāre})]
    # nodes: [llevar#Spanish$0, $0{inh|Old Spanish|levar}, $0{inh|Latin|levāre}, $0{m|Latin|levō}]

    def test_lemma_llevaron(self):
        # etyobjects.reset_global_o_id()

        fetched_Q = fetch_query("llevaron", "Spanish")
        G = wx.graph(fetched_Q)
        global G_llevaron
        G2 = G_llevaron # this is the repr() version of each node
        assert nx.is_isomorphic(G, G2)

        assert [repr(s) for s in G.nodes] == [s for s in reversed(list(G2.nodes))] # nx reversed the nodes for some reason
        assert [(repr(l), repr(r)) for l, r in G.edges] == [e for e in reversed(list(G2.edges))]

    def test_not_equal(self):
        fetched_Q = fetch_query("llevaron", "Spanish")
        Llevaron = wx.graph(fetched_Q)

        fetched_Q = fetch_query("llevar", "Spanish")
        Llevar = wx.graph(fetched_Q)

        assert not nx.is_isomorphic(Llevar, Llevaron)

    def test_connection(self, monkeypatch):

        Gs = main.mainloop(draw_graphs=False, test_queries=[("llevaron", "Spanish"), ("llevar", "Spanish")])
        # fetched_Q = fetch_query("llevaron", "Spanish")
        # GG = wx.graph(fetched_Q)
        assert len(Gs) == 3
        G1, G2, GG = Gs
        # _Q = fetch_query("llevar", "Spanish") # accept one input

        # G = wx.graph(_Q, replacement_origin=GG_origin)
        # assert GG_origin # llevaron should contain llevar
        global G_llevaron
        assert is_eq__repr(G1, G_llevaron)

        G_llevar_with_rorigin = nx.DiGraph()
        nx.add_path(G_llevar_with_rorigin, ['$1{m|Latin|levō}', '$1{inh|Latin|levāre}', '$1{inh|Old Spanish|levar}', '$0L{es-verb form of|Spanish|llevar}'])
        assert is_eq__repr(G2, G_llevar_with_rorigin)

        # GG2 -> GG
        G_composed = nx.DiGraph()
        nx.add_path(G_composed, ['$1{m|Latin|levō}', '$1{inh|Latin|levāre}', '$1{inh|Old Spanish|levar}', '$0L{es-verb form of|Spanish|llevar}', 'llevaron#Spanish$0'])

        # wx.draw_graph(G_composed) # DID: this fails. Why? Answer: blank node_colors.
        assert is_eq__repr(GG, G_composed)
        # TODO: origin indexing is broken with lemmas
# [$0L{es-verb form of|Spanish|llevar}, $0{inh|Old Spanish|levar}, $0{inh|Latin|levāre}, $0{m|Latin|levō}]
# GG2.nodes [llevaron#Spanish$0, $0L{es-verb form of|Spanish|llevar}, $0{inh|Old Spanish|levar}, $0{inh|Latin|levāre}, $0{m|Latin|levō}]
# G_composed.nodes ['$0{m|Latin|levō}', '$0{inh|Latin|levāre}', '$0{inh|Old Spanish|levar}', '$0L{es-verb form of|Spanish|llevar}', 'llevaron#Spanish$0']


