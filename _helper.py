#import Autodesk.Revit.DB as DB

import pprint
# from os import system as System
import clr
clr.AddReference('System')
from System.Collections.Generic import List

import json

### Helper function ###
## Print ##
def prettyprint(l):
	pylist = []
	if type(l) == List:
		for elem in elemList:
			pylist.append(elem)
	elif type(l) == list:
		pylist = l
	pp = pprint.PrettyPrinter()
	pp.pprint(pylist)

## List & list conversion ##
def ElemList2PythonList(elemList):
	res = []
	for elem in elemList:
		res.append(elem)
	return res
	
def PythonList2ElemList(pythonList, Type):
	res = List[Type]()


	for elem in pythonList:
		res.Add(elem)
	return res
	
## Batch operations ##
def ElemsToIds(l):
	if type(l) == type(List[Element]()):
		res = List[ElementId]()
		for elem in l:
			res.Add(elem.Id)
	elif type(l) == list():
		res = []
		for elem in l:
			res.append(elem.Id)
	return res

def IdsToElems(l):
	if type(l) == type(List[ElementId]()):
		res = List[Element]()
		for id in l:
			elem = doc.GetElement(id)
			res.Add(elem)
	elif type(l) == type(list()):
		res = []
		for id in l:
			res.append(doc.GetElement(id))
	return res
	
## Get elements ##
def get_viselem():
	all = FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
	all_vis = set()
	# get all family instances
	for elem in all:
		if elem.Category != None and elem.Category.HasMaterialQuantities:
			all_vis.add(elem)
	# get all generic form instances - includes Extrusion, Sweep ... 
	gfs = FilteredElementCollector(doc).OfClass(GenericForm).ToElements()
	for gf in gfs:
		all_vis.add(gf)
	return list(all_vis)

def get_refplane():
	all_rps = set()
	rps = FilteredElementCollector(doc).OfClass(ReferencePlane).ToElements()
	for rp in rps:
		all_rps.add(rp)
	return list(all_rps)

def get_elem_of_type(elem_type):
	return FilteredElementCollector(doc).OfClass(elem_type).ToElements()
	#return FilteredElementCollector(doc).WherePasses(ElementIsElementTypeFilter(elem_type)).WhereElementIsNotElementType().ToElements()
	
## Node functions ##
def getNodeCategories(all):
	''' Given list of all visible Elements and ReferencePlanes, 
		Returns 2 sets of node types in Type object(later to extract Elements), string(to store as json) format  '''
	node_cat_str = set() # string format for json
	node_cat_type = set() # type object
	for elem in all:
		t = elem.GetType()
		node_cat_type.add(t) # set that preserves type - to get elements of type
		node_cat_str.add(t.ToString()[18:])# striping 'Autodesk.Revit.DB.' in front # to add as name in graph
	return node_cat_type, node_cat_str

def printNodeNames(elem_list):
	'''
	Given element list prints node name in "Category id" format 
	- Reference plane -> element.Name
	- GenericForm, FamilyInstance ... -> element.GetType()
	ex) Left 380109 - Family instances, Generic Form, Reference plane
	'''
	for e in elem_list:
		t = e.GetType()
		if t == ReferencePlane:
			print(e.Name + ' ' + e.Id.ToString())
		else:
			print(t.ToString().strip('Autodesk.Revit.DB.') + ' ' + e.Id.ToString())

def getTupleFromElem(elem):
	''' 
	Given Element, Returns node/edge tuple in (uniqueId, category_str) format 
	'''
	return (elem.UniqueId, elem.Id.ToString(), *getElemTypeStr(elem))


def getElemTypeStr(elem):
	''' 
	Given Element, Return category name
	Used to create (uniqueId, category_str) tuple
	- Reference plane -> element.Name
	- GenericForm, FamilyInstance ... -> element.GetType()
	- Alignment, Default linear style, Line, Symbolic Line -> element.Name

	Name is used for labeling (if exists), Type is used for coloring
	'''
	t = elem.GetType()
	# ReferencePlane
	# Alignment, Default linear style, Line
	if t == ReferencePlane or t == Dimension:
		return (t.ToString(), elem.Name)
	# Node that is not ReferencePlane
	else: 
		return (t.ToString()[18:], None)

def isNode(elem):
	'''
	Given Element, Return True if Node (ReferencePlane, Extrusion, Sweep, FamilyInstance)
	'''
	t = elem.GetType()
	if t == ReferencePlane or t == FamilyInstance or t == Extrusion or t == Sweep:
		return True
	else:
		return False

def isEdge(elem):
	'''
	Given Element, Return True if Edge (Alignment, Line, Default linear style)
	'''
	t = elem.GetType()
	if t == Dimension: #Alignment, Default linear style
		t = elem.Name
		if (t == "Alignment" or ("Default linear style" in t)): # there are some named with space at end!
			return True
		else: 
			return False
	elif t == ModelLine: #Line
		return True
	else:
		return False

