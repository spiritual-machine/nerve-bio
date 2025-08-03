"""
================================================================================
Dublin Core Meta
================================================================================
DC.Title:           PDF Parsing Module for NERVE
DC.Creator:         Autumn Denny
DC.Subject:         Natural Language Processing, PDF Parsing, Data Ingestion, PyMuPDF, OCR
DC.Description:     This script contains the core functions to parse text and
                    metadata from scientific PDF documents. It serves as the
                    first step in the NERVE knowledge extraction pipeline.
DC.Publisher:       spiritual-machine
DC.Date:            2025-08-02
DC.Type:            Software, Python Script
DC.Format:          text/x-python
DC.Identifier:      /nerve/parsing.py
DC.Language:        en-US
DC.Relation:        This module is called by main.py and its output is used as
                    input for classification.py
DC.Coverage:        N/A for this software module.
DC.Rights:          TBD
================================================================================
"""
# v0 is a unit test using scientific PDFs from a known author
import pymupdf
import ftfy
import pytesseract   # nts: actually implement this 
import os

# TODO: (originally, this is a "proof of concept" before proposing it)
# 1. Add docstrings and typehints.
# 2. OO-style classes + enhance modularity
# 3. clean comments to be more formal
# 4. Remove as much global stuff as possible (likely when I tie to UI) -> move to a config
# 5. Implement the pytesseract fallback -> keep scalability in mind and optimize
# 6. Test if quality score threshold is reasonable on a larger PDF set (mine maybe 100 or so PDFs to test?)
# 7. Make all unique variable names, keeping consistent.


# Global vars
testPDFDir = 'test_pdfs'
testTXTDir = 'test_txts'
qualityScoreThreshold = 0.92


# Allowed and disallowed characters.
# Used Gemini Pro to make a set of allowed characters.
allowedChars = [
    (0x0020, 0x007E),  # Basic ASCII -> For most common characters in English. 
    (0x00A0, 0x00FF),  # Latin-1 Supplement -> For Latin-based words.
    (0x2000, 0x206F),  # General Punctuation -> Punctuation
    (0x0370, 0x03FF),  # Greek and Coptic -> For scientific shorthand
    (0x2200, 0x22FF)   # Mathematical operators -> For mathematical symbols, stuff like ≥
]
whiteListedChars = {'◦','˚','°'}
# Used ChatGPT to generate blacklisted characters.
blackListedChars = {'¤','§','©','®','¶','•','†','‡','◦','˚','※','⁂','‽','⁉','‥','☺','☻','♥','♦','♣','♠','✦','✧','★','☆','✪','☀','☁','☂','☃','☄','\uFFFD','\u200B','\u200C','\u200D','\u2060','\uFEFF','\u202A','\u202B','\u202C','\u202D','\u202E','\u2066','\u2067','\u2068','\u2069','\u25AA','\u25AB','\u25B6','\u25C0'}
allowedEscapedChars = ['\n', '\r', '\t']

def getNewTXTPath(fileName):
    """
    Input: fileName (str | name of pdf file being converted to txt)
    Output: txtPath (str | path of new txt file)
    Purpose: Converts to a path of the new txt file of the converted pdf.
    """
    txtPath = os.path.join(testTXTDir, fileName[:-4] + '.txt')
    return txtPath

def textSlicer(sampleText):
    """
    Input: sampleText (str | text from transcribed .txt)
    Output: txtWords (array)
    Purpose: Slices text from the txt transcribed from the PDF into words for quality checks.
    """
    words = sampleText.split()
    return words

# This is all a heuristic ###. Sorry.
def checkInvalidChars(word):
    """
    Input: word (str | single word)
    Output: isInvalid (bool)
    Purpose: Checks for any super weird characters that came out of parsing errors. Labels word as invalid (True) or valid (False).
             Assumes validity.
    """
    isInvalid = False
    for char in word:
        if char in allowedEscapedChars:
            continue
        elif char in whiteListedChars:
            continue
        else:
            ordChar = ord(char)
            isInRange = any(start <= ordChar <= end for start, end in allowedChars)
            if not isInRange:
                isInvalid = True
            elif char in blackListedChars:
                isInvalid = True
    return isInvalid

