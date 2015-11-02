#!/usr/bin/env python
"""resume-randomizer.py: This program generates random text, based off of .rtf files (called resume template files).  This file should not need to be modified by end users; by changing the template files the text results will be changed."""

# Copyright 2015 Ryan Beasley and Joanna Lahey
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Version 23 11/1/2015: When outputting the csv, the column headers for the points have their values prepended by "v", e.g., "v1-3". This change is to help with importing the data into Stata, which cannot have variable names that start with numbers.  Ditto for the parents in the codebook, so that Excel formats that column as string.  Also, the csv files no longer have spaces after each comma.  Licensed under Apache License 2.0.
# Version 22 6/20/2015: If attempting to print out the codebook fails because the program does not find an expected start tag, it prints a section of the template (including fragments) with line numbers, to aid in debugging. Refactored the generation of the codebook into a function.  Can now specify the percentage chance for the first sub-point in a random section...the remaining sub-points are uniform probability.
# Version 21 4/21/2014: Checks for malformed start tags (e.g., empty lines) while creating codebook.  Bugfix, correctly creates new codebook when the new codebook is the same except missing one or more leafs at the end. Bugfix, malformed templates correctly abort codebook creation.  Better error messages and error handling.
# Version 20 2/7/2014: Prints the executable's version number.
# Version 19 9/6/2013: Prevents overwriting the codebook by using an unused filename.  When exiting with error, requests keypress because otherwise the window might close before user sees the error.
# Version 18 3/12/2013: Creates a codebook from the template, each time the program runs.  The codebook is an xls file containing one line per Leaf, with the parent section, the leaf's number in the parent, and the Leaf's text.
# Version 17 11/21/2012: Removes two debugging messages about minimum/maximum number of entries.
# Version 16 7/28/2012: Adds minimum/maximum number of entries for repeating sections with repeatNoDoubles.
# Version 15 7/12/2012: Adds output of csv file with variable names.  Clarifies the user input questions regarding number of matched resumes and number of batches. Renames the variable names for the filenames so they match the filename extensions.
# Version 14 7/10/2012: Adds MatchOnlyOneEver.
# Version 13 7/10/2012: The *end_leaf* special text in file fragments do not have to be directly followed by a CRLF.  Can now specify whether or not to include the date & time on filenames.
# Version 12 7/8/2012: Bugfix: Now correctly handles unexpected end-of-file while reading templates.
# Version 11 7/4/2012: Adds global memory for store and recall of template-defined variables.
# Version 10 6/27/2012: Adds file fragments.
# Version 9 6/20/2012: Throws an error if a special text references a section other than Random, or if special text is used outside of a repeating section, or if the start/end/interval inputs are neither integers nor floats.
# Version 8 5/25/2012: Adds Dependent sections.
# Version 7 6/22/2007: The template files now end in ".rtf" because FileGether.exe created files ending in ".dat".
# Version 6 6/22/2007: The ".txt" files are now ".doc" files.  The ".raw" files are now ".txt" files.  This change is being done so that we can continue to use the FileGather.exe program to combine the records for many resumes into a single file.  As a side benefit, the resume files will now open in Word.
# Version 5 6/22/2007: The program now creates ".raw" files also, containing just the filename for the text file and the choices made when creating the file.
# Version 4 6/22/2007: No changes except for the version number (to keep the same as the version of the web-based template generator).
# Version 3 6/22/2007: No changes except for the version number (to keep the same as the version of the web-based template generator).
# Version 2 6/22/2007: Replaced all instances of the text "style" with "template".
# Version 1 6/20/2007


# TODO:
#Putting a space before the *leaf* special text in a fragment should not cause the program to fail.
#I should just put repeatNever here like matchDifferent...simplify the below if-elif block of getChoiceFor...

Version = 23
Date = "November 1, 2015"

import os
import glob
import re
import tempfile
import shutil
import sys
from random import randrange
from random import random
from random import shuffle
from time import strftime

globalDelayedWrite = []
globalMemory = {}
globalThisResumeNumber = 0
globalCsvNames = ''
globalCsvData = ''
globalDictRangeChoices = {}
logging = False

import math
def frange(limit1, limit2 = None, increment = 1.):
  """
  Range function that accepts floats (and integers).

  Usage:
  frange(-2, 2, 0.1)
  frange(10)
  frange(10, increment = 0.5)

  The returned value is an iterator.  Use list(frange(start,...)) for a list.
  """

  if limit2 is None:    limit2, limit1 = limit1, 0.
  else:    limit1 = float(limit1)
  count = int(math.ceil(limit2 - limit1)/increment)
  return (limit1 + n*increment for n in xrange(0,count))

def makeNameArrays(numDifferent, initName, iString, matchedPair):
  nameArray = []
  numDifferentString = str(numDifferent)
  for j in range(numDifferent):
    jString = str(j+1)
    while len(jString)<len(numDifferentString): jString="0"+jString
    if matchedPair:
      nameArray += [initName+"_"+iString+"_"+jString+"of"+numDifferentString]
    else:
      nameArray += [initName+"_"+iString]
  docArray = map(lambda x: x+'.doc', nameArray)
  savArray = map(lambda x: x+'.sav', nameArray)
  txtArray = map(lambda x: x+'.txt', nameArray)
  csvArray = map(lambda x: x+'.csv', nameArray)
  return [docArray, savArray, txtArray, csvArray]

def createFileNames(name, myTime, numberLength, numDifferent, matchedPair, i=1):
  tempName = name[:-4]+myTime
  iString = str(i)
  while len(iString)<numberLength: iString="0"+iString
  [docArray, savArray, txtArray, csvArray] = makeNameArrays(numDifferent, tempName, iString, matchedPair)
  while reduce(lambda x,y: x or os.path.exists(y), [False]+docArray+savArray+txtArray):
    i+=1
    iString = str(i)
    while len(iString)<numberLength: iString="0"+iString
    [docArray, savArray, txtArray, csvArray] = makeNameArrays(numDifferent, tempName, iString, matchedPair)
  return [docArray, savArray, txtArray, csvArray]

