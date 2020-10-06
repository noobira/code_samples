import math
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
from maya import cmds
import time

rbfNodeName = "vvsRBFNode"
rampNodeName = "vvsRAMPNode"
rbfNodeId = om.MTypeId(0x00008)
rampNodeId = om.MTypeId(0x00009)


def store_to_array_by_index(array_data_handle, index, double_value):
    try:
        array_data_handle.jumpToElement(index)
    except:
        array_builder_handle = array_data_handle.builder()
        array_builder_handle.addElement(index)
        array_data_handle.set(array_builder_handle)
        array_data_handle.jumpToElement(index)
    array_data_handle.outputValue().setDouble(double_value)

def matrix_to_translation(matrix):
    mTransformMtx = om.MTransformationMatrix(matrix)
    trans = mTransformMtx.translation(om.MSpace.kWorld)
    return [trans.x, trans.y, trans.z]

def euclidean_distance(translation_point_1, translation_point_2):
    vector = []
    for i in range(3):
        vector.append(translation_point_1[i] - translation_point_2[i])
    return math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)


class RBFNode(ompx.MPxNode):
    inMainObj = om.MObject()
    inSecObjs = om.MObject()
    inMode = om.MObject()
    outWeights = om.MObject()
    

    def __init__(self):
        ompx.MPxNode.__init__(self)

    def compute(self, plug, dataBlock):
        if plug != RBFNode.outWeights:
            return om.kUnknownParameter

        # time1 = time.clock()
        # get handles
        input_mode_handle = dataBlock.inputValue(RBFNode.inMode)
        input_main_tr_handle = dataBlock.inputValue(RBFNode.inMainObj)
        input_array_of_sec_matr_handle = dataBlock.inputArrayValue(RBFNode.inSecObjs)
        output_array_data_handle = dataBlock.outputArrayValue(RBFNode.outWeights)

        tr_main = input_main_tr_handle.asDouble3()

        mode = input_mode_handle.asInt()
        inverted_distances = []
        infinity_flag = False
        num_sec_matrices = input_array_of_sec_matr_handle.elementCount()

        i = 0
        while i < num_sec_matrices:
            input_array_of_sec_matr_handle.jumpToArrayElement(i)
            tr_sec = input_array_of_sec_matr_handle.inputValue().asDouble3()

            # get the world translations from input matrices to calculate distance
            # tr_sec = matrix_to_translation(secondary_matrix)

            distance = euclidean_distance(tr_main, tr_sec)

            #vect = om.MVector(tr_sec[0]-tr_main[0], tr_sec[1]-tr_main[1], tr_sec[2]-tr_main[2])
            #distance = vect.length()

            if distance == 0:
                inverted_distance = 0.0
                infinity_flag = True
                break
            else:
                if mode == 0: # linear
                    inverted_distance = 1.0 / distance
                elif mode == 1: # quadratic
                    inverted_distance = 1.0 / distance ** 2
                else: # cubic
                    inverted_distance = 1.0 / distance ** 3
            inverted_distances.append(inverted_distance)
            i += 1


        if infinity_flag:
            for j in range(num_sec_matrices):
                if j == i:
                    store_to_array_by_index(output_array_data_handle, j, 1.0)
                else:
                    store_to_array_by_index(output_array_data_handle, j, 0.0)
        else:
            # num_sec_matrices == len(distances)
            # sum_inv_distance = 0.0
            # for i in range(num_sec_matrices):
            #     sum_inv_distance += inverted_distances[i]
            sum_inv_distance = math.fsum(inverted_distances)
            for i in range(num_sec_matrices):
                store_to_array_by_index(output_array_data_handle, i, inverted_distances[i]/sum_inv_distance)

        # set output array
        output_array_data_handle.setAllClean()
        dataBlock.setClean(plug)
        # time2 = time.clock()
        # print time2-time1


def rbfCreator():
    return ompx.asMPxPtr(RBFNode())

