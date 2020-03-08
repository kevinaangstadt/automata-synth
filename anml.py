# useful for manipulating ANML files

import os, sys

import untangle

class AnmlDefs(object):
    NO_START = "none"
    START_OF_DATA = "start-of-data"
    ALL_INPUT = "all-input"
    
    STE_PORT = "ste"
    T1_PORT = "t1"
    T2_PORT = "t2"
    T3_PORT = "t3"
    COUNT_ONE_PORT = "cnt"
    RESET_PORT = "rst"

class CounterMode:
    STOP_HOLD = "latch"
    ROLLOVER_PULSE = "roll"
    STOP_PULSE = "pulse"
    
class BooleanMode:
    AND = "and"
    OR = "or"
    SOP2 = "sum-of-products"
    POS2 = "product-of-sums"
    NAND = "nand"
    NOR = "nor"
    NSOP = "nsum-of-products"
    NPOS = "nproduct-of-sums"
    NOT = "inverter"

class AnmlNetwork(object):
    def __init__(self, id):
        self.id = id
        self.elements = dict()
    
    def __str__(self):
        anml = "<anml version=\"1.0\"  xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
        anml += "\n<automata-network id=\"" + self.id + "\" >"
        
        for _,e in self.elements.iteritems():
            anml += "\n" + str(e)
        
        anml += "\n</automata-network>"
        anml += "\n</anml>"
        
        return anml
        
    def getElementByID(self, id):
        return self.elements[id]
    
    def AddSTE(self,
               symbols,
               startType = AnmlDefs.NO_START,
               anmlId = None,
               reportCode = 0,
               match = False,
               latched = False
              ):
        if anmlId in self.elements:
            raise AnmlDuplicateId('this anmlId already exists: ' + anmlId)
        
        new_ste = STE(symbols, startType=startType, anmlId=anmlId, reportCode=reportCode, match=match, latched=latched)
        
        self.elements[anmlId] = new_ste
        
        return new_ste
    
    def AddCounter(self,
                   target,
                   mode = CounterMode.STOP_HOLD,
                   anmlId = None,
                   reportCode = 0,
                   match = False,
                   cnt_used = 0
                  ):
        if anmlId in self.elements:
            raise AnmlDuplicateId('this anmlId already exists: ' + anmlId)
        
        new_counter = Counter(target, mode=mode, anmlId=anmlId, reportCode=reportCode, match=match, cnt_used=cnt_used)
        
        self.elements[anmlId] = new_counter
        
        return new_counter
    
    def AddBoolean(self,
                    mode=BooleanMode.AND,
                    eod=False,
                    anmlId=None,
                    terminals=1,
                    reportCode=0,
                    match=False
                   ):
        if anmlId in self.elements:
            raise AnmlDuplicateId('this anmlId already exists: ' + anmlId)
        
        new_boolean = Boolean(mode=mode, eod=eod, anmlId=anmlId, terminals=terminals, reportCode=reportCode, match=match)
        
        self.elements[anmlId] = new_boolean
        
        return new_boolean
    
    def AddAnmlEdge(self,
                    srcElement,
                    destElement,
                    destPort=AnmlDefs.STE_PORT
                    ):
        
        if srcElement.anmlId not in self.elements:
            raise AnmlElementNotFound('could not find source: ' + srcElement.anmlId)
        if destElement.anmlId not in self.elements:
            raise AnmlElementNotFound('could not find destination: ' + destElement.anmlId)
        
        srcElement.activate.append((destElement,destPort))
    
    def ExportAnml(self,
                   filename,
                   basename=None
                  ):
        f = open(filename, "w")
        f.write(str(self))
        f.close()
    