def replaceFragments(inFile_strings):
  fragment_regex = r'''%file%(.*)%'''
  num_fragments_replaced = 0
  for line_number in xrange(len(inFile_strings)-1, -1, -1):
    match_object = re.match(fragment_regex, inFile_strings[line_number])
    if match_object is not None:
      num_fragments_replaced += 1
      print "Inserting file fragment, line #" + str(line_number) + ": " + inFile_strings[line_number].rstrip('\n')
      try:
        fragmentFile = open(match_object.group(1), 'r')
      except:
        print "Error! Found the tag for a file fragment, but was unable to open the file it names."
        print "The tag is in line #" + str(line_number) + ": " + inFile_strings[line_number]
        print "The tag names the file '" + match_object.group(1) + "', but this program was unable to open that file...is it in the same directory as this program?  Is the filename spelled correctly?"
        return -41, '', ''
      with fragmentFile: # the file will be closed by the compound "with" statement
        fragment_strings = fragmentFile.readlines()

      if (fragment_strings[0].find("*fragment*") != 0):
        print "\nWarning! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  The file is supposed to start with '*fragment*' on the first line...are you sure this is a fragment?\n"
      #remove lines between leaves
      outside_leaf = True
      for line_number_fragment in xrange(len(fragment_strings)-1, -1, -1):
        currentLine = fragment_strings[line_number_fragment]
        temp = currentLine.rstrip('\n').split(" ")
        myText = temp[0]
        if outside_leaf:
          if ("*end_leaf*" in myText):
            outside_leaf = False
            continue
          fragment_strings = fragment_strings[0:line_number_fragment] + fragment_strings[(line_number_fragment+1):]
        if not outside_leaf:
          if ("*leaf*" in myText):
            outside_leaf = True

      #march up to find the leaf to get the section ID, and determine how far up to remove
      found_leaf = False
      for i in xrange(line_number-1, -1, -1):
        currentLine = inFile_strings[i]
        temp = currentLine.rstrip('\n').split(" ")
        myText = temp[0]
        if ("*leaf*" in myText):
          found_leaf = True
          first_added_label = temp[1]
          leaf_line_number = i
          break
      if not found_leaf:
        print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program tried to find the enclosing *leaf* tag, but failed."
        return -42, '', ''
        
      #march down to find the end_leaf, and determine how far down to remove
      found_end_leaf = False
      for i in xrange(line_number+1, len(inFile_strings)):
        currentLine = inFile_strings[i]
        temp = currentLine.rstrip('\n').split(" ")
        myText = temp[0]
        if ("*end_leaf*" in myText):
          found_end_leaf = True
          if (first_added_label != temp[1]):
            print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program tried to find the enclosing *leaf* and *end_leaf* tags, but they had different labels: " + first_added_label + " vs " + temp[1] + ".  Is the template correct above and below the special text that inserts the file fragment?"
            return -43, '', ''
          end_leaf_line_number = i
          break
      if not found_leaf:
        print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program tried to find the enclosing *end_leaf* tag, but failed."
        return -44, '', ''

      #now fix all the section IDs in the fragment_strings...and the %next% special text
      #first, what is the nearest parent repeating section, if any?
      found_parent_repeating = False
      for i in xrange(line_number-1, -1, -1):
        currentLine = inFile_strings[i]
        temp = currentLine.rstrip('\n').split(" ")
        myText = temp[0]
        if (("*random*" in myText) and ("*repeat*" in currentLine)):
          found_parent_repeating = True
          nextLabel = temp[1]
          break
      num_added_sections = -1
      myLabel = first_added_label
      for i in xrange(len(fragment_strings)):
        currentLine = fragment_strings[i]
        temp = currentLine.rstrip('\n').split(" ")
        myText = temp[0]
        if ("*leaf*" in myText):
          fragment_strings[i] = "*leaf* " + myLabel + "\n"
          continue
        if ("*end_leaf*" in myText):
          fragment_strings[i] = "*end_leaf* " + myLabel + "\n"
          myLabel_split = myLabel.split('-')
          myLabel_split[-1] = str(int(myLabel_split[-1])+1)
          myLabel = '-'.join(myLabel_split)
          num_added_sections += 1
          continue
        if ("%next%" in currentLine):
          if not found_parent_repeating:
            print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program tried to replace the %next% special text, but the fragment does not appear after a repeating random section.  Inside a file fragment, the special text %next% will reference the most recent section that is both random and repeating."
            return -45, '', ''
          fragment_strings[i] = fragment_strings[i].replace("%next%", "%next%"+nextLabel+"%")
          continue

      #now find the enclosing constant or random section and fix its number of subsections
      parentLabel_strings = myLabel.split('-')[0:-1]
      parentLabel = '-'.join(parentLabel_strings)
      found_parent = False
      for i in xrange(line_number):
        currentLine = inFile_strings[i]
        temp = currentLine.rstrip('\n').split(" ")
        if ((len(temp) > 1) and (temp[1] == parentLabel)):
          found_parent = True
          temp[2] = str(int(temp[2]) + num_added_sections)
          inFile_strings[i] = ' '.join(temp) + "\n"
          break
      if not found_parent:
        print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program tried to correct the parent's number of subsections (top, opening tag) but did not find the parent's ID " + parentLabel
        return -46, '', ''

      found_parent = False
      for i in xrange(line_number,len(inFile_strings)):
        currentLine = inFile_strings[i]
        temp = currentLine.rstrip('\n').split(" ")
        if ((len(temp) > 1) and (temp[1] == parentLabel)):
          found_parent = True
          temp[2] = str(int(temp[2]) + num_added_sections)
          inFile_strings[i] = ' '.join(temp) + "\n"
          break
      if not found_parent:
        print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program tried to correct the parent's number of subsections (bottom, closing tag) but did not find the parent's ID " + parentLabel
        return -47, '', ''

      #work down through the inFile_strings and fix any sibling subsections
      first_added_label_strings = first_added_label.split('-')
      tags = ["leaf", "random", "constant", "dependent"]
      tags.extend(["end_"+tag for tag in tags])
      tags = ["*"+tag+"*" for tag in tags]
      for i in xrange(end_leaf_line_number+1, len(inFile_strings)):
        currentLine = inFile_strings[i]
        temp = currentLine.rstrip('\n').split(" ")
        myText = temp[0]
        if (myText in tags):
          if (len(temp) < 2):
            print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program is scanning through each line in the template, and expects to find an ID as the second token on this line #" + i + ": " + currentLine
            print "but there are only " + len(temp) + " tokens on the line."
            return -48, '', ''
          myLabel = temp[1]
          myLabel_strings = myLabel.split('-')
          if (len(myLabel_strings) > len(parentLabel_strings) and 
              (all([myLabel_strings[j] == parentLabel_strings[j] for j in xrange(len(parentLabel_strings))])) and 
              (myLabel_strings[len(parentLabel_strings)] > first_added_label_strings[len(parentLabel_strings)])):
            myLabel_strings[len(parentLabel_strings)] = str(int(myLabel_strings[len(parentLabel_strings)]) + num_added_sections)
            temp[1] = '-'.join(myLabel_strings)
            inFile_strings[i] = ' '.join(temp) + "\n"
          if (myText == "*dependent*"):
            if (len(temp) < 5):
              print "Error! While updating the file fragment '" + match_object.group(1) + "' for line #" + str(line_number) + ": " + inFile_strings[line_number] + "  This program is scanning through each line in the template, and expects to find the ID of the master section as the fifth token on this line #" + i + ": " + currentLine
              print "but there are only " + len(temp) + " tokens on the line."
              return -49, '', ''
            master = temp[4]
            master_strings = master.split('-')
            if (len(master_strings) > len(parentLabel_strings) and 
                (all([master_strings[j] == parentLabel_strings[j] for j in xrange(len(parentLabel_strings))])) and 
                (master_strings[len(parentLabel_strings)] > first_added_label_strings[len(parentLabel_strings)])):
              master_strings[len(parentLabel_strings)] = str(int(master_strings[len(parentLabel_strings)]) + num_added_sections)
              temp[4] = '-'.join(master_strings)
              inFile_strings[i] = ' '.join(temp) + "\n"
        else:
          if ("%next%" in currentLine):
            next_strings = currentLine.split('%')
            for next_index in xrange(len(next_strings) - 1):
              if (next_strings[next_index] == "next"):
                myLabel = next_strings[next_index+1]
                myLabel_strings = myLabel.split('-')
                if (len(myLabel_strings) > len(parentLabel_strings) and 
                    (all([myLabel_strings[j] == parentLabel_strings[j] for j in xrange(len(parentLabel_strings))])) and 
                    (myLabel_strings[len(parentLabel_strings)] > first_added_label_strings[len(parentLabel_strings)])):
                  myLabel_strings[len(parentLabel_strings)] = str(int(myLabel_strings[len(parentLabel_strings)]) + num_added_sections)
                  next_strings[next_index+1] = '-'.join(myLabel_strings)
            inFile_strings[i] = '%'.join(next_strings)
            
      inFile_strings = inFile_strings[0:leaf_line_number] + fragment_strings + inFile_strings[(end_leaf_line_number+1):]
  return 1, inFile_strings, num_fragments_replaced


