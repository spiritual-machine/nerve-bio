"""
================================================================================
Dublin Core Metadata for this file
================================================================================
DC.Title:           PDF Ingestion Module for Project NERVE
DC.Creator:         Autumn Denny
DC.Subject:         Natural Language Processing, PDF Parsing, Data Ingestion, PyMuPDF
DC.Description:     This script contains the core functions to parse text and
                    metadata from scientific PDF documents. It serves as the
                    first step in the NERVE knowledge extraction pipeline.
DC.Publisher:       [Your GitHub Username or Lab Name, e.g., autumn-denny-dev]
DC.Contributor:     [e.g., Name of advisor if they contributed to the code]
DC.Date:            2025-08-01
DC.Type:            Software, Python Script
DC.Format:          text/x-python
DC.Identifier:      /nerve/ingestion.py
DC.Source:          [If this code is adapted from another source, link it here]
DC.Language:        en-US
DC.Relation:        This module is called by main.py and its output is used as
                    input for processing.py.
DC.Coverage:        N/A for this software module.
DC.Rights:          [e.g., MIT License, Copyright 2025 Autumn Denny]
================================================================================
"""

import scispacy
import spacy

# Setting to sciBERT, we'll see how it goes and adjust as needed. Supposedly SciSpaCy has an entity linker to play with too.
languageProcessor = spacy.load("en_core_sci_scibert")


import os
for file in os.listdir('test_txts'):
    