class STE(object):
    def __init__(self,
                 symbol,
                 startType=AnmlDefs.NO_START,
                 anmlId=None,
                 reportCode=0,
                 match=False,
                 latched=False
                ):
        self.symbol = symbol
        self.startType = startType
        self.anmlId = anmlId
        self.reportCode = reportCode
        self.match = match
        self.latched = latched
        self.activate = []
    
    def getAnmlId(self):
        return self.anmlId
    
    def getActivate(self):
        return self.activate
    
    def __str__(self):
        anml = "<state-transition-element id=\"" + self.anmlId + "\" symbol-set=\"" + self.symbol +"\" start=\"" + self.startType + "\" latch=\"" + str(self.latched).lower() + "\">"
        if self.match:
            anml += "\n    <report-on-match />"
        for e,p in self.activate:
            if p == AnmlDefs.STE_PORT or (p == AnmlDefs.T1_PORT and (e.mode == BooleanMode.AND or e.mode == BooleanMode.OR or e.mode == BooleanMode.NAND or e.mode == BooleanMode.NOR or e.mode == BooleanMode.NOT)):
                anml += "\n    <activate-on-match element=\"" + e.anmlId + "\" />"
            else:
                anml += "\n    <activate-on-match element=\"" + e.anmlId + ":" + p + "\" />"
        anml += "\n</state-transition-element>"
        return anml

class Counter(object):
    def __init__(self,
                 target,
                 mode=CounterMode.STOP_HOLD,
                 anmlId=None,
                 reportCode=0,
                 match=False,
                 cnt_used=0
                ):
        self.target = target
        self.mode = mode
        self.anmlId = anmlId
        self.reportCode = reportCode
        self.match = match
        self.cnt_used = cnt_used
        
        self.activate = []
    
    def getAnmlId(self):
        return self.anmlId
    
    
    def getActivate(self):
        return self.activate
    
    def __str__(self):
        anml = "<counter id=\"" + self.anmlId + "\" target=\"" + str(self.target) + "\" at-target=\"" + self.mode + "\" >"
        if self.match:
            anml += "\n     <report-on-target />"
        for e,p in self.activate:
            if p == AnmlDefs.STE_PORT or (p == AnmlDefs.T1_PORT and (e.mode == BooleanMode.AND or e.mode == BooleanMode.OR or e.mode == BooleanMode.NAND or e.mode == BooleanMode.NOR or e.mode == BooleanMode.NOT)):
                anml += "\n    <activate-on-target element=\"" + e.anmlId + "\" />"
            else:
                anml += "\n    <activate-on-target element=\"" + e.anmlId + ":" + p + "\" />"
        anml += "\n</counter>"
        
        return anml

class Boolean(object):
    def __init__(self,
                 mode=BooleanMode.AND,
                 eod=False,
                 anmlId=None,
                 terminals=1,
                 reportCode=0,
                 match=False
                ):
        self.mode = mode
        self.eod = eod
        self.anmlId = anmlId
        self.terminals = terminals
        self.reportCode = reportCode
        self.match = match
        
        self.activate = []
    
    def getAnmlId(self):
        return self.anmlId
    
    def getActivate(self):
        return self.activate
        
    def __str__(self):
        anml = "<" + self.mode + " id=\"" + self.anmlId + "\" high-only-on-eod=\"" + str(self.eod).lower() + "\" >"
        if self.match:
            anml += "\n     <report-on-high />"
        for e,p in self.activate:
            if p == AnmlDefs.STE_PORT or (p == AnmlDefs.T1_PORT and (e.mode == BooleanMode.AND or e.mode == BooleanMode.OR or e.mode == BooleanMode.NAND or e.mode == BooleanMode.NOR or e.mode == BooleanMode.NOT)):
                anml += "\n    <activate-on-high element=\"" + e.anmlId + "\" />"
            else:
                anml += "\n    <activate-on-high element=\"" + e.anmlId + ":" + p + "\" />"
        anml += "\n</" + self.mode + ">"
        
        return anml