def printCodebook(inFile, fileName):
  #instead of always printing the codebook, find the last codebook, check to see if this one will be the same, and if not, don't save it.
  print
  print "Checking whether codebook already exists."
  try:
    tempFile = tempfile.TemporaryFile()
  except:
    print
    print "Error creating a temporary file to hold the codebook!"
    return -51
  outFile = tempFile
  inFile.seek(0)
  theLine = inFile.readline() #skip gui version
  theLine = inFile.readline()
  makeCodeBook = True
  startString = "%start%"
  endString = "%end%"
  currentString = "%current%"
  currentPlusIntervalString = "%currentPlusInterval%"
  outFile.write("Parent Section\tLeaf\tText\n")
  lineNumber = 2
  while theLine: #readline returns an empty string when it reaches EOF
    currentLine = theLine
    if logging: print currentLine
    temp = currentLine.rstrip('\n').split(" ")
    if logging: print temp
    if (len(temp)<2):
      print "\nPortion of template (after inserting fragments), with line numbers:"
      inFile.seek(0)
      theLine = inFile.readline()
      outputLineNumber = 1
      while theLine:
        if (outputLineNumber + 7 > lineNumber) and (lineNumber + 7 > outputLineNumber):
          sys.stdout.write(str(outputLineNumber) + ":" + theLine)
        theLine = inFile.readline()
        outputLineNumber += 1
      print "\nError!  While reading through the template to print the codebook, the software expected a start tag (e.g., *random* 3-2 4) on line number " + str(lineNumber) + " (see print out with line numbers above) but got: "+currentLine
      print "Make sure the lines (in the template file) that contain start tags for Random and Constant and Dependent sections specify the correct number of subsections listed after the label (following the second space in the line), that each end tag is directly followed by either a start tag or an end tag, that there are no blank lines in the template file outside of Leaf sections, and that all fragments use the start/end tag texts '*leaf*' and '*end_leaf*' exactly and with no spaces on the same lines. Also look at the surrounding lines to see if a fragment does not have the correct text for a start/end tag."
      return -38
      
    myText = temp[0]
    myLabel = temp[1]
    if "*leaf*" in myText:
      splitLabel = myLabel.split("-")
      myParent = '-'.join(splitLabel[:-1])
      outFile.write("v" + myParent + "\t" + splitLabel[-1] + "\t")
      retval = writeLeaf(inFile, outFile, currentLine, myLabel, startString, endString, currentString, currentPlusIntervalString, makeCodeBook)
      if (retval < 1):
        return retval
      lineNumber += retval
      outFile.write("\n")
    if "*end_constant*" in myText and myLabel is '1': # We've come to the end of the template
      break
    theLine = inFile.readline()
    lineNumber += 1

  #is this codebook the same as the latest one?
  codebookPrefix = fileName + "_codebook-"
  prevCodebookNames = glob.glob(codebookPrefix + "*.xls")
  saveCodebook = True
  if (len(prevCodebookNames) == 0):
    print "No previous codebook was found in the folder."
  else:
    latestCodebookName = max(prevCodebookNames, key=os.path.getmtime)
    try:
      latestCodebook = open(latestCodebookName, 'r')
    except IOError as e:
      print
      print "Warning, failed to compare previous codebook with new codebook!  Saving new codebook even though it might have the same content."
      print e
    else:
      saveCodebook = False
      tempFile.flush()
      tempFile.seek(0)
      aLine = tempFile.readline()
      while aLine:
        if (aLine != latestCodebook.readline()):
          saveCodebook = True
          break
        aLine = tempFile.readline()
      if not saveCodebook:
        #If the new set of leaf texts is exactly the same as before except missing lines at the end, the previous check won't find the difference.  We must compare the other way so a shortened codebook is noticed.
        tempFile.seek(0)
        latestCodebook.seek(0)
        aLine = latestCodebook.readline()
        while aLine:
          otherLine = tempFile.readline()
          if (aLine != otherLine):
            saveCodebook = True
            break
          aLine = latestCodebook.readline()
      latestCodebook.close()
      if saveCodebook:
        print
        print "Warning! The template does not match the latest codebook file: " + latestCodebookName
        print "One (or both) of the template or the codebook have been modified."
        print "A new codebook file will be created for the files being generated now."
        raw_input('Press return to continue')

  if saveCodebook:
    codebookNumber = 1
    while True:
      codebookFilename = codebookPrefix + str(codebookNumber) + ".xls"
      if not os.path.isfile(codebookFilename):
        break
      codebookNumber += 1
    print "Saving new codebook in a file named " + codebookFilename
    try:
      codebookFile = open(codebookFilename, 'w')
    except IOError as e:
      print
      print "Error creating codebook file named " + codebookFilename
      print e
      return -52
    tempFile.seek(0)
    shutil.copyfileobj(tempFile, codebookFile)
    tempFile.close()
    codebookFile.close()
    print "Done saving the codebook."
    print
  else:
    print "The codebook for this template already exists in " + latestCodebookName

  return 1


def createResumes(fileName):
  inFile = open(fileName, 'r')
  matchedPair = False
  guiVersion = inFile.readline()
  guiVersion_text = " ".join(guiVersion.split(" ")[1:4])
  if (guiVersion_text.rstrip("\n") != "gui version number"):
    print "Error! The file selected as a template " + fileName + " does not have the correct text starting its first line: '" + str(Version) + " gui version number'"
    print "Instead, the first line is '" + guiVersion + "'"
    return -53

  for line in inFile:
    if ('*matchDifferent*' in line) or ('*matchSame*' in line) or ('*matchOnlyOneEver*' in line):
      matchedPair = True
      break
  numDifferent = 1
  if matchedPair:
    while True:
      try: numDifferent = int(raw_input('This template file contains random sections for Matched "pairs".  How many files should be matched in each batch? (0 to cancel) '))
      except ValueError:
        print "Please enter a positive integer."
        continue
      if numDifferent < 1:
        print "Canceled"
        return -1
      break

  while True:
    try:
      if matchedPair:
        numToMake = int(raw_input('How many batches of matched resumes should be generated? (0 to cancel) '))
      else:
        numToMake = int(raw_input('How many resumes should be generated? (0 to cancel) '))
      break
    except ValueError:
      print "Please enter an integer."
      continue
  if (numToMake < 1):
    print "Canceled"
    return -1

  print
  myTime = ""
  withTime = raw_input('Would you like the date & time in each resume filename? (Y/n, anything else to cancel) ')
  if (not withTime) or (withTime.lower() == 'y') or (withTime.lower() == 'yes'):
    myTime = strftime("_%Y-%m-%d-%H-%M-%S")
  elif (withTime.lower() != 'n') and (withTime.lower() != 'no'):
    print "Canceled"
    return -1
  print

  inFile.seek(0)
  inFile_strings = inFile.readlines()
  replaced_fragments = 1
  num_fragments = -1
  have_printed_warning = False
  while replaced_fragments > 0:
    num_fragments += replaced_fragments
    if ((num_fragments > 1000) and not have_printed_warning):
      have_printed_warning = True
      print "Warning! This program has so far replaced " + str(num_fragments) + " file fragments. Verify that the file fragments do not contain %file% special texts that reference each other, causing an infinite loop."
      raw_input("Press return to continue")
    retval, inFile_strings, replaced_fragments = replaceFragments(inFile_strings)
    if (retval < 0):
      return retval

  if (num_fragments > 0):
    inFile.close()
    try:
      inFile = tempfile.TemporaryFile()
    except:
      print "Error! After inserting file fragments into the template, this program failed to create a temporary file to store the new template."
      return -50
    inFile.writelines(inFile_strings)
    inFile.seek(0)
    inFile_strings = inFile.readlines()
    
  returnVal = printCodebook(inFile, fileName)
  if returnVal < 0:
    return returnVal

  inFile.seek(0)
  global globalThisResumeNumber;
  for batchOfResumes in range(numToMake):
    [outputFiles, saveChoicesFiles, txtChoicesFiles, csvChoicesFiles] = createFileNames(fileName, myTime, len(str(numToMake)), numDifferent, matchedPair, batchOfResumes+1)
    dictionaryMatchSame = {}
    dictionaryMatchDifferent = {}
    dictionaryMatchOnlyOneEver = {}
    globalThisResumeNumber = 0;
    for [outputFilename, saveChoicesFilename, txtChoicesFilename, csvChoicesFilename] in map(lambda x,y: [x, y[0], y[1], y[2]], outputFiles, map(None, saveChoicesFiles, txtChoicesFiles, csvChoicesFiles)):
      globalThisResumeNumber += 1;
      saveChoicesFile = open(saveChoicesFilename, 'w')
      print >>saveChoicesFile, outputFilename +" is the text file that these choices created"
      print >>saveChoicesFile, fileName+" is the template file being used"
      print >>saveChoicesFile, str(i+1)+" is the index of this text file within a matched set"
      tempTime = myTime
      if not tempTime:
        tempTime = strftime("_%Y-%m-%d-%H-%M-%S")
      print >>saveChoicesFile, tempTime+" is the current time as year, month, day, hour (out of 24), minute, second"
      print >>saveChoicesFile, str(Version)+" is the version of the Python program"
      print >>saveChoicesFile, guiVersion.rstrip('\n')
      print >>saveChoicesFile, str(numDifferent) + " is the number of text files being Matched."
      print >>saveChoicesFile, "Read the following lines in pairs.  The first line is the start tag (from the template file) that required a choice.  The start tag line contains the type of section that required a decision (currently only 'Random' sections require decisions), then the label of this section as shown in the outline in the web-based meta-program, then the number of subsections to choose from, and then any settings for this section (e.g., repeating or matched files).  The second line is the index of the subsection that was randomly chosen.  The indices run from 0 through n-1, inclusive, where n is the number of choices listed in the start tag line.  All of the choices are also stored in the .txt file, and in the .csv file with variable names based on the section IDs."
      txtChoicesFile = open(txtChoicesFilename, 'w')
      txtChoicesFile.write(outputFilename)
      csvChoicesFile = open(csvChoicesFilename, 'w')
      global globalCsvNames, globalCsvData
      globalCsvNames = "filename,batch,numberOfBatches,resume,numberOfResumesPerBatch"
      globalCsvData = outputFilename
      if "," in globalCsvData:
        globalCsvData.replace(",", "")
        print "\nWarning! the filename contained a comma, which is a delimiter in csv (comma-separated-variables) files.  So in the csv file (and only inside the csv file), the comma has been removed from the filename.\n\n"
      globalCsvData += "," + str(batchOfResumes+1) + "," + str(numToMake) + "," + str(globalThisResumeNumber) + "," + str(numDifferent)
      outputFile = open(outputFilename, 'w')
      #reset the store/recall variables for each file
      global globalMemory
      globalMemory = {}
      global globalDictRangeChoices
      globalDictRangeChoices = {}
      inFile.seek(0)
      inFile.readline() #skip gui version
      retval = recursiveGenerate(inFile, outputFile, saveChoicesFile, txtChoicesFile, '', {}, {}, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, '', '', '', '', {})
      if (retval >= 0) and (len(globalDelayedWrite) > 0):
        print "Error! A Leaf contains special text that refers to the 'next' value of a repeating section, but the section to which it refers is not repeating:\n" + globalDelayedWrite[0];
        retval = -40
      outputFile.close()
      if (retval<0):
        print >>saveChoicesFile, str(retval)+" is the error code...this template file had a problem"
        txtChoicesFile.write('\t-1')
        print '\nError! Problem with the template file.  Error code '+str(retval)
        saveChoicesFile.close()
        txtChoicesFile.close()
        csvChoicesFile.close()
        return retval
      saveChoicesFile.close()
      txtChoicesFile.close()
      csvChoicesFile.writelines([globalCsvNames, "\n", globalCsvData])
      csvChoicesFile.close()
      print "Done with resume "+outputFilename
  inFile.close()
  return 1

