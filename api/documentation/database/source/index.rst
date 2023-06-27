.. eNDP-database documentation master file, created by
   sphinx-quickstart on Mon Apr 17 17:46:34 2023.

=======================================================
Base de données e-NDP
=======================================================

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: contents:

.. contents:: Table des matières
   :local:
   :depth: 2

.. currentmodule:: models

Schéma général
==============

.. image:: _static/graph_db_endp.png
   :align: center
   :width: 100%

Remarques générales
===================

.. note:: Le ``_`` devant les attributs signifie qu'ils sont générés de manière automatique lors d'une injection en base.
.. note:: [REQ.] indique que le champ est obligatoire. [OPT.] indique que le champ est optionnel.


Tables principales
==================

.. autoclass:: Person
   :show-inheritance:

.. autoclass:: Event
   :show-inheritance:

.. autoclass:: ThesaurusTerm
   :show-inheritance:

.. autoclass:: PlacesTerm
   :show-inheritance:


Tables de relations
===================

.. autoclass:: PersonHasKbLinks
   :members:
   :show-inheritance:

.. autoclass:: PersonHasFamilyRelationshipType
   :members:
   :show-inheritance:

Listes énumérées
================


.. autoclass:: FamilyRelationshipLabels
   :members:
   :show-inheritance:

.. autoclass:: KnowledgeBaseLabels
   :members:
   :show-inheritance:

.. autoclass:: EventTypeLabels
    :members:
    :show-inheritance:

.. autoclass:: ThesaurusTopicLabels
    :members:
    :show-inheritance:

.. autoclass:: ThesaurusPlacesTopicsLabels
    :members:
    :show-inheritance:


Licence
=======

CC-BY-SA 4.0

.. raw:: html

    <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Licence Creative Commons" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />Le modèle de données e-NDP est mis à disposition selon les termes de la <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Licence Creative Commons Attribution -  Partage dans les Mêmes Conditions 4.0 International</a>.

.. container:: twocol

   .. container:: leftside

      .. image:: _static/Logo_enc.png
         :width: 100
         :alt: École nationale des chartes

   .. container:: rightside

       .. image:: _static/Logo_anr.png
         :width: 100
         :alt: Agence nationale de la recherche

Ce travail a bénéficié d’une aide de l’État gérée par l’Agence Nationale de la
Recherche.