# nto: Noticed ligatures and broken accents from test run.
def fixText(text):
    """
    Input: text (str | text that was from .txt transcribed from pdf)
    Output: text (str | text that was fixed in-place to translate ligatures)
    Purpose: Replaces ligatures and accents in text that would otherwise be flagged as invalid characters.
    """
    # Google's Gemini was used to compile a list of ligatures.
    ligatures = {'ﬀ': 'ff', 'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬃ': 'ffi','ﬄ': 'ffl', 'æ': 'ae','œ': 'oe'}
    for key in ligatures.keys():
        text = text.replace(key, ligatures[key])
    # ChatGPT for broken accents.
    brokenAccents = {'ı´':'í','I´':'Í','i´':'í','I´':'Í','a´':'á','A´':'Á','e´':'é','E´':'É','o´':'ó','O´':'Ó','u´':'ú','U´':'Ú','n~':'ñ','N~':'Ñ','c¸':'ç','C¸':'Ç','a`':'à','A`':'À','e`':'è','E`':'È','i`':'ì','I`':'Ì','o`':'ò','O`':'Ò','u`':'ù','U`':'Ù','a^':'â','A^':'Â','e^':'ê','E^':'Ê','i^':'î','I^':'Î','o^':'ô','O^':'Ô','u^':'û','U^':'Û','a¨':'ä','A¨':'Ä','e¨':'ë','E¨':'Ë','i¨':'ï','I¨':'Ï','o¨':'ö','O¨':'Ö','u¨':'ü','U¨':'Ü'}
    for key in brokenAccents.keys():
        text = text.replace(key, brokenAccents[key])
    return text

def cleanText(text):
    """
    Input: text (str | text that was from the .txt transcribed from pdf)
    Output: text (str | text that was cleaned in-place to remove wonky unicode characters)
    Purpose: Removes obviously bad unicode characters.
    """
    # I *will* just forcibly remove weird characters, man.
    for char in text:
        if char in blackListedChars:
            text = text.replace(char, '')
    text = ftfy.fix_text(text)
    return text


def checktextQuality(text):
    """
    Input: txtFile (str | Text from txt.)
    Output: gibberScore (float | percentage of words that are gibberish)
    Purpose: Combined with checkInvalidChars, compared against a threshold for whether OCR should be used as a fallback for parsing
             difficult PDFs.
    """
    textWords = textSlicer(text)
    # Initializing these variables to make the quality score for the text transcription.
    invalidWords = 0
    validWords = 0
    for word in textWords:
        if checkInvalidChars(word) == True:
            print(word)
            invalidWords += 1
        else:
            validWords += 1
    qualityScore = 1 - (invalidWords / (invalidWords + validWords))
    print('[NERVE-bio] First-pass PDF quality score (using PyMuPDF): ' + str(qualityScore))
    return qualityScore


def transcribePDF(pdfFile):
    """
    Input: pdfFile (str | name of PDF)
    Output: None.
    Purpose: Uses PyMuPDF as first attempt to parse PDFs. Stores parsed files as internal TXTs. 
             Initiates pipeline for checking transcription quality.
    """
    pdfPath = os.path.join(testPDFDir, pdfFile)
    pmPDF = pymupdf.open(pdfPath)
    txtPath = os.path.join(testTXTDir, pdfFile[:-4] + '.txt')
    textOutput = open(txtPath, 'wb')
    for page in pmPDF:
        pageText = page.get_text()
        textOutput.write(pageText.encode('utf-8'))
    textOutput.close()
    with open(txtPath, 'r', encoding = 'utf-8') as file:
        text = file.read()
        fixedText = fixText(text)
    if checktextQuality(fixedText) > qualityScoreThreshold:
        cleanedText = cleanText(fixedText)
        with open(txtPath, 'w', encoding='utf-8') as file:
            file.write(cleanedText)
        print('[NERVE-bio] Extracted PDF: ' + pdfFile)
        #print('[NERVE-bio] Failed to Extract PDF: ' + pdfFile)
    # Log to console that PDF text was extracted.
    


# nts: remove stuff here that hard codes directory for PDFs; users will input using UI

for file in os.listdir(testPDFDir):
    transcribePDF(file)