def skipElement(inFile, currentLine):
  theLine = inFile.readline()
  if (theLine == ''):
    print "\nError!  The skipElement function reached the end of the file unexpectedly."
    print "The program chose which subsection to follow for the Random or Dependent section on this line: "+currentLine
    print "The program was trying to move down in the template file to that subsection, but did not find it before reaching the end of the file.  Make sure the line above has the correct number of subsections listed after the label (following the second space in the line).  Make sure each subsection has a correct start tag (e.g., *leaf* 1-3-2) and end tag (e.g., *end_leaf* 1-3-2) in the template file."
    return -2
  currentLine = theLine
  splitLine = currentLine.split(" ")
  if (len(splitLine)<2):
    print "\nError!  The skipElement function expected a start tag (e.g., *random* 1-3-2 4) but got: "+currentLine
    print "The program chose which subsection to follow for a Random or Dependent section, and was trying to move down in the template file to that subsection, but the template was not correctly formed."
    print "Make sure each start tag is followed by the correct end tag, that each end tag is directly followed by either a start tag or an end tag, and that there are no blank lines in the template file outside of Leaf sections."
    return -3
  endTag = "*end_"+splitLine[0][1:]+" "+splitLine[1].rstrip('\n')+" "
  next_line = ''
  while (not endTag in next_line):
    next_line = inFile.readline()
    if not next_line: #readline returns an empty string when it reaches EOF
      print "\nError!  The skipElement function reached the end of the file unexpectedly while looking for the stop tag for: "+currentLine
      print "The program chose which subsection to follow for a Random or Dependent section, and was trying to move down in the template file to that subsection, but the template was not correctly formed."
      print "Make sure that the stop tag exists in the template file (e.g., *end_random* 1-3-2)"
      return -4
    next_line = next_line.rstrip('\n')+' '
  return 1

def recursiveGenerate(inFile, outFile, saveChoicesFile, txtChoicesFile, myVariableName, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice):
  theLine = inFile.readline()
  if not theLine: #readline returns an empty string when it reaches EOF
    print "\nError!  The recursiveGenerate function was looking for a new section when it reached the end of the file unexpectedly.  It expected to find a start tag (e.g., *random* 1-3-1 7).  Make sure the lines (in the template file) that contain start tags for Random and Constant and Dependent sections specify the correct number of subsections listed after the label (following the second space in the line).  Why did the function not find an end tag as the last line in the file?"
    return -5
  currentLine = theLine
  if logging: print currentLine
  temp = currentLine.rstrip('\n').split(" ")
  if (len(temp)<2):
    print "\nError!  The recursiveGenerate function was looking for a new section and expected a start tag (e.g., *random* 3-2 4) but got: "+currentLine
    print "Make sure the lines (in the template file) that contain start tags for Random and Constant and Dependent sections specify the correct number of subsections listed after the label (following the second space in the line), that each end tag is directly followed by either a start tag or an end tag, and that there are no blank lines in the template file outside of Leaf sections."
    return -6
  myText = temp[0]
  myLabel = temp[1]
  if not myVariableName:
    myVariableName = myLabel
  myNumChoices = ""
  if (("*random*" in myText) or ("*constant*" in myText) or ("*dependent*" in myText)):
    if (len(temp) < 3):
      print "\nError!  The recursiveGenerate function found a non-Leaf start tag, but the start tag did not contain the number of subsections: "+currentLine
      print "The start tags for Random and Constant and Dependent sections should list the type of the section, then a space, then the label for the section, then a space, then the number of the subsections.  (e.g., *random* 1-1-5-6 8)"
      return -7
    temp[2] = temp[2].rstrip("\n")
    if temp[2].isdigit() == False:
      print "\nError!  The recursiveGenerate function found a non-Leaf start tag, for which the number of subsections should be the second item, but on this line that is not a number: "+currentLine
      print "The start tags for Random and Constant and Dependent sections should list the type of the section, then a space, then the label for the section, then a space, then the number of the subsections.  (e.g., *random* 1-1-5-6 8)"
      return -8
    myNumChoices = int(temp[2])

  makeCodeBook = False
  if "*leaf*" in myText:
    return writeLeaf(inFile, outFile, currentLine, myLabel, startString, endString, currentString, currentPlusIntervalString, makeCodeBook)

  if "*random*" in myText:
    return writeRandom(temp, inFile, myVariableName, myNumChoices, currentLine, saveChoicesFile, txtChoicesFile, outFile, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice)

  if "*dependent*" in myText:
    return writeDependent(temp, inFile, myVariableName, myNumChoices, currentLine, saveChoicesFile, txtChoicesFile, outFile, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice)

  if "*constant*" in myText:
    return writeConstant(myNumChoices, myLabel, currentLine, inFile, outFile, saveChoicesFile, txtChoicesFile, myVariableName, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice)

  print "\nError!  The recursiveGenerate function found a start tag that it does not recognize: "+currentLine
  print "The recognizable start tags are *leaf*, *random*, *dependent*, and *constant*.  If the line above is not supposed to be a start tag, make sure in the template file it is not directly after a start tag for a Random or Constant or Dependent section, and that it does not directly follow an end tag."
  return -9


