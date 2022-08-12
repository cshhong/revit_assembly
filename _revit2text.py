'''
For all visible components in Revit family,
getting constraint informations by
Try moving for all 3 directions, which will likely cause a constraint error
record failing elements in text file
to later convert to dictionary and then to node-edge graph in TEST2NETWORK
'''

import Autodesk.Revit.DB as DB
import Autodesk.Revit.UI as UI
from System.Collections.Generic import List
import pprint
import json
import sys
import logging

######################## Helper function ############################ 
#Also in helper.py file, but needed here to run in RevitPython. 

########### Print ###########
def prettyprint(l):
	pylist = []
	if type(l) == List:
		for elem in elemList:
			pylist.append(elem)
	elif type(l) == list:
		pylist = l
	pp = pprint.PrettyPrinter()
	pp.pprint(pylist)

########### List & list conversion ###########
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
	
########### Batch operations ###########
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
	
########### Get elements ###########
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
	
########### Node functions ###########
def getNodeCategories(all):
	''' Given list of all visible Elements and ReferencePlanes, 
		Returns 2 sets of node types in Type object(later to extract Elements), string(to store as json) format  '''
	node_cat = set() # string format for json
	node_cat_type = set() # type object
	for elem in all:
		t = elem.GetType()
		node_cat_type.add(t) # set that preserves type - to get elements of type
		# print(t)
		node_cat.add(t.ToString()[18:])# striping 'Autodesk.Revit.DB.' in front # to add as name in graph
	return node_cat_type, node_cat

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
	return (elem.UniqueId, elem.Id.ToString(), getElemTypeStr(elem))


def getElemTypeStr(elem):
	''' 
	Given Element, Return category name
	Used to create (uniqueId, category_str) tuple
	- Reference plane -> element.Name
	- GenericForm, FamilyInstance ... -> element.GetType()
	- Alignment, Default linear style, Line, Symbolic Line -> element.Name
	'''
	t = elem.GetType()
	# ReferencePlane
	# Alignment, Default linear style, Line
	if t == ReferencePlane or t == Dimension:
		return elem.Name
	# Node that is not ReferencePlane
	else: 
		return t.ToString()[18:]

def isNode(elem):
	'''
	Given Element, Return True if Node (ReferencePlane, Extrusion, Sweep, FamilyInstance)
	'''
	t = elem.GetType()
	if t == ReferencePlane or t == FamilyInstance or t == Extrusion or t == Sweep or t==Revolution or t==Wall or t==SymbolicCurve:
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



######################## Main ############################ 
'''
1. List of visible elements
2. for each element, open transaction, move to each direction
	2-1. Get Error, related elements 
	2-2. add to text file
3. with text file - add node and edges

References: 
 - Handling errors: https://knowledge.autodesk.com/support/revit/learn-explore/caas/CloudHelp/cloudhelp/2014/ENU/Revit/files/GUID-52A45CC1-3BB4-48B4-BFC7-F6F8666C2AA4-htm.html
 - IFailuresPreprocessor Interface : https://www.revitapidocs.com/2015/053c6262-d958-b1b6-44b7-35d0d83b5a43.htm
 - Using IFailuresPreprocessor to rollback transaction in the event of a failure : https://forum.dynamobim.com/t/using-ifailurespreprocessor-to-rollback-transaction-in-the-event-of-a-failure/67222
 - Gathering and Returning Failure Information : https://thebuildingcoder.typepad.com/blog/2018/01/gathering-and-returning-failure-information.html
'''

