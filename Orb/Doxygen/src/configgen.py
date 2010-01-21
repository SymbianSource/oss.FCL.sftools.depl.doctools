# python script to generate configoptions.cpp from config.xml
#
# Copyright (C) 1997-2008 by Dimitri van Heesch.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation under the terms of the GNU General Public License is hereby 
# granted. No representations are made about the suitability of this software 
# for any purpose. It is provided "as is" without express or implied warranty.
# See the GNU General Public License for more details.
#
# Documents produced by Doxygen are derivative works derived from the
# input used in their production; they are not affected by this license.
#
import xml.dom.minidom
from xml.dom import minidom, Node

def addValues(var,node):
        for n in node.childNodes:
		if n.nodeType == Node.ELEMENT_NODE:
			name = n.getAttribute('name');
			print "  %s->addValue(\"%s\");" % (var,name)
	
def parseOption(node):
	name    = node.getAttribute('id')
	type    = node.getAttribute('type')
	format  = node.getAttribute('format')
	doc     = node.getAttribute('docs')
	defval  = node.getAttribute('defval')
	adefval = node.getAttribute('altdefval')
	depends = node.getAttribute('depends')
	# replace \ by \\, replace " by \", and '  ' by a newline with end string and start string at next line
        docC    = doc.strip().replace('\\','\\\\').replace('"','\\"').replace('  ','\\n"\n                 "')
	print "  //----"
        if type=='bool':
        	if len(adefval)>0:
			enabled = adefval
		else:
			enabled = "TRUE" if defval=='1' else "FALSE"
		print "  cb = cfg->addBool("
		print "                 \"%s\"," % (name)
		print "                 \"%s\"," % (docC)
		print "                 %s"  % (enabled)
                print "                );"
		if depends!='':
			print "  cb->addDependency(\"%s\");" % (depends)
	elif type=='string':
		print "  cs = cfg->addString("
		print "                 \"%s\"," % (name)
		print "                 \"%s\""  % (docC)
                print "                );"
		if defval!='':
			print "  cs->setDefaultValue(\"%s\");" % (defval)
		if format=='file':
			print "  cs->setWidgetType(ConfigString::File);"
		elif format=='dir':
			print "  cs->setWidgetType(ConfigString::Dir);"
		if depends!='':
			print "  cs->addDependency(\"%s\");" % (depends)
	elif type=='enum':
		print "  ce = cfg->addEnum("
		print "                 \"%s\"," % (name)
		print "                 \"%s\"," % (docC)
		print "                 \"%s\""  % (defval)
                print "                );"
                addValues("ce",node)
		if depends!='':
			print "  ce->addDependency(\"%s\");" % (depends)
	elif type=='int':
		minval = node.getAttribute('minval')
		maxval = node.getAttribute('maxval')
		print "  ci = cfg->addInt("
		print "                 \"%s\"," % (name)
		print "                 \"%s\"," % (docC)
		print "                 %s,%s,%s" % (minval,maxval,defval)
                print "                );"
		if depends!='':
			print "  ci->addDependency(\"%s\");" % (depends)
	elif type=='list':
		print "  cl = cfg->addList("
		print "                 \"%s\"," % (name)
		print "                 \"%s\""  % (docC)
                print "                );"
		addValues("cl",node)
		if depends!='':
			print "  cl->addDependency(\"%s\");" % (depends)
		if format=='file':
			print "  cl->setWidgetType(ConfigList::File);"
		elif format=='dir':
			print "  cl->setWidgetType(ConfigList::Dir);"
		elif format=='filedir':
			print "  cl->setWidgetType(ConfigList::FileAndDir);"
	elif type=='obsolete':
		print "  cfg->addObsolete(\"%s\");" % (name)
		



def parseGroups(node):
	name = node.getAttribute('name')
	doc  = node.getAttribute('docs')
        print "  //---------------------------------------------------------------------------";
	print "  cfg->addInfo(\"%s\",\"%s\");" % (name,doc)
        print "  //---------------------------------------------------------------------------";
        print
        for n in node.childNodes:
		if n.nodeType == Node.ELEMENT_NODE:
			parseOption(n)
	

def main():
	doc = xml.dom.minidom.parse("config.xml")
	elem = doc.documentElement
        print "/* WARNING: This file is generated!"
        print " * Do not edit this file, but edit config.xml instead and run"
        print " * python configgen.py to regenerate this file!"
        print " */"
        print ""
        print "#include \"configoptions.h\""
        print "#include \"config.h\""
        print "#include \"portable.h\""
        print ""
        print "void addConfigOptions(Config *cfg)"
        print "{"
        print "  ConfigString *cs;"
        print "  ConfigEnum   *ce;"
        print "  ConfigList   *cl;"
        print "  ConfigInt    *ci;"
        print "  ConfigBool   *cb;"
        print ""
	for n in elem.childNodes:
		if n.nodeType == Node.ELEMENT_NODE:
			parseGroups(n)
        print "}"

if __name__ == '__main__':
	main()