def writeLeaf(inFile, outFile, currentLine, myLabel, startString, endString, currentString, currentPlusIntervalString, makeCodeBook):
  theLine = inFile.readline()
  lineNumber = 1
  if not theLine: #readline returns an empty string when it reaches EOF
    print "\nError!  The last line in the file is " + currentLine
    print "So there is no *end_leaf* for that tag."
    return -10
  firstRun = True
  while not "*end_leaf* " + myLabel in theLine+' ':
    if firstRun:
      firstRun = False
      myLineBreak = ''
    else: myLineBreak = '\n'
    if ((('%start%' in theLine) and (startString == '')) or
        (('%end%' in theLine) and (endString == '')) or
        (('%current%' in theLine) and (currentString == '')) or
        (('%currentPlusInterval%' in theLine) and (currentPlusIntervalString == '')) or
        (('%next%' in theLine) and (startString == ''))):
      print "\nError!  In section " + myLabel + ", this line contains a special text (%start%, %end%, %current%, %currentPlusInterval%, or %next%), but it is not inside a Random section that Repeats:\n" + theLine
      return -29
    tempString = myLineBreak + theLine.rstrip("\n").replace('%start%',startString).replace('%end%',endString).replace('%current%',currentString).replace('%currentPlusInterval%',currentPlusIntervalString)
    if (makeCodeBook):
      outFile.write(tempString.replace("\n", " ").replace("\t", " "))
    else:
      global globalMemory
      if ('%store%' in tempString):
        tempString_strings = tempString.split('%')
        for temp_index in xrange(len(tempString_strings)-3, -1, -1):
          if tempString_strings[temp_index] == 'store':
            globalMemory[tempString_strings[temp_index+1]] = tempString_strings[temp_index+2]
            #if the store special text comes at the beginning or end of the line, it will leave an empty string when splitting, which will make a '%' when joining
            start_index = temp_index
            if ((temp_index == 1) and (tempString_strings[0] == '')):
              start_index = temp_index - 1;
            end_index = temp_index + 3
            if ((temp_index == len(tempString_strings) - 4) and (tempString_strings[temp_index + 3]=='')):
              end_index = temp_index + 4;
            tempString_strings = tempString_strings[:start_index] + tempString_strings[end_index:]
        tempString = '%'.join(tempString_strings)
      if ('%recall%' in tempString):
        tempString_strings = tempString.split('%')
        for temp_index in xrange(len(tempString_strings)-2, -1, -1):
          if tempString_strings[temp_index] == 'recall':
            try:
              tempString = '%'.join(tempString_strings[:temp_index]) + globalMemory[tempString_strings[temp_index+1]] + '%'.join(tempString_strings[temp_index+2:])
            except KeyError:
              print "\nError!  In section " + myLabel + ", this line contains a special text (%recall%), but the variable being recalled '" + tempString_strings[temp_index+1] + "' has not been stored (using %store%):\n" + theLine
              return -34
            tempString_strings = tempString.split('%')
        tempString = '%'.join(tempString_strings)
      global globalDelayedWrite
      if len(globalDelayedWrite)>0 or '%next%' in tempString: globalDelayedWrite += [tempString]
      else: outFile.write(tempString)
    theLine = inFile.readline()
    lineNumber += 1
    if not theLine: #readline returns an empty string when it reaches EOF
      print "\nError!  Could not find *end_leaf* " + myLabel
      print "The program was processing a Leaf section and never found the end tag for that section.  Make sure the end tag is in the file."
      return -11
  return lineNumber


def writeConstant(myNumChoices, myLabel, currentLine, inFile, outFile, saveChoicesFile, txtChoicesFile, myVariableName, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice):
  for i in range(myNumChoices):
    retval = recursiveGenerate(inFile, outFile, saveChoicesFile, txtChoicesFile, myVariableName + '-' + str(i+1), dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice)
    if (retval < 0): return retval
  theLine = inFile.readline()
  if not theLine: #readline returns an empty string when it reaches EOF
    print "\nError!  Reached the end of the file looking for the *end_constant* corresponding to this start tag "+ currentLine
    print "The program was processing a Constant section and had finished going through the subsections but in doing so it got to the end of the file.  Make sure the end tag is in the correct place and that the Constant section has the correct number of subsections."
    return -12
  if ("*end_constant*" + myLabel+" " in theLine):
    print "\nError!  While processing a Constant section, and after processing the subsections, the next line was not *end_constant* corresponding to this start tag "+ currentLine
    print "Make sure the end tag is in the correct location and that the Constant section has the correct number of subsections."
    return -13
  return 1


def writeRandom(temp, inFile, myVariableName, myNumChoices, currentLine, saveChoicesFile, txtChoicesFile, outFile, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice):
  repeat = False
  repeatSame = False
  repeatNever = False
  repeatNoDoubles = False
  repeatDifferentDouble = False
  repeatDifferentDoublePercentage = 0
  nonUniformFirstSubPoint = False
  nonUniformFirstSubPointPercentage = 0
  matchSame = False
  matchDifferent = False
  matchOnlyOneEver = False
  minimumNumberOfEntries = 0;
  maximumNumberOfEntries = 0
  for countSplit in range(3, len(temp)):
    if (temp[countSplit] == "*repeat*") and (len(temp) > countSplit+3):
      repeat = True
      repeatIndicesAreIntegers = True
      try:
        repeatStart = int(temp[countSplit+1])
      except ValueError:
        try:
          repeatStart = float(temp[countSplit+1])
          repeatIndicesAreIntegers = False
        except ValueError:
          print "\nError!  For Repeating section " + myLabel + ", the start value '" + temp[countSplit+1] + "' is neither an integer nor a decimal."
          return -30
      try:
        repeatEnd = int(temp[countSplit+2])
      except ValueError:
        try:
          repeatEnd = float(temp[countSplit+2])
          repeatIndicesAreIntegers = False
        except ValueError:
          print "\nError!  For Repeating section " + myLabel + ", the end value '" + temp[countSplit+2] + "' is neither an integer nor a decimal."
          return -31
      try:
        repeatInterval = int(temp[countSplit+3])
      except ValueError:
        try:
          repeatInterval = float(temp[countSplit+3])
          repeatIndicesAreIntegers = False
        except ValueError:
          print "\nError!  For Repeating section " + myLabel + ", the interval value '" + temp[countSplit+3] + "' is neither an integer nor a decimal."
          return -32
    elif temp[countSplit] == "*repeatSame*": repeatSame = True
    elif temp[countSplit] == "*repeatNever*": repeatNever = True
    elif temp[countSplit] == "*repeatNoDoubles*": repeatNoDoubles = True
    elif (temp[countSplit] == "*repeatDifferentDouble*") and (len(temp) > countSplit+1):
      repeatDifferentDouble = True
      repeatDifferentDoublePercentage = float(temp[countSplit+1])
    elif (temp[countSplit] == "*nonUniformFirstSubPoint*"):
      nonUniformFirstSubPoint = True
      nonUniformFirstSubPointPercentage = float(temp[countSplit+1])
    elif (temp[countSplit] == "*minimumNumberOfEntries*") and (len(temp) > countSplit+1):
      minimumNumberOfEntries = int(temp[countSplit+1])
    elif (temp[countSplit] == "*maximumNumberOfEntries*") and (len(temp) > countSplit+1):
      maximumNumberOfEntries = int(temp[countSplit+1])
    elif temp[countSplit] == "*matchSame*": matchSame = True
    elif temp[countSplit] == "*matchDifferent*": matchDifferent = True
    elif temp[countSplit] == "*matchOnlyOneEver*": matchOnlyOneEver = True
  if matchOnlyOneEver and matchDifferent:
    print "\nWarning! This Random start tag: " + currentLine
    print "specifies both Match Only One Ever and Match Different.  Ignoring Match Different."
  if matchOnlyOneEver and matchSame:
    print "\nError! This Random start tag: " + currentLine
    print "specifies both Match Only One Ever and Match Same, but the two constraints are exclusive.  Fix the template file by removing one of the two constraints."
    return -35
  if matchDifferent and matchSame:
    print "\nError! This Random start tag: " + currentLine
    print "specifies both Match Different and Match Same, but the two constraints are exclusive.  Fix the template file by removing one of the two constraints."
    return -20
  if repeatSame and repeatNever:
    print "\nError! This Random start tag: " + currentLine
    print "specifies both Repeat Same and Repeat Never, but the two constraints are exclusive.  Fix the template file by removing one of the two constraints."
    return -21
  if repeatSame and repeatDifferentDouble:
    print "\nError! This Random start tag: " + currentLine
    print "specifies both Repeat Same and Repeat Different Double (aka non-uniform chance for immediate repeat), but the two constraints are exclusive.  Fix the template file by removing one of the two constraints."
    return -22
  if repeatNever and repeatDifferentDouble:
    print "\nError! This Random start tag: " + currentLine
    print "specifies both Repeat Never and Repeat Different Double (aka non-uniform chance for immediate repeat), but the two constraints are exclusive.  Fix the template file by removing one of the two constraints."
    return -23
  if repeatSame and (minimumNumberOfEntries > 1):
    print "\nError! This Random start tag: " + currentLine
    print "specifies both Repeat Same and a minimum number of entries greater than 1, but the two constraints are exclusive.  Fix the template file by removing one of the two constraints."
    return -37

  global globalDictRangeChoices
  if repeat:
    currentPosition = inFile.tell()
    if repeatIndicesAreIntegers: myRange = range(repeatStart, repeatEnd, repeatInterval)
    else: myRange = frange(repeatStart, repeatEnd, repeatInterval)
    if len(myRange)<1:
      print "\nError! Invalid start/end/interval values for repetition on this start tag: "+ currentLine
      print "Make sure that the interval (the third number after *repeat*) is not zero, and that the start value (the first number after *repeat*) plus some multiple of the interval equals or is past the end value (the second value after *repeat*)."
      return -25
    if (minimumNumberOfEntries > 0) or (maximumNumberOfEntries > 0):
      globalDictRangeChoices[myLabel] = [len(myRange), 0, 0];
    for myIteration in myRange:
      inFile.seek(currentPosition)
      startString = str(repeatStart)
      endString = str(repeatEnd)
      currentString = str(myIteration)
      currentPlusIntervalString = str(myIteration+repeatInterval)
      retval = enterRandomSection(repeatSame, repeatNever, repeatNoDoubles, repeatDifferentDouble, repeatDifferentDoublePercentage, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage, matchSame, matchDifferent, matchOnlyOneEver, myVariableName+'-iter'+str(myIteration), myNumChoices, currentLine, saveChoicesFile, txtChoicesFile, inFile, outFile, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice, minimumNumberOfEntries, maximumNumberOfEntries)
      if retval < 0: return retval
    if len(globalDelayedWrite)>0: replaceNextString(endString, outFile, myLabel)
  else: retval = enterRandomSection(repeatSame, repeatNever, repeatNoDoubles, repeatDifferentDouble, repeatDifferentDoublePercentage, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage, matchSame, matchDifferent, matchOnlyOneEver, myVariableName, myNumChoices, currentLine, saveChoicesFile, txtChoicesFile, inFile, outFile, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice, minimumNumberOfEntries, maximumNumberOfEntries)
  return retval