def rbfInitializer():
    # 1. creating a function set for numeric attributes
    mFnAttr = om.MFnNumericAttribute()
    #mFnAttr_matrix = om.MFnMatrixAttribute()

    # 2. create the attributes

    RBFNode.outWeights = mFnAttr.create("weights", "weights", om.MFnNumericData.kDouble)
    mFnAttr.setWritable(0)
    mFnAttr.setStorable(0)
    mFnAttr.setArray(1)
    mFnAttr.setUsesArrayDataBuilder(1)
    mFnAttr.setIndexMatters(0)
    RBFNode.addAttribute(RBFNode.outWeights)

    mFn_enum = om.MFnEnumAttribute()
    RBFNode.inMode = mFn_enum.create("mode", "mode")
    mFn_enum.addField("linear", 0)
    mFn_enum.addField("quadratic", 1)
    mFn_enum.addField("cubic", 2)
    mFn_enum.setKeyable(1)
    RBFNode.addAttribute(RBFNode.inMode)
    RBFNode.attributeAffects(RBFNode.inMode, RBFNode.outWeights)

    RBFNode.inMainObj = mFnAttr.create("main_tr", "main_tr", om.MFnNumericData.k3Double)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    RBFNode.addAttribute(RBFNode.inMainObj)
    RBFNode.attributeAffects(RBFNode.inMainObj, RBFNode.outWeights)


    RBFNode.inSecObjs = mFnAttr.create("sec_tr", "sec_tr", om.MFnNumericData.k3Double)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    mFnAttr.setArray(1)
    mFnAttr.setIndexMatters(0)
    RBFNode.addAttribute(RBFNode.inSecObjs)
    RBFNode.attributeAffects(RBFNode.inSecObjs, RBFNode.outWeights)

class RAMPNode(ompx.MPxNode):
    outWeights = om.MObject()
    inStart = om.MObject()
    inEnd = om.MObject()
    inOffset = om.MObject()
    inAxis = om.MObject()
    inPoints = om.MObject()
    inSymmetry = om.MObject()
    inInvert = om.MObject()
    inPrecision = om.MObject()


    def find_weights(self, cv_array, min_v, max_v, offset_v, axis, invert):
        if max_v <= min_v:
            return
        interval = max_v - min_v

        for i in range(cv_array.length()):
            val = cv_array[i][axis]
            if val < min_v + offset_v:
                if invert:
                    cv_array[i].w = 1.0
                else:
                    cv_array[i].w = 0.0
            elif min_v + offset_v <= val <= max_v + offset_v:
                if invert:
                    new_weight = (-math.cos(  (val-min_v-offset_v)*math.pi/interval + math.pi  ) + 1.0) / 2.0
                else:
                    new_weight = (math.cos(  (val-min_v-offset_v)*math.pi/interval + math.pi  ) + 1.0) / 2.0
                cv_array[i].w = new_weight

            elif val > max_v + offset_v:
                if invert:
                    cv_array[i].w = 0.0
                else:
                    cv_array[i].w = 1.0
            else:
                continue

        


    def __init__(self):
        ompx.MPxNode.__init__(self)

    def compute(self, plug, dataBlock):
        if plug != RAMPNode.outWeights:
            return om.kUnknownParameter
        # read input handles
        output_array_data_handle = dataBlock.outputArrayValue(RAMPNode.outWeights)
        min_v = dataBlock.inputValue(RAMPNode.inStart).asDouble()
        max_v = dataBlock.inputValue(RAMPNode.inEnd).asDouble()
        offset_v = dataBlock.inputValue(RAMPNode.inOffset).asDouble()
        axis_v = dataBlock.inputValue(RAMPNode.inAxis).asInt()
        sym_v = dataBlock.inputValue(RAMPNode.inSymmetry).asBool()
        invert_v = dataBlock.inputValue(RAMPNode.inInvert).asBool()
        precision_v = dataBlock.inputValue(RAMPNode.inPrecision).asInt()
        input_array_data_handle = dataBlock.inputArrayValue(RAMPNode.inPoints)
        element_count = input_array_data_handle.elementCount()

        # translate input array of float3 points to array of MPoints with w=1 (by default)
        curve_cvs = om.MPointArray()
        for i in range(element_count):
            input_array_data_handle.jumpToArrayElement(i)
            inputValue = input_array_data_handle.inputValue().asDouble3()
            curve_cvs.append(om.MPoint(inputValue[0], inputValue[1], inputValue[2]))


        # calculating weights
        self.find_weights(curve_cvs, min_v, max_v, offset_v, axis_v, invert_v)

        if sym_v:
            int_prec = len(str(precision_v))
            some_dict = {}
            for i in range(curve_cvs.length()):
                some_dict[round( curve_cvs[i][axis_v], int_prec )] = i

            for i in range(curve_cvs.length()):
                val = round( curve_cvs[i][axis_v], int_prec )
                if val <= 0.0:
                    store_to_array_by_index(output_array_data_handle, i, curve_cvs[i].w)
                    try:
                        j = some_dict[-val]
                        store_to_array_by_index(output_array_data_handle, j, curve_cvs[i].w)
                    except:
                        pass
                else:
                    continue
            

        else:
        # store found weights to the output
            for i in range(curve_cvs.length()):
                store_to_array_by_index(output_array_data_handle, i, curve_cvs[i].w)

        # set output as clean for clean-dirty propogation 
        output_array_data_handle.setAllClean()
        dataBlock.setClean(plug)

