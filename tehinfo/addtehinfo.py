#   Teh Info: Adds miscellaneous info extracted from csv files (\t separated) to anki fields .
#   Copyright (C) 2014 Abimael Martinez <abijr.mtz@gmail.com>, Ian Worthington <Worthy.vii@gmail.com>
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
import os, re
from anki.utils import stripHTML
# import the main window object (mw) from ankiqt
from aqt import mw

# Get the path to this plugin's directory
this_dir, this_filename = os.path.split(__file__)

# infoDir
info_dir = os.path.join(this_dir, "info")


#this is annoyingly useful
joinseparator = ','


sources = {
    'henshall':             'henshall.tsv',
    'Skip Code':            'skip_codes.tsv',
    'heisig index':         'heisig.tsv',
    'heisig index (old)':   'heisig_old.tsv',
    'heisig keywords':      'heisig_keywords.tsv',
}

def readInfo(sourceInfo):
    # Data from csv's goes here
    kanjiIndex = dict()
    info = os.path.join(info_dir, sources[sourceInfo])
    with open(info, 'r') as f:
        content = f.read().splitlines()
        #sys.stderr.write(content[0] + "\n")
    f.close() 
    for line in content:
        fieldhash = dict(zip(('kanji', 'info'),
                            line.split('\t')))
        kanjiIndex[fieldhash['kanji'].decode('utf8')] = fieldhash
    return kanjiIndex
    
  
#get user to select from a list
def getKeyFromList(titleText, labelText, strings):
        
    d = QInputDialog()
    d.setComboBoxItems(strings)
    d.setWindowTitle(titleText)
    d.setLabelText(labelText)
    d.setOption(QInputDialog.UseListViewForComboBoxItems)
       
    
    if d.exec_()==1:
        return d.textValue()

      
def addInfo(nids, sourceName):

    fields = []

    anote=mw.col.getNote(nids[0])
    #get the fields of the first note
    for (i, f) in anote.items():
        fields.append(i)
    
    #get input/output fields from user
    expField = getKeyFromList("Select field to read from", "Read relevant kanji/expression from:", fields)
    if (expField is None):
        return
    infoDstField = getKeyFromList("Select field to write to", "Write {} to:".format(sourceName), fields)
    if (infoDstField is None):
        return
    
    
    mw.checkpoint("Add {} info".format(sourceName))
    mw.progress.start()
    kanjiIndex = readInfo(sourceName)
    
    #For each seleccted card
    for nid in nids:
        note = mw.col.getNote(nid)
        src = None
        if expField in note:
            src = expField
        if not src:
            # no src field then next card
            continue
        dst = None
        if infoDstField in note:
            dst = infoDstField
        if not dst:
            # no dst field then skip card
            continue
        srcTxt = mw.col.media.strip(note[src])
        if not srcTxt.strip():
            continue
        #Add the data to the dst field
        num = joinseparator.join(lookupKanjiInfo(srcTxt, kanjiIndex, 'info'))
        if num!=0:
            note[dst] = str(num)
        #sys.stderr.write("Results:" + note[dst])
        note.flush()
    mw.progress.finish()
    mw.reset()
    

def lookupKanjiInfo(wordsTxt, kanjiIndex, key):
    # Get only the kanji
    words = re.findall(ur'[\u4e00-\u9fbf]',wordsTxt)
    results = []
    for word in words:
        if (word in kanjiIndex):
            results.append(kanjiIndex[word][key]) 
        else:
            results.append('??')
    return results    

   
def setupMenu(browser):

    browser.form.menuEdit.addSeparator()
    
    tehInfoMenu = browser.form.menuEdit.addMenu('Add TehInfo')
    
    for k, v in sources.iteritems():
        action = "Add {} Info".format(k)
        a = QAction(action, browser)
        tehInfoMenu.addAction(a)
        browser.connect(a, SIGNAL("triggered()"), lambda e=browser, s=k: onAddTehInfo(e, s))

                    
def onAddTehInfo(browser, k):
    addInfo(browser.selectedNotes(), k)
    


addHook("browser.setupMenus", setupMenu)