def writeDependent(temp, inFile, myVariableName, myNumChoices, currentLine, saveChoicesFile, txtChoicesFile, outFile, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice):
  # find previous choice in dictionaryLastChoice
  for countSplit in range(3, len(temp)-1):
    if (temp[countSplit] == "*master*"):
      masterLabel = temp[countSplit + 1]
  if masterLabel in dictionaryLastChoice:
    chosenSubelement = dictionaryLastChoice[masterLabel]
  else:
    print "\nError! This Dependent section " + myLabel + " depends upon the section labeled " + masterLabel + " which has not yet made a choice.\nThe current line is: " + currentLine
    print "Make sure this Dependent section depends upon a Random section, and make sure that Random section must always be visited before this Dependent section.\n"
    return -26
  if chosenSubelement >= myNumChoices:
    print "\nError! This Dependent section does not have enough subsections.  The section it depends on chose element #" + chosenSubelement + " but this Dependent section only has #" + myNumChoices + " subsections.\nThe current line is: " + currentLine
    print "\nMake sure this Dependent section depends upon the correct Random section, make sure that the Random section and the Dependent section have the same number of subsections."
    return -28

  saveChoicesFile.write(currentLine)
  print >>saveChoicesFile, chosenSubelement
  txtChoicesFile.write('\t'+str(chosenSubelement))
  global globalCsvNames, globalCsvData
  globalCsvNames += ",v" + myVariableName
  globalCsvData += "," + str(chosenSubelement+1)
  for i in range(chosenSubelement):
    retval = skipElement(inFile, currentLine)
    if (retval < 0): return retval
  retval = recursiveGenerate(inFile, outFile, saveChoicesFile, txtChoicesFile, myVariableName + "-" + str(chosenSubelement+1), dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice)
  if (retval < 0): return retval
  next_line = ''
  while (not "*end_dependent* "+myLabel+" " in next_line):
    next_line = inFile.readline()
    if not next_line: #readline returns an empty string when it reaches EOF
      print "\nError!  Could not find *end_dependent* for the Dependent section with the label: " + myLabel
      print "The program finished following a subsection for this Dependent section but was unable to find this Dependent section's end tag.  Make sure the end tag is in the file.  Make sure the Random and Constant and Dependent sections have the correct number of subsections."
      return -27
    next_line = next_line.rstrip('\n')+' '
  return 1

def intersection(list1, list2):
  ### returns the intersection and then the items in list2 that are not in list 1
  int_dict = {}
  not_int_dict = {}
  list1_dict = {}
  for e in list1: list1_dict[e] = 1
  for e in list2:
    if list1_dict.has_key(e): int_dict[e] = 1
    else: not_int_dict[e] = 1
  return [int_dict.keys(), not_int_dict.keys()]

def nonUniformShuffle(freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage):
  ### shuffle, but obey nonUniformFirstSubPoint
  shuffle(freeToChoose)
  if (nonUniformFirstSubPoint and (0 in freeToChoose)):
    freeToChoose.remove(0)
    if (random()*100. < nonUniformFirstSubPointPercentage):
      freeToChoose.insert(0, 0)
    else:
      freeToChoose.append(0)

def getChoiceForRepeatSame(myLabel, dictionaryRepeatSame, freeToChoose, myVariableName):
  if myLabel in dictionaryRepeatSame:
    if dictionaryRepeatSame[myLabel] in freeToChoose: chosenSubelement = dictionaryRepeatSame[myLabel]
    else:
      print "\nError! Cannot satisfy both Repeat Same (aka 'Same when repeat') and either Match Different or Match Only One Ever."
      print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName)
      print "\nAny given text file was supposed to choose the same choice each time it encountered this Random section (so this random section, or one of its parents must Repeat).  All of the matched text files were supposed to choose different choices on the same iteration of the repetition.  The program was not able to satisfy both constraints.  The most likely cause is that not all of the matched files encountered this Random section on the same iteration of a parent Random section."
      print "\nFor example, if the first text file chose the first choice on the first iteration, then the second file did not encounter this Random section (due to a different choice in a Random parent), then the first file did not encounter this Random section in the second iteration, and finally the second file chose the first choice on the second iteration (a valid choice since it has not yet chosen anything and the other file did not choose on this repetition), then on any future repetition if they both encounter this Random section they will not be able to satisfy both constraints."
      print "\nThis error may not always occur because the files may choose differently by chance, or because they choose the same but never encounter this Random section on the same iteration."
      print "To alleviate this problem: remove one of the constraints (Repeat Same, Match Different, or Match Only One Ever), add more choices, reduce the number of matched files, or make the parent Random section Match Same so that all matched files encounter this Random section on the same iterations."
      return -14
  else: chosenSubelement = freeToChoose[0]
  return chosenSubelement