def rampCreator():
    return ompx.asMPxPtr(RAMPNode())

def rampInitializer():
    # 1. creating a function set for numeric attributes
    mFnAttr = om.MFnNumericAttribute()

    # 2. create the attributes

    RAMPNode.outWeights = mFnAttr.create("targetWeights", "targetWeights", om.MFnNumericData.kDouble)
    mFnAttr.setWritable(0)
    mFnAttr.setStorable(0)
    mFnAttr.setArray(1)
    mFnAttr.setUsesArrayDataBuilder(1)
    mFnAttr.setIndexMatters(0)
    RAMPNode.addAttribute(RAMPNode.outWeights)

    RAMPNode.inStart = mFnAttr.create("start", "start", om.MFnNumericData.kDouble)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    RAMPNode.addAttribute(RAMPNode.inStart)
    RAMPNode.attributeAffects(RAMPNode.inStart, RAMPNode.outWeights)

    RAMPNode.inEnd = mFnAttr.create("end", "end", om.MFnNumericData.kDouble)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    RAMPNode.addAttribute(RAMPNode.inEnd)
    RAMPNode.attributeAffects(RAMPNode.inEnd, RAMPNode.outWeights)

    RAMPNode.inOffset = mFnAttr.create("offset", "offset", om.MFnNumericData.kDouble)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    RAMPNode.addAttribute(RAMPNode.inOffset)
    RAMPNode.attributeAffects(RAMPNode.inOffset, RAMPNode.outWeights)

    RAMPNode.inSymmetry = mFnAttr.create("sym", "sym", om.MFnNumericData.kBoolean)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    RAMPNode.addAttribute(RAMPNode.inSymmetry)
    RAMPNode.attributeAffects(RAMPNode.inSymmetry, RAMPNode.outWeights)

    RAMPNode.inInvert = mFnAttr.create("inv", "inv", om.MFnNumericData.kBoolean)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    RAMPNode.addAttribute(RAMPNode.inInvert)
    RAMPNode.attributeAffects(RAMPNode.inInvert, RAMPNode.outWeights)

    RAMPNode.inPrecision = mFnAttr.create("Precision", "Precision", om.MFnNumericData.kInt)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    mFnAttr.setDefault(1000)
    RAMPNode.addAttribute(RAMPNode.inPrecision)
    RAMPNode.attributeAffects(RAMPNode.inPrecision, RAMPNode.outWeights)

    RAMPNode.inPoints = mFnAttr.create("controlPoints", "controlPoints", om.MFnNumericData.k3Double)
    mFnAttr.setReadable(1)
    mFnAttr.setWritable(1)
    mFnAttr.setStorable(1)
    mFnAttr.setKeyable(1)
    mFnAttr.setArray(1)
    mFnAttr.setIndexMatters(0)
    RAMPNode.addAttribute(RAMPNode.inPoints)
    RAMPNode.attributeAffects(RAMPNode.inPoints, RAMPNode.outWeights)

    mFn_enum = om.MFnEnumAttribute()
    RAMPNode.inAxis = mFn_enum.create("axis", "axis")
    mFn_enum.addField("x", 0)
    mFn_enum.addField("y", 1)
    mFn_enum.addField("z", 2)
    mFn_enum.setKeyable(1)
    RAMPNode.addAttribute(RAMPNode.inAxis)
    RAMPNode.attributeAffects(RAMPNode.inAxis, RAMPNode.outWeights)



def initializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject, 'VVS', '666', 'Any')
    try:
        mplugin.registerNode(rbfNodeName, rbfNodeId, rbfCreator, rbfInitializer, ompx.MPxNode.kDependNode)
        mplugin.registerNode(rampNodeName, rampNodeId, rampCreator, rampInitializer, ompx.MPxNode.kDependNode)
    except:
        om.MGlobal.displayError("Error load VVS plugin)")


def uninitializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(rbfNodeId)
        mplugin.deregisterNode(rampNodeId)
    except:
        om.MGlobal.displayError("Error unload VVS plugin)")