class ExtractConstraintHandler(DB.IFailuresPreprocessor):
	'''
	Creating handler to deal with Errors
	We use handler to access elements related to error
	Error related elements are recorded in string format and printed to edge_list_org.txt file through sys.stout
	'''
	def __init__(self):
		self.des = "  "
		self.edgeDict = dict()

	def PreprocessFailures(self, FailuresAccessor): # FailureProcessingResult in C#
		# FailureProcessingResult(FailuresAccessor) : Notifies end of transaction code about further actions
		# DB.FailuresAccessor : interface class that provides access to the failure info
		# instance can be only obtained as arguement passed to interfaces used in process of failure resolution 
		failList = List[FailureMessageAccessor]() # inside event handler, retrieve all warnings
		for f in FailuresAccessor.GetFailureMessages():
			self.des = f.GetDescriptionText()
			fail_elem = IdsToElems(f.GetFailingElementIds())
			#fail_uid = []

			##### TODO : Formatting as Data Dictionary - only show message per element? or for all elements?
			# try to use json.dumps(dict) -> return string!
			nodes = list()
			subedges = list()
			for e in fail_elem:
				uid, id, typestr = getTupleFromElem(e)
				if isNode(e):
					nodes.append([uid, id, typestr])
					#nodes.append(list(getTupleFromElem(e))).replace("'", '"') # format tuple into array(list) and double quotes with json
				elif isEdge(e):
					subedges.append([uid, id, typestr])
					#subedges.append(list(getTupleFromElem(e))).replace("'", '"')
				#fail_uid.append()
			#self.elems.append(self.des + ':' + '\n'.join(fail_uid)) # list of strings (tuples put together)

			
			if len(nodes)!=0 and len(subedges)!=0:
				edgeDict = dict()
				edgeDict["nodes"] = nodes
				edgeDict["subedges"] = subedges
				edgeDict_str = json.dumps(edgeDict)
				print(edgeDict_str + ',') # format to create list of Edge Dictionaries

			#logging.info(self.edgeDict)

			
		#print('\n')
		#print(self.elems)
		

		return FailureProcessingResult.Continue
		
	def ShowDialogue(self):
		'''
		What to show in Task Dialog
		Meant for debugging
		'''
		fail_elems = json.dumps(self.edgeDict) # For debugging - only gets the last one

		ConstrD = TaskDialog("Constraints for this Element!")
		ConstrD.MainInstruction = "selected object name?"
		ConstrD.MainContent = fail_elems
		
		TaskDialog.Show(ConstrD)

		
		
		### Currently TaskDialog only writes in title - Task Dialog Class Example! https://www.revitapidocs.com/2017/853afb57-7455-a636-9881-61a391118c16.htm
		### Extract TaskDialog to text file!! https://forums.autodesk.com/t5/revit-api-forum/copy-the-massage-that-shows-on-taskdialog/td-p/9452620


abs_path = 'C:\Users\hongc\OneDrive - Autodesk\Chloe_Hong\RevitPython'
# get type list of all visible elements + reference planes
all_vis = get_viselem()
all_rps = get_refplane()
all = all_vis + all_rps
#print("### All Node Elements:")
#pprint.pprint(all, indent=5)
node_cat_txt = open(abs_path + '\\node_cat.txt', 'w') #for some reason FamilyInstance type disappears when converting to list?!

node_cat_type, node_cat_str = getNodeCategories(all)
node_cat = list(node_cat_str)
node_cat_txt.write(json.dumps(node_cat))
node_cat_txt.close()


# print('### node_cat: ')
# pprint.pprint(node_cat, indent=5)

## For Testing
# sel_ids = uidoc.Selection.GetElementIds()
# sel_elem = [doc.GetElement(i) for i in sel_ids]

# for sel in sel_elem:
# Set path to print console - This is how we extract error related elements to text file!
sys.stdout = open(abs_path + '\edge_list_org.txt', 'w')

for vis in all:
	# Create Transation to temporarily move element
	trans = DB.Transaction(doc, "test")
	# Set transaction failure handler to Extract Constraint Handler
	failureHandlingOptions = trans.GetFailureHandlingOptions()
	handler = ExtractConstraintHandler()
	failureHandlingOptions.SetFailuresPreprocessor(handler)
	trans.SetFailureHandlingOptions(failureHandlingOptions)
	# Start transaction and move element
	trans.Start()
	new_XYZ = XYZ(100,200,300)
	ElementTransformUtils.MoveElement(doc, vis.Id, new_XYZ)
	# Reset changes and end transaction
	trans.RollBack()
	# option to show dialog
	handler.ShowDialogue()
	
# Set path to print console - This is how we extract error related elements to text file!
sys.stdout.close()	






######################## Error to Data text file ############################
'''
Types of Error related element groups (Node - Edge - Node combinations):
    Reference Plane - Alignment - FamilyInstance(GenericModel)
    Reference Plane - Alignment - Sweep
    Reference Plane - Alignment - FamilyInstance

    Reference Plane - Line - Alignment - Sweep/Extrusion
    Reference Plane - Line - Default linear style - Sweep/Extrusion

    Sweep/Extrusion - Alignment - Sweep/Extrusion
    Sweep/Extrusion - Line - Alignment - Sweep/Extrusion

'''