def getChoiceForMatchDifferentAndRepeatNever(myLabel, myVariableName, dictionaryRepeatNever, freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage, myNumChoices):
###if matchDifferent and repeatNever, need to precompute all results to prevent a locking situation (or test for inevitable locking)  but what about nested repeats?
###This is a complicated possibility.  If the results for each text file were determined randomly, just avoiding previous choices (for this file and others), then it is possible to enter a blocking situation (e.g., files a and b choose between results 0,1,2 for three repeats.  'a' chooses 201, 'b' randomly chooses 02 and then has no valid third choice).  Furthermore, if this section is nested within a Repeat section, then it is possible that not all of the text files will be making this choice on the same repeat iteration, complicating the generation of optimal permutations across all text files.
###We have decided to do this the dumb/simple way.  The code will take each text file as it comes and each choice as it comes, obeying the rules for Match Different and Repeat Never.  If it runs into a blocking situation, it will error out.
  if myLabel in dictionaryRepeatNever:
    [alreadyTaken, freeToChoose] = intersection(dictionaryRepeatNever[myLabel], freeToChoose)
    if len(freeToChoose) < 1:
      [alreadyTaken, freeToChoose] = intersection(dictionaryRepeatNever[myLabel], range(myNumChoices))
      if len(freeToChoose) < 1:
        print "\nError! Disobeying Repeat Never (aka 'Always different when repeat'), which says that a section should not be chosen more than once in a single text file.  To alleviate this problem: add more choices or reduce the number of repetitions."
        print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName)
        return -24
      else:
        print "\nError!  Failed to obey both Repeat Never (aka 'Always different when repeat') and either Match Different or Match Only One Ever.  This section or one of its parents repeats, and this section is supposed to always choose a different result than any chosen previously for this text file or any other.  It failed.  To alleviate this problem: add more choices, reduce the number of matched files, or reduce the number of repetitions.  This error may occur even if there exists a set of permutations of the choices that obeys both restrictions."
        print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName)
        return -15
    nonUniformShuffle(freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage)
    chosenSubelement = freeToChoose[0]
  else: chosenSubelement = freeToChoose[0]
  return chosenSubelement

def getChoiceForRepeatNeverNotMatchDifferent(myLabel, myVariableName, dictionaryRepeatNever, freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage):
  if myLabel in dictionaryRepeatNever:
    [alreadyTaken, freeToChoose] = intersection(dictionaryRepeatNever[myLabel], freeToChoose)
    if len(freeToChoose) < 1:
      print "\nError! Disobeying Repeat Never (aka 'Always different when repeat'), which says that a section should not be chosen more than once in a single text file.  To alleviate this problem: add more choices or reduce the number of repetitions."
      print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName)
      return -33
    nonUniformShuffle(freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage)
    chosenSubelement = freeToChoose[0]
  else: chosenSubelement = freeToChoose[0]
  return chosenSubelement

def getChoiceForDifferentDouble(repeatDifferentDoublePercentage, dictionaryLastChoice, myLabel, freeToChoose):
  if random()*100. < repeatDifferentDoublePercentage: chosenSubelement = dictionaryLastChoice[myLabel]
  else:
    freeToChoose.remove(dictionaryLastChoice[myLabel])
    freeToChoose += [dictionaryLastChoice[myLabel]] # needed in case there is only one choice
    chosenSubelement = freeToChoose[0]
  return chosenSubelement

def getChoiceForMatchSame(repeatSame, myLabel, myVariableName, dictionaryMatchSame, dictionaryRepeatSame, repeatNever, dictionaryRepeatNever):
    if repeatSame and myLabel in dictionaryRepeatSame and dictionaryMatchSame[myVariableName] != dictionaryRepeatSame[myLabel]:
      print "\nError! Cannot satisfy both Match Same and Repeat Same (aka 'Same when repeat')."
      print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName)
      print "\nThis Random section or one of its parents repeats.  This section is supposed to always choose the same result as it has previously chosen, and is supposed to choose the same result as the matched text files chose on the same iteration of the repetition.  The program was not able to satisfy both requirements.  Most likely this random section is within another random section, and that parent random section does not use Match Same.  So this section does not run on the same iterations for all the matched files.  In the first iteration it did run for this file, no previous file had chosen this section, and this file chose differently than the others.  Then in a future iteration, this file and a previous one both ran, putting the two requirements in conflict."
      print "\nTo solve this problem, make the parent repeating section Match Same, or remove one of the two restrictions.  Alternatively, if the current template file is run again there is a chance that the text files will choose similarly and this error will not appear."
      return -16
    if repeatNever and myLabel in dictionaryRepeatNever and dictionaryMatchSame[myVariableName] in dictionaryRepeatNever[myLabel]:
      print "\nError! Cannot satisfy both Match Same and Repeat Never (aka 'Always different when repeat')."
      print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName)
      print "\nThis Random section or one of its parents repeats.  This section is supposed to always choose the same result as the matched text files chose on the same iteration of the repetition, and this text file is not supposed to contain duplicates. The program was not able to satisfy both requirements. Most likely this random section is within another random section, and that parent random section does not use Match Same.  So this section does not run on the same iterations for all the matched files.  This text file made a choice in an iteration that no previous file chose during.  Then in a later iteration, the previous files made that same choice and now this file cannot satisfy both requirements."
      print "\nTo solve this problem, make the parent repeating section Match Same, or remove one of the two restrictions.  Alternatively, if the current template file is run again there may be a chance that the text files will choose similarly and this error will not appear."
      return -17
    chosenSubelement = dictionaryMatchSame[myVariableName]
    return chosenSubelement
  
