#!/usr/local/bin/python
#
#  littriageload.py
###########################################################################
#
#  Purpose:
#
#      This script will 
#
#  Usage:
#
#      littriageload.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#	MASTERTRIAGEDIR
#	FAILEDTRIAGEDIR
#
#  Inputs:
#
#	INPUTDIR=${FILEDIR}/input
#	there are subdirectories for each curator.
#	for example:
#		input/cms
#		input/csmith
#		input/terryh
#
#  Outputs:
#
#	OUTPUTDIR=${FILEDIR}/output
#	FAILEDTRIAGEDIR=/data/littriagefailed/byCurator
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Initialize variables.
#      2) Open files.
#      3) Read each PDF (input file)/sanity checks
#      4) If sanity check fails, send PDF to FAILEDTRIAGEDIR
#      5) If sanity check successful, create BCP files
#      6) Close files.
#
#  Notes:  None
#
# lec	06/20/2017
#       - TR12250/Lit Triage
#
###########################################################################

import sys 
import os
import db
import PdfParser

litparser = ''

errorLog = ''
errorLogFile = ''

inputDir = ''

failDir = ''

#
# userDict = {'user' : [pdf1, pdf2]}
# {'cms': ['28069793_ag.pdf', '28069794_ag.pdf', '28069795_ag.pdf']}
userDict = {}

#
# doiidDict = {'pdf file' : doiid}
# {'28069793_ag.pdf': ['xxxxx']}
doiidDict = {}

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global litparser
    global errorLog
    global inputDir
    global failDir

    litparser = os.getenv('LITPARSER')
    errorLog = os.getenv('LOG_ERROR')
    inputDir = os.getenv('INPUTDIR')
    failDir = os.getenv('FAILEDTRIAGEDIR')

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not litparser:
        print 'Environment variable not set: LITPARSER'
        rc = 1

    #
    # Make sure the required environment variables are set.
    #
    if not errorLog:
        print 'Environment variable not set: LOG_ERROR'
        rc = 1

    #
    # Make sure the required environment variables are set.
    #
    if not inputDir:
        print 'Environment variable not set: INPUTDIR'
        rc = 1

    #
    # Make sure the required environment variables are set.
    #
    if not failDir:
        print 'Environment variable not set: FAILEDTRIAGEDIR'
        rc = 1

    # must be initialized PdfParser.py
    print litparser
    PdfParser.setLitParserDir(litparser)

    return rc


#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global errorLogFile

    #
    # Open the error log file.
    #
    try:
        errorLogFile = open(errorLog, 'w')
    except:
        print 'Cannot open error log file: ' + errorLogFile
        return 1

    return 0


#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():

    if errorLogFile:
        errorLogFile.close()

    return 0


#
# Purpose: Bucketize the MGI/UniProt IDs from the association files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def processPDFs():
    global userDict
    global doiidDict

    #
    # iterate thru PDFs
    #

    #
    # level 1 sanity check
    #
    # file not in PDF format
    # cannot extract/find DOI ID
    # PDF is duplicated in published directory (same DOI id)
    #

    for userPath in os.listdir(inputDir):

	#if userPath != 'cms':
	#	break

	for pdfFile in os.listdir(inputDir + '/' + userPath):

		if not pdfFile.lower().endswith('.pdf'):
			errorLogFile.write('file does not end with pdf : %s/%s\n' % (userPath, pdfFile))
			continue

		if userPath not in userDict:
			userDict[userPath] = []
		userDict[userPath].append(pdfFile)

    for userPath in userDict:

	#if userPath != 'cms':
		#break

	pdfPath = inputDir + '/' + userPath + '/'

	for pdfFile in userDict[userPath]:

		print 'PdfParser.PdfParser: %s%s' % (pdfPath, pdfFile)

		pdf = PdfParser.PdfParser(pdfPath + pdfFile)
		doiid = ''

		try:
			doiid = pdf.getFirstDoiID()
		        if doiid not in doiidDict:
			        doiidDict[doiid] = []
		        doiidDict[doiid].append(pdfFile)
			print 'pdf.getFirstDoiID() : successful : %s%s\n' % (pdfPath, pdfFile)
		except:
			print 'pdf.getFirstDoiID() : error reported : %s%s\n' % (pdfPath, pdfFile)
			errorLogFile.write('cannot extract/find DOI ID (litparser): %s%s\n' % (pdfPath, pdfFile))
			print 'moving %s%s to %s/%s/%s\n' % (pdfPath, pdfFile, failDir, pdfPath, pdfFile)
			#os.rename(pdfPath + pdfFile, failDir + '/' + userPath + '/' + pdfFile)
			continue
	
    #print userDict
    #print doiidDict

    return 0

#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if processPDFs() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