class AnmlDuplicateId(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AnmlElementNotFound(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AnmlParseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# helper for xml2anml
def raw2anml(raw):
    # our anml network
    anmlNet = AnmlNetwork(raw['id'])
    
    connections = []
    
    # add the STEs
    try:
        for ste in raw.state_transition_element:
            
            try:
                if ste.report_on_match is not None:
                    match = True
                    reportCode = ste.report_on_match['reportcode'] or 0
            except IndexError:
                match = False
                reportCode = 0
            
            anmlNet.AddSTE(
                ste['symbol-set'] or '',
                startType = ste['start'] or AnmlDefs.NO_START,
                anmlId = str(ste['id']),
                reportCode = reportCode,
                match = match,
                latched = ste['latched'] or False
            )
            
            try:
                for activate in ste.activate_on_match:
                    el = str(activate['element'])
                    if len(str.split(el,":")) == 1:
                        out = (el,AnmlDefs.STE_PORT)
                    else:
                        out = (str.split(el,":")[0], str.split(el,":")[1])
                    connections.append((str(ste['id']),out))
            except IndexError:
                pass
    except IndexError:
        pass
    
    # FIXME add the Boolean
    boolean_gates = [
        ('or', BooleanMode.OR,1),
        ('nor', BooleanMode.NOR,1),
        ('and', BooleanMode.AND,1),
        ('nand', BooleanMode.NAND,1),
        ('sum-of-products', BooleanMode.SOP2,3),
        ('nsum-of-products', BooleanMode.NSOP,3),
        ('product-of-sums', BooleanMode.POS2,3),
        ('nproduct-of-sums', BooleanMode.NPOS,3),
        ('inverter', BooleanMode.NOT,1)
    ]
    for gate_type,AnmlType,terms in boolean_gates:
        try:
            for gate in getattr(raw, gate_type):
                
                # get reports
                try:
                    if gate.report_on_high is not None:
                        match = True
                except IndexError:
                    match = False
                    
                # get eod
                try:
                    if gate.high_only_on_eod is not None:
                        eod = True
                except IndexError:
                    eod = False
                    
                anmlNet.AddBoolean(
                    mode=AnmlType,
                    eod=eod,
                    anmlId=str(gate['id']),
                    terminals=terms,
                    match=match
                )
                try:
                    for activate in gate.activate_on_high:
                        el = str(activate['element'])
                        if len(str.split(el,":")) == 1:
                                out = (el,AnmlDefs.STE_PORT)
                        else:
                            out = (str.split(el,":")[0], str.split(el,":")[1])
                        connections.append((str(ste['id']),out))
                except IndexError:
                    pass
        except IndexError:
            pass
    
    
    # add the Counters
    try:
        for counter in raw.counter:
            
            try:
                if counter.report_on_target is not None:
                    match = True
                    reportCode = counter.report_on_target['reportcode'] or 0
            except IndexError:
                match = False
                reportCode = 0
                
            anmlNet.AddCounter(
                   int(counter['target']) or 0,
                   mode = counter['at-target'],
                   anmlId = str(counter['id']),
                   reportCode = reportCode,
                   match = match,
                  )
            try:
                for activate in counter.activate_on_target:
                    el = str(activate['element'])
                    if len(str.split(el,":")) == 1:
                        out = (el,AnmlDefs.STE_PORT)
                    else:
                        out = (str.split(el,":")[0], str.split(el,":")[1])
                    connections.append((str(ste['id']),out))
            except IndexError:
                pass
            
    except IndexError:
        pass
            
    for (src,(dest,prt)) in connections:
        anmlNet.AddAnmlEdge(
                anmlNet.getElementByID(src),
                anmlNet.getElementByID(dest),
                destPort=prt
                )
    
    return anmlNet

def xml2anml(filename):
    raw_xml = untangle.parse(filename)
    
    try:
        return raw2anml(raw_xml.automata_network)
    except IndexError:
        try:
            return raw2anml(raw_xml.anml.automata_network)
        except IndexError:
            raise AnmlParseError('could not find ANML root')