def getChosenSubElement(repeatSame, repeatNever, repeatNoDoubles, repeatDifferentDouble, repeatDifferentDoublePercentage, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage, matchSame, matchDifferent, matchOnlyOneEver, myVariableName, myNumChoices, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, dictionaryLastChoice, minimumNumberOfEntries, maximumNumberOfEntries):
  if matchDifferent and myVariableName in dictionaryMatchDifferent:
    [alreadyTaken, freeToChoose] = intersection(dictionaryMatchDifferent[myVariableName], range(myNumChoices))
    if len(freeToChoose) < 1:
      print "\nError! Disobeying Match Different.  Not enough choices."
      print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName)
      print "\nThis random section or one of its parents repeats.  This section is not supposed to have the same result as any of the text files it is matched with for the same iteration in the repetition.  The program was not able to satisfy that requirement.  Add more choices, reduce the number of matched files, or reduce the number of repetitions (check for nested repeating sections)."
      return [-19, -1]
  else: freeToChoose = range(myNumChoices)

  #I should just put repeatNever here like matchDifferent...simplify the below if-elif block of getChoiceFor...

  global globalThisResumeNumber;
  if matchOnlyOneEver and myLabel in dictionaryMatchOnlyOneEver:
    dictOfResumeToChoices = dictionaryMatchOnlyOneEver[myLabel]
    for aResumeNumber in dictOfResumeToChoices:
      if (aResumeNumber != globalThisResumeNumber):
        [alreadyTaken, freeToChoose] = intersection(dictOfResumeToChoices[aResumeNumber], freeToChoose)
    if len(freeToChoose) < 1:
      print "\nError! Disobeying Match One Only Ever (possibly combined with Match Different).  Not enough choices."
      print "The label for this Random section: " + str(myLabel) + ". The 'key' which contains the label and also a concatenated list of the iterations for any ongoing repetitions: " + str(myVariableName) + ". The resume number: " + str(globalThisResumeNumber)
      print "\nThis random section or one of its parents repeats.  This section is not supposed to have the same result as any of the text files it is matched with.  The program was not able to satisfy that requirement.  Add more choices, reduce the number of matched files, or reduce the number of repetitions (check for nested repeating sections)."
      return [-36, -1]

  #deal with minimum and maximum numbers of different subelements
  global globalDictRangeChoices
  if (myLabel in globalDictRangeChoices):  #this should only happen if this label repeats and either minimumNumberOfEntries or maximumNumberOfEntries is set
    [rangeLength, numChoicesAlreadyMade, numTimesChoiceWasDifferentFromLast] = globalDictRangeChoices[myLabel]
    # do we have enough choices left to exactly satisfy the minimum?
    if (minimumNumberOfEntries - numTimesChoiceWasDifferentFromLast >= rangeLength - numChoicesAlreadyMade):
      repeatDifferentDouble = True
      repeatDifferentDoublePercentage = -1.
    if (maximumNumberOfEntries <= numTimesChoiceWasDifferentFromLast):
      repeatDifferentDouble = True
      repeatDifferentDoublePercentage = 101.

  nonUniformShuffle(freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage)
      
  #note that matchDifferent and matchOnlyOneEver behave exactly the same after the freeToChoose variable is populated
  if matchSame and myVariableName in dictionaryMatchSame: chosenSubelement = getChoiceForMatchSame(repeatSame, myLabel, myVariableName, dictionaryMatchSame, dictionaryRepeatSame, repeatNever, dictionaryRepeatNever)
  elif repeatSame: chosenSubelement = getChoiceForRepeatSame(myLabel, dictionaryRepeatSame, freeToChoose, myVariableName)
  elif (matchDifferent or matchOnlyOneEver) and repeatNever: chosenSubelement = getChoiceForMatchDifferentAndRepeatNever(myLabel, myVariableName, dictionaryRepeatNever, freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage, myNumChoices)
  elif repeatNever: chosenSubelement = getChoiceForRepeatNeverNotMatchDifferent(myLabel, myVariableName, dictionaryRepeatNever, freeToChoose, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage)
  elif repeatDifferentDouble and myLabel in dictionaryLastChoice: chosenSubelement = getChoiceForDifferentDouble(repeatDifferentDoublePercentage, dictionaryLastChoice, myLabel, freeToChoose)
  else: chosenSubelement = freeToChoose[0]
  if chosenSubelement < 0: return [chosenSubelement, -1]

  if repeatSame: dictionaryRepeatSame[myLabel] = chosenSubelement
  if matchSame: dictionaryMatchSame[myVariableName] = chosenSubelement
  if matchDifferent:
    if myVariableName in dictionaryMatchDifferent: dictionaryMatchDifferent[myVariableName] += [chosenSubelement]
    else: dictionaryMatchDifferent[myVariableName] = [chosenSubelement]
  if repeatNever:
    if myLabel in dictionaryRepeatNever: dictionaryRepeatNever[myLabel] += [chosenSubelement]
    else: dictionaryRepeatNever[myLabel] = [chosenSubelement]
  if matchOnlyOneEver:
    if myLabel in dictionaryMatchOnlyOneEver:
      if globalThisResumeNumber in dictionaryMatchOnlyOneEver[myLabel]:
        dictionaryMatchOnlyOneEver[myLabel][globalThisResumeNumber] += [chosenSubelement]
      else:
        dictionaryMatchOnlyOneEver[myLabel][globalThisResumeNumber] = [chosenSubelement]
    else:
      dictionaryMatchOnlyOneEver[myLabel] = {}
      dictionaryMatchOnlyOneEver[myLabel][globalThisResumeNumber] = [chosenSubelement]
      
  if myLabel in dictionaryLastChoice and chosenSubelement == dictionaryLastChoice[myLabel]: sameChoiceAsLastTime = True
  else: sameChoiceAsLastTime = False
  dictionaryLastChoice[myLabel] = chosenSubelement
  if (myLabel in globalDictRangeChoices):
    globalDictRangeChoices[myLabel][1] += 1
    if not sameChoiceAsLastTime: globalDictRangeChoices[myLabel][2] += 1;
  return [chosenSubelement, sameChoiceAsLastTime]



def enterRandomSection(repeatSame, repeatNever, repeatNoDoubles, repeatDifferentDouble, repeatDifferentDoublePercentage, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage, matchSame, matchDifferent, matchOnlyOneEver, myVariableName, myNumChoices, currentLine, saveChoicesFile, txtChoicesFile, inFile, outFile, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice, minimumNumberOfEntries, maximumNumberOfEntries):
  [chosenSubelement, sameChoiceAsLastTime] = getChosenSubElement(repeatSame, repeatNever, repeatNoDoubles, repeatDifferentDouble, repeatDifferentDoublePercentage, nonUniformFirstSubPoint, nonUniformFirstSubPointPercentage, matchSame, matchDifferent, matchOnlyOneEver, myVariableName, myNumChoices, myLabel, dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, dictionaryLastChoice, minimumNumberOfEntries, maximumNumberOfEntries)
  if chosenSubelement < 0: return chosenSubelement
  if len(globalDelayedWrite)>0 and not sameChoiceAsLastTime: replaceNextString(currentString, outFile, myLabel)
  saveChoicesFile.write(currentLine)
  print >>saveChoicesFile, chosenSubelement
  txtChoicesFile.write('\t'+str(chosenSubelement))
  global globalCsvNames, globalCsvData
  globalCsvNames += ",v" + myVariableName
  globalCsvData += "," + str(chosenSubelement+1)
  for i in range(chosenSubelement):
    retval = skipElement(inFile, currentLine)
    if (retval < 0): return retval
  if not repeatNoDoubles or not sameChoiceAsLastTime:
    retval = recursiveGenerate(inFile, outFile, saveChoicesFile, txtChoicesFile, myVariableName + "-" + str(chosenSubelement+1), dictionaryRepeatSame, dictionaryRepeatNever, dictionaryMatchSame, dictionaryMatchDifferent, dictionaryMatchOnlyOneEver, startString, endString, currentString, currentPlusIntervalString, dictionaryLastChoice)
    if (retval < 0): return retval
  next_line = ''
  while (not "*end_random* "+myLabel+" " in next_line):
    next_line = inFile.readline()
    if not next_line: #readline returns an empty string when it reaches EOF
      print "\nError!  Could not find *end_random* for the Random section with the label: " + myLabel
      print "The program finished following a subsection for this Random section but was unable to find this Random section's end tag.  Make sure the end tag is in the file.  Make sure the Random and Constant sections have the correct number of subsections."
      return -18
    next_line = next_line.rstrip('\n')+' '
  return 1

def replaceNextString(currentString, outFile, myLabel):
  global globalDelayedWrite
  tempList = []
  readyToPrint = True
  for line in globalDelayedWrite:
    if '%next%'+myLabel+'%' in line: replacedLine = line.replace('%next%'+myLabel+'%', currentString)
    else: replacedLine = line
    if '%next%' in replacedLine: readyToPrint = False
    tempList += [replacedLine]
  if readyToPrint:
    for line in tempList: outFile.write(line)
    globalDelayedWrite = []
  else: globalDelayedWrite = tempList 

def isTemplateFile(filename):
  try:
    inFile = open(filename, 'r')
  except:
    print "Warning! Failed to open the file named '" + filename + "'.  Is it actually a file?"
    return False
  with inFile:
    first_line = inFile.readline()
    if first_line.find("*fragment*") == 0:
      return False
  return True
  
retval = 1;
while retval >= 0:
  print "\n\nResumeRandomizer program, version " + str(Version) + ", last updated " + Date + ".\n"
  templateFileNames = glob.glob('*.rtf')
  templateFileNames = filter(os.path.isfile, templateFileNames)
  if templateFileNames is None or len(templateFileNames)<1:
    print "No .rtf file available...where are the resume template files?  They should be in the same folder as this program."
    raw_input("Press return to quit")
    break

  templateFileNames = filter(isTemplateFile, templateFileNames)
  if templateFileNames is None or len(templateFileNames)<1:
    print "There are .rtf files in the folder, but they do not appear to be template files...where are the resume template files?  They should be in the same folder as this program."
    raw_input("Press return to quit")
    break

  print "Available templates:"
  for i in range(len(templateFileNames)): print str(i+1) + ") " + templateFileNames[i]
  try:
    whichTemplate = int(raw_input('Which template?  (0 to quit) '))
  except ValueError:
    print "Please enter an integer between 0 and "+str(len(templateFileNames))
    continue
  if (whichTemplate < 1):
    print "Bye"
    break
  if (whichTemplate > len(templateFileNames)):
    raw_input("That number is too large.  Press return")
    continue
  whichTemplate-=1
  print "Using template "+ templateFileNames[whichTemplate]
  print
  retval = createResumes(templateFileNames[whichTemplate])

if retval < -1:
  print
  print "ResumeRandomizer has exited with a return code of " + str(retval) + "."
  print "There may have been an error.  If you cannot fix the problem, or need help, contact one of the authors."
  raw_input("Press return to quit")
